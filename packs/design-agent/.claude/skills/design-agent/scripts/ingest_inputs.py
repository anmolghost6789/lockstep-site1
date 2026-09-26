#!/usr/bin/env python3
"""Deterministic input ingestion for agent runs.

Converts every binary input/context document (.docx, .pdf, .xlsx, .pptx, images)
into a clean UTF-8 text/markdown *sidecar* and writes a single
``inputs_manifest.json`` describing each file. The agent reads the sidecar text
instead of ever touching a binary, which removes the trial-and-error
"can't read binary → try python-docx → encoding error" loop that wastes a large
amount of time and tokens on every run.

Design guarantees (this is shared by ALL agents, standalone and under the UI):

* **No silent loss.** Anything that cannot become text (embedded images,
  diagrams, scanned pages, spreadsheet colour-coding) is either extracted as an
  asset file and referenced, or explicitly flagged in the manifest with a
  ``notes`` field. The original file is always kept and remains the source of
  truth.
* **Graceful degradation.** A missing optional library, a corrupt file, or an
  oversized file never crashes ingestion or fails the run — that file is marked
  ``unsupported`` / ``failed`` / ``skipped_large`` with a reason, and the
  original is left in place for the agent to fall back on. Worst case equals
  today's behaviour, never worse.
* **Idempotent.** Each file's sha256 is recorded; re-running skips unchanged
  files unless ``--force`` is given, so uploads and re-runs are cheap.
* **Structure-preserving.** Word keeps headings + paragraph indices + tables;
  Excel keeps per-sheet grids with cell coordinates, formulas, merged ranges and
  comments; PDF is page-delimited; PowerPoint is slide-delimited. This keeps the
  precise citation anchors (section/paragraph, page, sheet/cell) the downstream
  deliverables rely on.

Usage::

    python ingest_inputs.py                 # ingest ./inputs and ./context under cwd
    python ingest_inputs.py --root <run>    # explicit run dir
    python ingest_inputs.py --force         # re-convert everything
    python ingest_inputs.py --roots inputs  # only ingest inputs/

Exit code is always 0 unless arguments are invalid; per-file failures are
reported in the manifest, not as a process error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

MANIFEST_NAME = "inputs_manifest.json"
INGESTED_DIRNAME = "_ingested"
ASSETS_DIRNAME = "_assets"

# Roots scanned by default, relative to the run dir.
DEFAULT_ROOTS = ("inputs", "context")

# Files that never need ingestion (already text the agent can Read directly).
TEXT_EXTS = {".md", ".markdown", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml", ".rst", ".log", ".svg", ".html", ".xml"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
DOCX_EXTS = {".docx"}
XLSX_EXTS = {".xlsx", ".xlsm"}
PPTX_EXTS = {".pptx"}
PDF_EXTS = {".pdf"}

# Skip our own derived output, hidden files, and index furniture.
SKIP_NAMES = {".gitkeep", ".keep", ".DS_Store", MANIFEST_NAME}
SKIP_DIRS = {INGESTED_DIRNAME, "__pycache__"}

# Files larger than this are not parsed (kept raw + flagged). Guards against
# zip/pdf bombs and pathological spreadsheets eating memory.
MAX_PARSE_BYTES = 50 * 1024 * 1024


def _approx_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) for context-budget awareness."""
    return max(0, len(text) // 4)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Always UTF-8 — this is what kills the cp1252 mojibake on Windows.
    path.write_text(text, encoding="utf-8", newline="\n")


def _classify(ext: str) -> str:
    if ext in DOCX_EXTS:
        return "document"
    if ext in XLSX_EXTS:
        return "spreadsheet"
    if ext in PPTX_EXTS:
        return "presentation"
    if ext in PDF_EXTS:
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in TEXT_EXTS:
        return "text"
    return "unknown"


# --------------------------------------------------------------------------- #
# Per-format extractors. Each returns (markdown_text, assets, notes, reader).
# They may raise; the caller turns exceptions into a `failed` manifest entry.
# A missing optional dependency raises ImportError, turned into `unsupported`.
# --------------------------------------------------------------------------- #


def _extract_docx(path: Path, assets_dir: Path, asset_stem: str) -> tuple[str, list[str], str, str]:
    import docx  # python-docx

    document = docx.Document(str(path))
    lines: list[str] = []
    para_index = 0
    for block in document.paragraphs:
        text = (block.text or "").strip()
        style = (block.style.name if block.style else "") or ""
        if not text:
            para_index += 1
            continue
        if style.startswith("Heading"):
            level = "".join(c for c in style if c.isdigit())
            hashes = "#" * (int(level) if level.isdigit() else 2)
            lines.append(f"{hashes} {text}")
        else:
            # Keep paragraph index so citations can reference paragraph_index.
            lines.append(f"<!-- p{para_index} -->{text}")
        para_index += 1

    for ti, table in enumerate(document.tables):
        lines.append("")
        lines.append(f"<!-- table {ti} -->")
        rows = [[(c.text or "").strip().replace("\n", " ") for c in row.cells] for row in table.rows]
        if rows:
            header = rows[0]
            lines.append("| " + " | ".join(header) + " |")
            lines.append("| " + " | ".join("---" for _ in header) + " |")
            for row in rows[1:]:
                lines.append("| " + " | ".join(row) + " |")

    notes = ""
    image_count = sum(1 for r in document.part.rels.values() if "image" in r.reltype)
    if image_count:
        notes = (
            f"{image_count} embedded image(s) not text-extracted; "
            "open the original .docx to inspect diagrams/screenshots."
        )
    return "\n".join(lines).strip() + "\n", [], notes, "python-docx"


def _extract_xlsx(path: Path, assets_dir: Path, asset_stem: str) -> tuple[str, list[str], str, str]:
    import openpyxl

    # data_only=False keeps formulas; we surface both formula and a note.
    wb = openpyxl.load_workbook(str(path), data_only=False, read_only=False)
    lines: list[str] = []
    note_bits: list[str] = []
    for ws in wb.worksheets:
        lines.append(f"## Sheet: {ws.title}")
        merged = [str(r) for r in getattr(ws, "merged_cells", []).ranges] if getattr(ws, "merged_cells", None) else []
        if merged:
            lines.append(f"<!-- merged_ranges: {', '.join(merged)} -->")
        dims = ws.calculate_dimension(force=True) if hasattr(ws, "calculate_dimension") else None
        if dims:
            lines.append(f"<!-- range: {dims} -->")
        comments: list[str] = []
        rows = list(ws.iter_rows())
        if not rows:
            lines.append("_(empty sheet)_")
            lines.append("")
            continue
        # Markdown table preserving the grid; first row treated as header.
        def _cell(cell: Any) -> str:
            val = cell.value
            if cell.comment is not None:
                comments.append(f"{cell.coordinate}: {str(cell.comment.text).strip()}")
            if val is None:
                return ""
            text = str(val).replace("\n", " ").replace("|", "\\|").strip()
            return text

        header = [_cell(c) for c in rows[0]]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        for row in rows[1:]:
            lines.append("| " + " | ".join(_cell(c) for c in row) + " |")
        if comments:
            lines.append("")
            lines.append("<!-- cell comments -->")
            for c in comments:
                lines.append(f"- {c}")
        lines.append("")
    note_bits.append(
        "Cell colour/conditional formatting is NOT captured; if colour encodes "
        "meaning (e.g. changed/deprecated columns), inspect the original .xlsx."
    )
    return "\n".join(lines).strip() + "\n", [], " ".join(note_bits), "openpyxl"


def _extract_pdf(path: Path, assets_dir: Path, asset_stem: str) -> tuple[str, list[str], str, str]:
    try:
        import pdfplumber  # preferred: better layout/tables
    except ImportError:
        pdfplumber = None
    if pdfplumber is not None:
        lines: list[str] = []
        empty_pages = 0
        with pdfplumber.open(str(path)) as pdf:
            for pi, page in enumerate(pdf.pages):
                text = (page.extract_text() or "").strip()
                lines.append(f"## Page {pi + 1}")
                if text:
                    lines.append(text)
                else:
                    empty_pages += 1
                    lines.append("_(no extractable text — likely a scanned/image page)_")
                lines.append("")
        notes = ""
        if empty_pages:
            notes = (
                f"{empty_pages} page(s) had no extractable text (scanned/image); "
                "OCR not applied — open the original PDF to read them."
            )
        return "\n".join(lines).strip() + "\n", [], notes, "pdfplumber"

    # Fallback to pypdf if present.
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # neither library available
        raise ImportError("install 'pdfplumber' (preferred) or 'pypdf' to ingest PDFs") from exc
    reader = PdfReader(str(path))
    lines = []
    for pi, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        lines.append(f"## Page {pi + 1}")
        lines.append(text or "_(no extractable text)_")
        lines.append("")
    return "\n".join(lines).strip() + "\n", [], "", "pypdf"


def _extract_pptx(path: Path, assets_dir: Path, asset_stem: str) -> tuple[str, list[str], str, str]:
    from pptx import Presentation  # python-pptx
    from pptx.util import Emu  # noqa: F401  (kept for clarity / future use)

    prs = Presentation(str(path))
    lines: list[str] = []
    assets: list[str] = []
    image_count = 0
    for si, slide in enumerate(prs.slides):
        lines.append(f"## Slide {si + 1}")
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                lines.append(shape.text_frame.text.strip())
            if getattr(shape, "has_table", False) and shape.has_table:
                table = shape.table
                rows = [[(c.text or "").strip().replace("\n", " ") for c in r.cells] for r in table.rows]
                if rows:
                    lines.append("| " + " | ".join(rows[0]) + " |")
                    lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
                    for row in rows[1:]:
                        lines.append("| " + " | ".join(row) + " |")
            if shape.shape_type == 13:  # PICTURE
                try:
                    image = shape.image
                    ext = (image.ext or "png").lstrip(".")
                    asset_name = f"{asset_stem}_slide{si + 1}_img{image_count + 1}.{ext}"
                    assets_dir.mkdir(parents=True, exist_ok=True)
                    (assets_dir / asset_name).write_bytes(image.blob)
                    assets.append(asset_name)
                    image_count += 1
                    lines.append(f"<!-- image extracted: {asset_name} -->")
                except Exception:
                    lines.append("<!-- image present but could not be extracted -->")
        # Speaker notes carry real intent.
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()
            if notes_text:
                lines.append(f"<!-- speaker notes -->\n{notes_text}")
        lines.append("")
    note = f"{image_count} slide image(s) extracted as assets." if image_count else ""
    return "\n".join(lines).strip() + "\n", assets, note, "python-pptx"


_EXTRACTORS = {
    "document": _extract_docx,
    "spreadsheet": _extract_xlsx,
    "pdf": _extract_pdf,
    "presentation": _extract_pptx,
}


def _ingest_file(file_path: Path, run_dir: Path, force: bool, prior: dict[str, dict]) -> dict:
    """Ingest one file; return its manifest entry. Never raises."""
    rel = _rel(file_path, run_dir)
    ext = file_path.suffix.lower()
    kind = _classify(ext)
    try:
        size = file_path.stat().st_size
        digest = _sha256(file_path)
    except OSError as exc:
        return {
            "path": rel, "kind": kind, "ext": ext,
            "extraction": {"status": "failed", "notes": f"stat/hash error: {exc}"},
        }

    entry: dict[str, Any] = {
        "path": rel,
        "category": rel.split("/")[1] if rel.startswith(("inputs/", "context/")) and "/" in rel[7:] else "",
        "ext": ext,
        "kind": kind,
        "sha256": digest,
        "size_bytes": size,
    }

    # Idempotency: unchanged file with an existing sidecar → reuse prior entry.
    previous = prior.get(rel)
    if (
        not force
        and previous
        and previous.get("sha256") == digest
        and (
            previous.get("extraction", {}).get("status") != "extracted"
            or (run_dir / (previous.get("extraction", {}).get("text_path") or "")).exists()
        )
    ):
        return {**previous, **entry}

    # Text and images need no conversion.
    if kind == "text":
        entry["extraction"] = {"status": "passthrough", "text_path": rel,
                               "notes": "already text; read directly"}
        return entry
    if kind == "image":
        entry["extraction"] = {"status": "passthrough", "text_path": None,
                               "notes": "image; read directly with the Read tool (multimodal)"}
        return entry
    if kind == "unknown":
        entry["extraction"] = {"status": "unsupported", "text_path": None,
                               "notes": f"no extractor for '{ext}'; open the original if needed"}
        return entry

    if size > MAX_PARSE_BYTES:
        entry["extraction"] = {"status": "skipped_large", "text_path": None,
                               "notes": f"file > {MAX_PARSE_BYTES // (1024 * 1024)}MB; not parsed, open original"}
        return entry

    # Run the format-specific extractor with full isolation.
    ingested_root = run_dir / rel.split("/", 1)[0] / INGESTED_DIRNAME
    sidecar = ingested_root / (Path(rel).relative_to(rel.split("/", 1)[0]).as_posix() + ".md")
    assets_dir = ingested_root / ASSETS_DIRNAME
    asset_stem = Path(rel).stem
    extractor = _EXTRACTORS[kind]
    try:
        text, assets, notes, reader = extractor(file_path, assets_dir, asset_stem)
    except ImportError as exc:
        entry["extraction"] = {"status": "unsupported", "text_path": None,
                               "notes": f"missing library: {exc}"}
        return entry
    except Exception as exc:  # corrupt / password-protected / unexpected
        entry["extraction"] = {
            "status": "failed", "text_path": None,
            "notes": f"{type(exc).__name__}: {exc}".strip()[:300],
            "trace": traceback.format_exc(limit=2)[:500],
        }
        return entry

    _write_text(sidecar, text)
    entry["extraction"] = {
        "status": "extracted",
        "text_path": _rel(sidecar, run_dir),
        "assets": [_rel(assets_dir / a, run_dir) for a in assets],
        "approx_tokens": _approx_tokens(text),
        "reader": reader,
        "notes": notes,
    }
    return entry


def _iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name in SKIP_NAMES or name.startswith("."):
                continue
            yield Path(dirpath) / name


def ingest_run(run_dir: Path, roots: list[str], force: bool = False) -> dict:
    """Ingest all configured roots under ``run_dir``; write the manifest; return it."""
    run_dir = run_dir.resolve()
    manifest_path = run_dir / MANIFEST_NAME
    prior: dict[str, dict] = {}
    if manifest_path.exists():
        try:
            for item in json.loads(manifest_path.read_text(encoding="utf-8")).get("files", []):
                if isinstance(item, dict) and item.get("path"):
                    prior[item["path"]] = item
        except (OSError, json.JSONDecodeError):
            prior = {}

    files: list[dict] = []
    for root_name in roots:
        root = run_dir / root_name
        if not root.is_dir():
            continue
        for file_path in _iter_files(root):
            files.append(_ingest_file(file_path, run_dir, force, prior))

    files.sort(key=lambda e: e["path"])
    summary: dict[str, int] = {"total": len(files)}
    for e in files:
        status = e.get("extraction", {}).get("status", "unknown")
        summary[status] = summary.get(status, 0) + 1

    manifest = {
        "version": 1,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "roots": roots,
        "summary": summary,
        "files": files,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic input ingestion for agent runs.")
    parser.add_argument("--root", default=".", help="Run directory (default: cwd).")
    parser.add_argument("--roots", nargs="*", default=list(DEFAULT_ROOTS),
                        help="Subdirectories under the run dir to ingest (default: inputs context).")
    parser.add_argument("--force", action="store_true", help="Re-convert even unchanged files.")
    parser.add_argument("--quiet", action="store_true", help="Suppress the summary line.")
    args = parser.parse_args(argv)

    run_dir = Path(args.root).resolve()
    if not run_dir.is_dir():
        print(f"error: run dir not found: {run_dir}", file=sys.stderr)
        return 2

    manifest = ingest_run(run_dir, args.roots, force=args.force)
    if not args.quiet:
        s = manifest["summary"]
        print(
            f"ingested {s.get('total', 0)} file(s): "
            + ", ".join(f"{k}={v}" for k, v in s.items() if k != "total")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
