#!/usr/bin/env python3
"""
md_to_docx.py — Markdown → branded DOCX renderer for the Requirements Agent.

Usage:
    python md_to_docx.py <input.md> [--branding <branding_preferences.json>] [--out <output.docx>]

Branding JSON fields (all optional — fall back to defaults when absent):
    client_name          str   — used in cover subtitle
    project_name         str   — used in cover subtitle
    font_name            str   — body font (default: Calibri)
    primary_color        str   — hex, applied to headings (default: 1F4E79)
    accent_color         str   — hex, table header fill (default: 1F4E79)
    secondary_accent     str   — hex, zebra-stripe row fill (default: F2F2F2)
    footer_text          str   — left footer text (default: Confidential)
    confidentiality      str   — center footer note + cover-page label
    logo_path            str   — path to a logo (PNG/JPG or SVG; SVG is
                                 rasterized automatically, resolved relative to
                                 the markdown file, CWD, or context/branding/)
    include_revision_table  bool
    include_signoff_table   bool

Optional nested docx object, intended for agent-normalized user instructions:
    font_name              str
    heading_color          hex
    table_header_color     hex
    footer_text            str
    confidentiality        str
    logo_path              str
    include_cover_page     bool
    include_footer         bool   (single-line footer: statement left, page no. right)
    include_header         bool   (running header: document name right-aligned, no logo)
    toc_max_level          int 1-6
    margins_inches         {top,bottom,left,right}

Exit codes: 0 = success, 1 = input file not found, 2 = rendering error.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Emu, Inches, Pt, RGBColor
except ImportError:
    print("ERROR: python-docx is not installed. Run: pip install python-docx", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_FONT = "Calibri"
DEFAULT_PRIMARY_HEX = "1F4E79"
DEFAULT_TABLE_HEADER_HEX = "1F4E79"
DEFAULT_ROW_STRIPE_HEX = "F2F2F2"
DEFAULT_FOOTER = "Confidential"
DEFAULT_CONFIDENTIALITY = "This document is confidential."
WHITE_RGB = RGBColor(0xFF, 0xFF, 0xFF)
LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".svg"}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _nested(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = config
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _first(config: dict[str, Any], paths: list[tuple[str, ...]], default: Any = None) -> Any:
    for path in paths:
        value = _nested(config, *path, default=None)
        if value not in (None, ""):
            return value
    return default


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    if value is None:
        return default
    return bool(value)


def _int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, min(maximum, parsed))


def _float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except Exception:
        parsed = default
    return max(minimum, min(maximum, parsed))


def _hex(value: Any, default: str) -> str:
    raw = str(value or default).strip().lstrip("#")
    if re.match(r"^[0-9a-fA-F]{6}$", raw):
        return raw.upper()
    return default


def _hex_to_rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return RGBColor(r, g, b)


# ---------------------------------------------------------------------------
# Logo handling — path resolution + SVG rasterization
# ---------------------------------------------------------------------------
# python-docx can only embed raster images (PNG/JPG/...) or EMF — not SVG.
# When the branding logo is an SVG (a common vector wordmark format), we
# rasterize it to a high-resolution PNG once and embed that. Conversion uses
# svglib + reportlab when available; if those libraries (or the file) are
# missing, we degrade gracefully and skip the logo rather than fail the render.
def _unique_existing_dirs(paths: list[Path]) -> list[Path]:
    """Return existing directories in deterministic order without duplicates."""
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def _branding_search_roots(md_path: Path) -> list[Path]:
    """Find candidate context/branding directories for this markdown file."""
    candidates = [
        Path.cwd() / "context" / "branding",
        Path("context") / "branding",
    ]
    try:
        resolved_md = md_path.resolve()
        ancestors = [resolved_md.parent, *resolved_md.parents]
    except Exception:
        ancestors = [md_path.parent]
    for parent in ancestors:
        candidates.append(parent / "context" / "branding")
    return _unique_existing_dirs(candidates)


def _resolve_logo_path(
    logo_path: str | None,
    search_dirs: list[Path],
) -> Path | None:
    """Resolve the explicitly configured logo path."""
    if not logo_path:
        return None
    candidate = Path(logo_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    tried: list[Path] = []
    if candidate.exists():
        return candidate.resolve()
    for base in search_dirs:
        p = (base / logo_path)
        tried.append(p)
        if p.exists():
            return p.resolve()
    raise FileNotFoundError(
        f"configured logo '{logo_path}' was not found; checked "
        f"{', '.join(str(t) for t in tried) or 'the current directory'}"
    )


def _rasterize_svg(svg_path: Path) -> Path | None:
    """Convert an SVG to a PNG and return its path, or None on failure.

    The PNG is cached in the system temp directory (not next to the source
    SVG) so that a render run leaves no artifacts behind beyond the .docx.
    The cache key includes the SVG's absolute path so distinct logos don't
    collide, and the cache is reused only while it is newer than the SVG."""
    import hashlib
    import tempfile

    cache_dir = Path(tempfile.gettempdir()) / "md_to_docx_logo_cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        cache_dir = Path(tempfile.gettempdir())
    key = hashlib.md5(str(svg_path.resolve()).encode("utf-8")).hexdigest()[:12]
    png_path = cache_dir / f"{svg_path.stem}.{key}.png"
    try:
        if png_path.exists() and png_path.stat().st_mtime >= svg_path.stat().st_mtime:
            return png_path  # cached and up to date
    except Exception:
        pass
    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg
    except ImportError:
        print(
            "WARNING: SVG logo supplied but svglib/reportlab are not installed; "
            "skipping logo. Install with: pip install svglib reportlab",
            file=sys.stderr,
        )
        return None
    try:
        drawing = svg2rlg(str(svg_path))
        if drawing is None:
            raise ValueError("svg2rlg returned no drawing")
        # Native pixel size is used (1 user unit -> 1 px). For a typical
        # wordmark (~1700px wide) this is crisp at the ~4-inch cover width.
        renderPM.drawToFile(drawing, str(png_path), fmt="PNG", bg=0xFFFFFF)
        return png_path
    except Exception as e:
        print(f"WARNING: Could not rasterize SVG logo ({svg_path}): {e}", file=sys.stderr)
        return None


def _prepare_logo(
    logo_path: str | None,
    search_dirs: list[Path],
) -> str | None:
    """Resolve a logo path and rasterize it if it is an SVG. Returns a path to
    an embeddable raster image, or None when no usable logo is available."""
    resolved = _resolve_logo_path(logo_path, search_dirs)
    if resolved is None:
        return None
    if resolved.suffix.lower() == ".svg":
        png = _rasterize_svg(resolved)
        return str(png) if png else None
    return str(resolved)


def _add_bottom_border(paragraph, color_hex: str, size: str = "8") -> None:
    """Add a single bottom rule to a paragraph (used for cover + H1 dividers)."""
    _add_para_edge_border(paragraph, "bottom", color_hex, size)


def _add_top_border(paragraph, color_hex: str, size: str = "8") -> None:
    """Add a single top rule to a paragraph (used for the footer separator)."""
    _add_para_edge_border(paragraph, "top", color_hex, size)


def _add_para_edge_border(paragraph, edge: str, color_hex: str, size: str = "8") -> None:
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), size)
    el.set(qn("w:space"), "4")
    el.set(qn("w:color"), color_hex.lstrip("#"))
    pBdr.append(el)


# ---------------------------------------------------------------------------
# Inline markdown parser
# ---------------------------------------------------------------------------
INLINE = re.compile(r"(\[.*?\]\(.*?\)|\*\*.+?\*\*|\*.+?\*|_.+?_|`.+?`)", re.DOTALL)


def _add_inline_runs(p, text: str) -> None:
    """Parse **bold**, *italic*, `code`, [label](url) and add runs to paragraph p."""
    if not text:
        return
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            p.add_run(text[pos : m.start()])
        token = m.group(0)
        if token.startswith("[") and "](" in token and token.endswith(")"):
            label = token[1 : token.index("](")]
            p.add_run(label)
        elif token.startswith("**") and token.endswith("**"):
            p.add_run(token[2:-2]).bold = True
        elif (token.startswith("*") and token.endswith("*")) or (
            token.startswith("_") and token.endswith("_")
        ):
            p.add_run(token[1:-1]).italic = True
        elif token.startswith("`") and token.endswith("`"):
            run = p.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        else:
            p.add_run(token)
        pos = m.end()
    if pos < len(text):
        p.add_run(text[pos:])


# ---------------------------------------------------------------------------
# OXML helpers
# ---------------------------------------------------------------------------
def _shade_cell(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def _set_cell_text_color(cell, rgb: RGBColor) -> None:
    for p in cell.paragraphs:
        for r in p.runs:
            r.font.color.rgb = rgb


def _center_cell(cell) -> None:
    for p in cell.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _set_cell_borders(cell, **borders: dict[str, str]) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = tc_pr.find(qn("w:tcBorders"))
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)

    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        attrs = borders.get(edge)
        if attrs is None:
            continue
        tag = f"w:{edge}"
        element = tc_borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            tc_borders.append(element)
        for key, value in attrs.items():
            element.set(qn(f"w:{key}"), str(value))


def _set_cell_margins(cell, top: int = 120, left: int = 180, bottom: int = 120, right: int = 180) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn("w:tcMar"))
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)

    for side, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _blockquote_palette(text: str) -> tuple[str, str]:
    lower = (text or "").lower()
    # Explicit severity tags (from the report grammar callout skeleton) are
    # authoritative and checked first, so a callout body that merely mentions
    # another severity word does not mis-color the box.
    if "[blocker]" in lower:
        return "FFF7ED", "FDBA74"  # orange
    if "[critical]" in lower:
        return "FEF2F2", "FCA5A5"  # red
    if "[major]" in lower or "[warning]" in lower:
        return "FEFCE8", "FACC15"  # amber
    if "[minor]" in lower or "[info]" in lower:
        return "F8FAFC", "CBD5E1"  # neutral slate
    if "[insufficient input]" in lower:
        return "FFF7ED", "FDBA74"
    if "[assumption]" in lower:
        return "FEFCE8", "FACC15"
    return "F8FAFC", "CBD5E1"


def _normalise_blockquote_line(line: str) -> str:
    stripped = line.lstrip()
    if stripped == ">":
        return ""
    if stripped.startswith("> "):
        return stripped[2:].rstrip()
    if stripped.startswith(">"):
        return stripped[1:].lstrip().rstrip()
    return stripped.rstrip()


def _add_blockquote_box(doc: Document, quote_lines: list[str]) -> None:
    quote_lines = quote_lines or [""]
    fill_hex, border_hex = _blockquote_palette("\n".join(quote_lines))

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    cell = table.cell(0, 0)
    _shade_cell(cell, fill_hex)
    _set_cell_margins(cell)
    _set_cell_borders(
        cell,
        top={"val": "nil"},
        right={"val": "nil"},
        bottom={"val": "nil"},
        left={"val": "single", "sz": "18", "space": "0", "color": border_hex},
    )

    first_paragraph = True
    for raw_line in quote_lines:
        text = raw_line.strip()
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", text)
        is_quote_heading = bool(heading_match)
        if heading_match:
            text = heading_match.group(2).strip()

        p = cell.paragraphs[0] if first_paragraph else cell.add_paragraph()
        first_paragraph = False
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15

        if text:
            _add_inline_runs(p, text)
        for run in p.runs:
            run.font.size = Pt(10)
            run.italic = True
            if is_quote_heading:
                run.bold = True
                run.font.size = Pt(11)

    doc.add_paragraph("")


def _add_field(run, field: str) -> None:
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(fld_end)


def _add_bookmark(paragraph, bookmark_name: str, bookmark_id: int) -> None:
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bookmark_id))
    start.set(qn("w:name"), bookmark_name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bookmark_id))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def _add_hyperlink(paragraph, anchor: str, text: str) -> None:
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("w:anchor"), anchor)
    hyperlink.set(qn("w:history"), "1")
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rPr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------
def _is_table_line(line: str) -> bool:
    s = (line or "").strip()
    return s.startswith("|") and "|" in s[1:]


def _parse_row(line: str) -> list[str]:
    s = line.strip().lstrip("|").rstrip("|")
    return [c.strip() for c in s.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.match(r"^:?-+:?$", c) for c in cells if c)


def _set_cell_rich_text(cell, text: str) -> None:
    text = text or ""
    cell.text = ""
    p = cell.paragraphs[0]
    for part in re.split(r"(<br\s*/?>)", text, flags=re.IGNORECASE):
        if re.match(r"<br\s*/?>", part or "", flags=re.IGNORECASE):
            p.add_run().add_break()
        else:
            _add_inline_runs(p, part)


def _repeat_header_row(row) -> None:
    """Mark a table row as a header row so Word repeats it at the top of each
    page the table spans — important for the long multi-page tables here."""
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def _add_md_table(
    doc: Document,
    header: list[str],
    rows: list[list[str]],
    header_fill_hex: str,
    row_stripe_hex: str | None = None,
) -> None:
    ncols = max(len(header), max((len(r) for r in rows), default=0))
    if ncols == 0:
        return
    table = doc.add_table(rows=1 + len(rows), cols=ncols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Let Word's layout engine compute balanced column widths and wrap text;
    # this keeps even very wide tables within the page margins.
    table.autofit = True
    # Repeat the header row whenever the table breaks across pages.
    _repeat_header_row(table.rows[0])
    for j in range(ncols):
        val = header[j] if j < len(header) else ""
        cell = table.cell(0, j)
        _set_cell_rich_text(cell, val)
        _shade_cell(cell, header_fill_hex)
        _set_cell_text_color(cell, WHITE_RGB)
        _center_cell(cell)
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(10)
                r.bold = True
    for i, row in enumerate(rows, start=1):
        # Zebra striping: shade every other data row for readability.
        stripe = row_stripe_hex if (row_stripe_hex and i % 2 == 0) else None
        for j in range(ncols):
            val = row[j] if j < len(row) else ""
            cell = table.cell(i, j)
            _set_cell_rich_text(cell, val)
            if stripe:
                _shade_cell(cell, stripe)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(10)
    doc.add_paragraph("")


# ---------------------------------------------------------------------------
# Code block helper
# ---------------------------------------------------------------------------
def _add_code_block(doc: Document, code_text: str) -> None:
    code_text = (code_text or "").rstrip("\n")
    if not code_text:
        return
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    doc.add_paragraph("")


# ---------------------------------------------------------------------------
# List style helper
# ---------------------------------------------------------------------------
def _style_for_list(doc: Document, base: str, level: int) -> str:
    level = max(0, min(level, 8))
    candidates = (
        [base] if level == 0 else [f"{base} {level + 1}", f"{base} {level}", base]
    )
    for name in candidates:
        try:
            _ = doc.styles[name]
            return name
        except Exception:
            continue
    return base


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------
def _add_cover(
    doc: Document,
    title_text: str,
    brand_text: str,
    primary_rgb: RGBColor,
    primary_hex: str,
    logo_path: str | None,
    confidentiality: str = "",
) -> None:
    # Brand logo near the top of the page.
    logo_added = False
    if logo_path:
        try:
            p_logo = doc.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_logo.paragraph_format.space_before = Inches(0.6)
            p_logo.paragraph_format.space_after = Inches(0.2)
            p_logo.add_run().add_picture(logo_path, width=Inches(3.6))
            logo_added = True
        except Exception as e:
            print(f"WARNING: Could not add logo ({logo_path}): {e}", file=sys.stderr)

    # Title block, pushed toward the vertical centre of the page.
    p_title = doc.add_paragraph(title_text or "")
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Inches(2.2 if logo_added else 2.8)
    p_title.paragraph_format.space_after = Pt(6)
    if p_title.runs:
        p_title.runs[0].bold = True
        p_title.runs[0].font.size = Pt(30)
        p_title.runs[0].font.color.rgb = primary_rgb

    # Accent divider rule under the title.
    p_rule = doc.add_paragraph()
    p_rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rule.paragraph_format.space_after = Pt(10)
    _add_bottom_border(p_rule, primary_hex, size="18")

    if brand_text:
        p_brand = doc.add_paragraph(brand_text)
        p_brand.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_brand.paragraph_format.space_before = Pt(4)
        if p_brand.runs:
            p_brand.runs[0].bold = True
            p_brand.runs[0].font.size = Pt(18)
            p_brand.runs[0].font.color.rgb = primary_rgb

    if confidentiality:
        p_conf = doc.add_paragraph(confidentiality)
        p_conf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_conf.paragraph_format.space_before = Pt(24)
        if p_conf.runs:
            p_conf.runs[0].italic = True
            p_conf.runs[0].font.size = Pt(10)
            p_conf.runs[0].font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    doc.add_page_break()


RULE_HEX = "A6A6A6"
META_GRAY = RGBColor(0x59, 0x54, 0x54)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def _add_header(doc: Document, header_text: str) -> None:
    """Single-line running header: document name (right-aligned) with a rule
    below it. No logo. Applied to the default (non-first-page) header."""
    section = doc.sections[0]
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(header_text or "")
    run.font.size = Pt(9)
    run.font.color.rgb = META_GRAY
    _add_bottom_border(p, RULE_HEX, size="6")


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def _footer_cell_text(cell, align, runs_spec) -> None:
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    for text, is_field in runs_spec:
        r = p.add_run("" if is_field else text)
        r.font.size = Pt(9)
        r.font.color.rgb = META_GRAY
        if is_field:
            _add_field(r, "PAGE")


def _add_footer(doc: Document, footer_text: str, confidentiality: str = "") -> None:
    """Running footer with a rule above it: a first row carrying the statement
    on the left and the page number on the right, and (when provided) a centered
    confidentiality note beneath it (see attached reference).

    The statement/page row is a borderless 2-column table rather than a tab
    stop: a right-aligned table cell renders the page number flush right
    deterministically in every Word version, whereas tab stops can collide with
    the built-in "Footer" style's own tabs and let the page number run into the
    statement.
    """
    section = doc.sections[0]
    footer = section.footer
    footer.is_linked_to_previous = False

    content_width = int(section.page_width - section.left_margin - section.right_margin)

    # Drop the default empty paragraph so the footer is exactly our table.
    for stray in list(footer.paragraphs):
        stray._p.getparent().remove(stray._p)

    table = footer.add_table(rows=1, cols=2, width=Emu(content_width))
    table.autofit = False
    table.allow_autofit = False
    left_w = int(content_width * 0.72)
    right_w = content_width - left_w
    cell_left, cell_right = table.rows[0].cells
    cell_left.width = Emu(left_w)
    cell_right.width = Emu(right_w)

    _footer_cell_text(cell_left, WD_ALIGN_PARAGRAPH.LEFT, [(footer_text or "", False)])
    _footer_cell_text(cell_right, WD_ALIGN_PARAGRAPH.RIGHT, [("Page ", False), (None, True)])

    # Rule above the footer (top border on the cells); flush cell edges; no
    # other borders.
    for cell in (cell_left, cell_right):
        _set_cell_borders(cell, top={"val": "single", "sz": "6", "space": "0", "color": RULE_HEX})
        _set_cell_margins(cell, top=80, left=0, bottom=0, right=0)

    # Confidentiality note, centered beneath the statement/page row.
    if confidentiality:
        p_conf = footer.add_paragraph()
        p_conf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_conf.paragraph_format.space_before = Pt(2)
        p_conf.paragraph_format.space_after = Pt(0)
        r_conf = p_conf.add_run(confidentiality)
        r_conf.font.size = Pt(8)
        r_conf.italic = True
        r_conf.font.color.rgb = META_GRAY


def _apply_page_setup(doc: Document, branding: dict[str, Any]) -> None:
    margins = _nested(branding, "docx", "margins_inches", default={}) or {}
    top = _float(margins.get("top"), 0.7, 0.25, 2.0)
    bottom = _float(margins.get("bottom"), 0.7, 0.25, 2.0)
    left = _float(margins.get("left"), 0.75, 0.25, 2.0)
    right = _float(margins.get("right"), 0.75, 0.25, 2.0)
    for section in doc.sections:
        section.top_margin = Inches(top)
        section.bottom_margin = Inches(bottom)
        section.left_margin = Inches(left)
        section.right_margin = Inches(right)


# ---------------------------------------------------------------------------
# TOC (clickable internal links)
# ---------------------------------------------------------------------------
def _inject_toc(
    doc: Document,
    all_headings: list[tuple[int, str, str]],
    from_index: int,
    toc_max_level: int,
) -> None:
    for idx, (hlvl, htxt, hbm) in enumerate(all_headings, start=1):
        if idx <= from_index:
            continue
        if hlvl > toc_max_level:
            continue
        tp = doc.add_paragraph()
        tp.paragraph_format.left_indent = Inches(0.25 * max(0, hlvl - 1))
        _add_hyperlink(tp, hbm, htxt)
        for r in tp.runs:
            r.font.size = Pt(10)
            if hlvl == 1:
                r.bold = True
    doc.add_paragraph("")


# ---------------------------------------------------------------------------
# Core content renderer
# ---------------------------------------------------------------------------
def _render_content(
    doc: Document,
    md_text: str,
    primary_rgb: RGBColor,
    primary_hex: str,
    header_fill_hex: str,
    toc_max_level: int = 3,
    row_stripe_hex: str | None = None,
) -> None:
    md_text = (md_text or "").replace("\r\n", "\n")
    if not md_text.strip():
        doc.add_paragraph("(No content provided)")
        return

    lines = md_text.split("\n")

    # Pre-scan all headings for TOC bookmark names
    all_headings: list[tuple[int, str, str]] = []
    hcount = 0
    for raw in lines:
        mh = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if mh:
            hcount += 1
            all_headings.append((len(mh.group(1)), mh.group(2).strip(), f"h_{hcount:04d}"))

    prescan_index = 0
    bookmark_id = 1
    i = 0
    in_code = False
    code_buf: list[str] = []
    injecting_toc = False
    toc_injected = False
    first_h1_seen = False

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip("\n")

        # Render-ownership markers are machine state embedded in markdown for
        # guarded incremental updates. They must never become visible paragraphs
        # in an exported client document.
        if re.match(r'^\s*<!--\s+RA-BLOCK\s+(?:START|END)\b.*-->\s*$', line):
            i += 1
            continue

        # Skip markdown TOC bullet lines that follow an injected TOC heading
        if injecting_toc:
            if re.match(r"^(#{1,6})\s+.+", line.strip()):
                injecting_toc = False
                # fall through to process this heading
            else:
                i += 1
                continue

        # Code fences
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                _add_code_block(doc, "\n".join(code_buf))
                code_buf = []
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^\s*([-*_])\1\1+\s*$", line):
            p = doc.add_paragraph("")
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "6")
            bottom.set(qn("w:space"), "1")
            bottom.set(qn("w:color"), "A6A6A6")
            pBdr.append(bottom)
            pPr.append(pBdr)
            i += 1
            continue

        # Tables
        if _is_table_line(line):
            header = _parse_row(line)
            i += 1
            if i < len(lines) and _is_table_line(lines[i]):
                sep = _parse_row(lines[i])
                if _is_separator_row(sep):
                    i += 1
            rows: list[list[str]] = []
            while i < len(lines) and _is_table_line(lines[i]):
                rows.append(_parse_row(lines[i]))
                i += 1
            _add_md_table(doc, header, rows, header_fill_hex, row_stripe_hex)
            continue

        # Blank line
        if not line.strip():
            doc.add_paragraph("")
            i += 1
            continue

        # Headings
        mh = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if mh:
            lvl = len(mh.group(1))
            txt = mh.group(2).strip()

            # Insert a page break before every H1 except the first
            if lvl == 1:
                if first_h1_seen:
                    doc.add_page_break()
                else:
                    first_h1_seen = True

            doc.add_heading(txt, level=min(lvl, 6))
            p = doc.paragraphs[-1]
            p.paragraph_format.keep_with_next = True

            # Apply the brand primary color to every heading level for a
            # cohesive look, and give H1 section headings an accent underline.
            for run in p.runs:
                run.font.color.rgb = primary_rgb
            if lvl == 1:
                _add_bottom_border(p, primary_hex, size="12")

            prescan_index += 1
            bm = f"h_{prescan_index:04d}"
            _add_bookmark(p, bm, bookmark_id)
            bookmark_id += 1

            # Inject clickable TOC where markdown has "Table of Contents" / "TOC" heading
            if txt.strip().lower() in {"table of contents", "toc"} and not toc_injected:
                _inject_toc(doc, all_headings, prescan_index, toc_max_level)
                injecting_toc = True
                toc_injected = True

            i += 1
            continue

        # Blockquote / callout
        if line.lstrip().startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote_lines.append(_normalise_blockquote_line(lines[i]))
                i += 1
            _add_blockquote_box(doc, quote_lines)
            continue

        # Unordered list
        if line.lstrip().startswith(("- ", "* ")):
            indent_spaces = len(line) - len(line.lstrip(" "))
            level = indent_spaces // 2
            txt = line.lstrip()[2:].strip()
            style = _style_for_list(doc, "List Bullet", level)
            p = doc.add_paragraph("", style=style)
            _add_inline_runs(p, txt)
            if level > 0:
                p.paragraph_format.left_indent = Inches(0.25 * level)
            for r in p.runs:
                r.font.size = Pt(10)
            i += 1
            continue

        # Ordered list — rendered as plain "N. text" to avoid Word auto-numbering
        mo = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if mo:
            p = doc.add_paragraph(f"{mo.group(1)}. ")
            _add_inline_runs(p, mo.group(2).strip())
            for r in p.runs:
                r.font.size = Pt(10)
            i += 1
            continue

        # Normal paragraph
        p = doc.add_paragraph("")
        _add_inline_runs(p, line.strip())
        for r in p.runs:
            r.font.size = Pt(10)
        i += 1

    # Flush any unclosed code block
    if in_code and code_buf:
        _add_code_block(doc, "\n".join(code_buf))

    # Flush any unclosed table (table at end-of-file with no trailing blank line)
    # — handled inside the loop since we break out of it normally; no extra action needed


# ---------------------------------------------------------------------------
# Top-level renderer
# ---------------------------------------------------------------------------
def render(
    md_path: Path,
    out_path: Path,
    branding: dict,
    toc_max_level: int = 3,
) -> None:
    md_text = md_path.read_text(encoding="utf-8")

    # Resolve the documented flat and nested branding fields.
    font_name = _first(branding, [("docx", "font_name"), ("font_name",)], DEFAULT_FONT)
    primary_hex = _hex(
        _first(branding, [("docx", "heading_color"), ("primary_color",)], DEFAULT_PRIMARY_HEX),
        DEFAULT_PRIMARY_HEX,
    )
    accent_hex = _hex(
        _first(
            branding,
            [("docx", "table_header_color"), ("docx", "accent_color"), ("accent_color",), ("primary_color",)],
            DEFAULT_TABLE_HEADER_HEX,
        ),
        DEFAULT_TABLE_HEADER_HEX,
    )
    footer_text = _first(branding, [("docx", "footer_text"), ("footer_text",), ("confidentiality",)], DEFAULT_FOOTER)
    confidentiality = _first(branding, [("docx", "confidentiality"), ("confidentiality",)], DEFAULT_CONFIDENTIALITY)
    row_stripe_hex = _hex(
        _first(
            branding,
            [("docx", "row_stripe_color"), ("docx", "secondary_accent"), ("secondary_accent",)],
            DEFAULT_ROW_STRIPE_HEX,
        ),
        DEFAULT_ROW_STRIPE_HEX,
    )
    raw_logo_path = _first(branding, [("docx", "logo_path"), ("logo_path",)], None)
    # Resolve the logo relative to the markdown file, CWD, and the branding
    # folder, then rasterize it if it is an SVG (python-docx can't embed SVG).
    branding_roots = _branding_search_roots(md_path)
    logo_search_dirs = [
        Path.cwd(),
        md_path.parent,
        *branding_roots,
    ]
    logo_path = _prepare_logo(raw_logo_path, logo_search_dirs)
    client_name = _first(branding, [("client_name",), ("document", "client_name")], "")
    project_name = _first(branding, [("project_name",), ("document", "project_name")], "")
    include_cover_page = _bool(_nested(branding, "docx", "include_cover_page", default=True), True)
    include_footer = _bool(_nested(branding, "docx", "include_footer", default=True), True)
    include_header = _bool(_nested(branding, "docx", "include_header", default=True), True)
    toc_max_level = _int(_nested(branding, "docx", "toc_max_level", default=toc_max_level), toc_max_level, 1, 6)

    # Cover brand text: "Client Name — Project Name" or just whichever is present
    brand_parts = [p for p in [client_name, project_name] if p]
    brand_text = " — ".join(brand_parts) if brand_parts else "Requirements Agent"

    primary_rgb = _hex_to_rgb(primary_hex)

    doc = Document()
    _apply_page_setup(doc, branding)

    # Apply base font
    normal = doc.styles["Normal"]
    normal.font.name = font_name
    normal.font.size = Pt(10)

    # Extract H1 title for the cover and the running header
    lines = md_text.replace("\r\n", "\n").split("\n")
    title = None
    body_start = 0
    for idx, raw in enumerate(lines):
        if not raw.strip():
            continue
        m = re.match(r"^\s*#\s+(.*)\s*$", raw)
        if m:
            title = m.group(1).strip()
            body_start = idx + 1
        break

    has_cover = bool(title and include_cover_page)
    # Keep the cover page clean: suppress the running header/footer on page 1.
    if has_cover:
        doc.sections[0].different_first_page_header_footer = True

    if include_header:
        _add_header(doc, title or brand_text)
    if include_footer:
        _add_footer(doc, footer_text, confidentiality)

    if has_cover:
        _add_cover(doc, title, brand_text, primary_rgb, primary_hex, logo_path, confidentiality)
        body_md = "\n".join(lines[body_start:]).lstrip("\n")
    else:
        body_md = md_text

    _render_content(
        doc,
        body_md,
        primary_rgb,
        primary_hex,
        accent_hex,
        toc_max_level,
        row_stripe_hex,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a markdown deliverable to branded DOCX."
    )
    parser.add_argument("input", help="Path to the input .md file")
    parser.add_argument(
        "--branding",
        default=None,
        help="Path to one branding JSON file (default: canonical files under context/branding)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output .docx path (default: same directory as input, same stem)",
    )
    parser.add_argument(
        "--toc-depth",
        type=int,
        default=3,
        help="Maximum heading level to include in TOC (default: 3)",
    )
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"ERROR: Input file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out) if args.out else md_path.with_suffix(".docx")

    # Branding/export preferences: explicit arg > auto-detect relative to CWD.
    # When auto-detecting, scan context/branding/** recursively for any JSON file
    # the user dropped (any filename — they choose how to organize their branding).
    # If multiple JSON files exist, merge in a deterministic order:
    #   1. base-looking files first (filename contains "branding", "preferences", "style", "default", "base")
    #   2. override-looking files next (filename contains "docx", "export", "override", "client", or in a sub-subfolder)
    # so per-client/per-export overrides apply last and win.
    branding: dict = {}
    branding_candidates: list[Path] = []
    if args.branding:
        explicit = Path(args.branding)
        if not explicit.exists():
            print(f"ERROR: Branding file not found: {explicit}", file=sys.stderr)
            sys.exit(1)
        branding_candidates.append(explicit)
    else:
        seen: set[Path] = set()
        for root in _branding_search_roots(md_path):
            for filename in ("branding_preferences.json", "docx_export_preferences.json"):
                candidate = root / filename
                resolved = candidate.resolve()
                if candidate.exists() and resolved not in seen:
                    seen.add(resolved)
                    branding_candidates.append(candidate)

    for bp in branding_candidates:
        try:
            branding = _deep_merge(branding, json.loads(bp.read_text(encoding="utf-8")))
            print(f"Using export preferences: {bp}")
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: Could not load branding file {bp}: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        render(md_path, out_path, branding, toc_max_level=args.toc_depth)
        print(f"Rendered: {out_path}")
    except Exception as e:
        print(f"ERROR: Rendering failed for {md_path}: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
