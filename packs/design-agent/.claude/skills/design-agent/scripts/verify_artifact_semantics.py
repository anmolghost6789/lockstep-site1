#!/usr/bin/env python3
"""Semantic post-generation checks for the design-artifact phase.

Runs three deterministic checks that our LLM-based evaluator does not perform
by inspection:

1. **DQ SQL validity** — parse every ``DQ Rule Expression`` cell in every
   ``DQ_*.xlsx`` workbook via ``sqlglot``. Catches any SQL syntax problem in
   the composed WHERE clause (dangling parentheses, unclosed quotes, invalid
   operators, malformed keyword ordering, etc.). This is a general validity
   invariant, not a fix for any single bug.
2. **ER Mermaid vs column_mappings diff** on every per-layer
   ``ER_DIAGRAM_{layer}.md`` file. Any table's column set in the Mermaid block
   must be a subset of that table's columns in ``column_mappings.json``. No
   invented columns; no dropped real columns.
3. **Encoding check** — smoke-scan every generated workbook cell and every
   design JSON for the classic UTF-8→cp1252 corruption sequences
   (``Â§``, ``â€"``, ``â€œ``, ``â€\x9d``, …) that appear when a file gets read
   or written without ``encoding='utf-8'`` on Windows.

Exit code:
* ``0`` — all three checks passed.
* ``1`` — one or more failures. Report JSON contains the details.
* ``2`` — the script itself could not run (missing dependency, missing input).

Usage:
    python verify_artifact_semantics.py \
        --artifacts-dir outputs/05_artifacts \
        --design-dir outputs/00_state/design \
        --report outputs/00_state/semantic_check.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    load_workbook = None  # type: ignore[assignment]

try:
    import sqlglot
    from sqlglot.errors import ParseError
except ImportError:  # pragma: no cover
    sqlglot = None  # type: ignore[assignment]
    ParseError = Exception  # type: ignore[assignment,misc]


ENCODING_MOJIBAKE_SEQUENCES = [
    "Â§",
    "â€\x9d",
    "â€œ",
    "â€\x93",
    "â€\x94",
    "â€\x99",
    "â€\x98",
    "Ã©",
    "Ã¨",
    "Ã¡",
    "Ã¢",
    "Ã\xad",
    "Ã¶",
    "Ãœ",
    "Â",  # kept last; only flag if adjacent to non-ASCII to reduce false positives
]

DQ_EXPRESSION_HEADER_CANDIDATES = {
    "DQ Rule Expression",
    "Rule Expression",
    "SQL Expression",
    "Expression",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_mermaid_columns(md_path: Path) -> dict[str, set[str]]:
    """Parse an erDiagram fenced Mermaid block; return {table_name: {column_name, ...}}."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    fenced = re.findall(r"```mermaid\s*(.*?)```", text, flags=re.DOTALL)
    if not fenced:
        return {}
    block = "\n".join(fenced)
    tables: dict[str, set[str]] = {}
    # erDiagram entries look like:  TABLE_NAME {\n TYPE column_name [PK|FK]\n }
    for match in re.finditer(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\{([^}]*)\}", block, flags=re.DOTALL
    ):
        table_name = match.group(1)
        body = match.group(2)
        cols: set[str] = set()
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            # split on whitespace: <TYPE> <name> [PK|FK]
            parts = line.split()
            if len(parts) >= 2:
                cols.add(parts[1].lower())
        if cols:
            tables[table_name.lower()] = cols
    return tables


def _column_mappings_by_table(mappings: dict) -> dict[str, dict[str, set[str]]]:
    """Return {layer: {table_lower: {col_lower, ...}}} for the shape we ship."""
    out: dict[str, dict[str, set[str]]] = {}
    layers = mappings.get("layers") or {}
    if isinstance(layers, dict):
        for layer, payload in layers.items():
            tables = payload.get("tables") if isinstance(payload, dict) else None
            layer_map: dict[str, set[str]] = {}
            if isinstance(tables, dict):
                for tname, tbody in tables.items():
                    cols = set()
                    for c in (tbody or {}).get("columns", []) or []:
                        name = (c.get("name") or c.get("column_name") or "").strip()
                        if name:
                            cols.add(name.lower())
                    layer_map[tname.lower()] = cols
            elif isinstance(tables, list):
                for tbody in tables:
                    tname = tbody.get("table_name") or tbody.get("name")
                    if not tname:
                        continue
                    cols = set()
                    for c in tbody.get("columns", []) or []:
                        name = (c.get("name") or c.get("column_name") or "").strip()
                        if name:
                            cols.add(name.lower())
                    layer_map[tname.lower()] = cols
            out[layer] = layer_map
    return out


def _check_dq_sql(artifacts_dir: Path) -> list[dict]:
    """Parse every DQ_*.xlsx expression cell with sqlglot; return list of errors."""
    errors: list[dict] = []
    if load_workbook is None:
        return [{"check": "dq_sql", "error": "openpyxl not installed"}]
    if sqlglot is None:
        return [{"check": "dq_sql", "error": "sqlglot not installed"}]

    for xlsx in artifacts_dir.rglob("DQ_*.xlsx"):
        try:
            wb = load_workbook(xlsx, read_only=True, data_only=True)
        except Exception as exc:  # pragma: no cover
            errors.append({"check": "dq_sql", "file": str(xlsx), "error": f"open failed: {exc}"})
            continue
        for sheet_name in wb.sheetnames:
            if sheet_name.startswith("_") or sheet_name == "table_tracker":
                continue
            ws = wb[sheet_name]
            rows_iter = ws.iter_rows(values_only=True)
            header_row = None
            header_map: dict[str, int] = {}
            # DQ detail header is at row 7; scan first ~12 rows to find any of our candidates
            for row_idx, row in enumerate(rows_iter, start=1):
                if row is None:
                    continue
                for col_idx, val in enumerate(row):
                    if isinstance(val, str) and val.strip() in DQ_EXPRESSION_HEADER_CANDIDATES:
                        header_row = row_idx
                        header_map = {
                            (c or "").strip(): i for i, c in enumerate(row) if isinstance(c, str)
                        }
                        break
                if header_row:
                    break
            if not header_row:
                continue
            expr_col = None
            for candidate in DQ_EXPRESSION_HEADER_CANDIDATES:
                if candidate in header_map:
                    expr_col = header_map[candidate]
                    break
            filter_col = header_map.get("Filter Conditions")
            rule_type_col = header_map.get("Rule Type")
            # Re-iterate after header
            for row_idx, row in enumerate(
                ws.iter_rows(min_row=header_row + 1, values_only=True),
                start=header_row + 1,
            ):
                if not row or expr_col is None or expr_col >= len(row):
                    continue
                expr = row[expr_col]
                if not isinstance(expr, str):
                    continue
                expr = expr.strip()
                if not expr or expr.upper().startswith("[NEEDS_HUMAN_REVIEW"):
                    continue
                if expr.upper().startswith("[CUSTOM_SQL") or (
                    rule_type_col is not None
                    and rule_type_col < len(row)
                    and isinstance(row[rule_type_col], str)
                    and row[rule_type_col].strip().upper() == "CUSTOM_SQL"
                ):
                    # CUSTOM_SQL: expect a full SELECT statement
                    to_parse = expr
                else:
                    filter_cond = None
                    if (
                        filter_col is not None
                        and filter_col < len(row)
                        and isinstance(row[filter_col], str)
                    ):
                        filter_cond = row[filter_col].strip()
                        if filter_cond in {"", "-"}:
                            filter_cond = None
                    # Compose the same way the generator should:
                    predicate = expr
                    if predicate.upper().startswith("WHERE "):
                        # This is the exact double-WHERE precursor; flag it.
                        errors.append(
                            {
                                "check": "dq_sql",
                                "file": str(xlsx),
                                "sheet": sheet_name,
                                "row": row_idx,
                                "error": "expression starts with WHERE (must be bare predicate per stage 03 R8)",
                                "expression": expr,
                            }
                        )
                        predicate = predicate[6:].strip()
                    where_clause = (
                        f"WHERE ({filter_cond}) AND ({predicate})"
                        if filter_cond
                        else f"WHERE ({predicate})"
                    )
                    to_parse = f"SELECT 1 FROM t {where_clause}"
                try:
                    sqlglot.parse_one(to_parse)
                except ParseError as exc:
                    errors.append(
                        {
                            "check": "dq_sql",
                            "file": str(xlsx),
                            "sheet": sheet_name,
                            "row": row_idx,
                            "expression": expr,
                            "error": f"sqlglot parse error: {exc}",
                        }
                    )
    return errors


def _check_er_mermaid(artifacts_dir: Path, design_dir: Path) -> list[dict]:
    """Compare per-layer ER Mermaid columns against column_mappings.json."""
    mapping_path = design_dir / "column_mappings.json"
    if not mapping_path.exists():
        return [{"check": "er_mermaid", "error": f"missing {mapping_path}"}]
    try:
        mappings = _read_json(mapping_path)
    except Exception as exc:
        return [{"check": "er_mermaid", "error": f"cannot read {mapping_path}: {exc}"}]

    layer_table_cols = _column_mappings_by_table(mappings)
    errors: list[dict] = []
    md_files = list(artifacts_dir.rglob("ER_DIAGRAM_*.md"))
    if not md_files:
        return errors
    for md in md_files:
        # Skip the whole-flow lineage doc; it's flowchart LR, not per-column.
        if md.name == "ER_DIAGRAM_LINEAGE.md":
            continue
        layer_match = re.match(r"ER_DIAGRAM_([A-Za-z0-9]+)", md.stem)
        if not layer_match:
            continue
        layer = layer_match.group(1)
        # normalize layer key against column_mappings.json (accept L0 vs L0_Raw etc.)
        candidates = [layer, layer.upper(), layer.lower()]
        for key in list(layer_table_cols.keys()):
            if key.lower().startswith(layer.lower()) or layer.lower().startswith(key.lower()):
                candidates.append(key)
        design_layer_map: dict[str, set[str]] | None = None
        for c in candidates:
            if c in layer_table_cols:
                design_layer_map = layer_table_cols[c]
                break
        if design_layer_map is None:
            errors.append(
                {
                    "check": "er_mermaid",
                    "file": str(md),
                    "error": f"could not find layer '{layer}' in column_mappings.json",
                }
            )
            continue
        mermaid_tables = _collect_mermaid_columns(md)
        for tname, mcols in mermaid_tables.items():
            design_cols = design_layer_map.get(tname)
            if design_cols is None:
                errors.append(
                    {
                        "check": "er_mermaid",
                        "file": str(md),
                        "table": tname,
                        "error": "table not in column_mappings.json for this layer",
                    }
                )
                continue
            extras = sorted(mcols - design_cols)
            missing = sorted(design_cols - mcols)
            if extras or missing:
                errors.append(
                    {
                        "check": "er_mermaid",
                        "file": str(md),
                        "table": tname,
                        "invented_columns": extras,
                        "missing_columns": missing,
                    }
                )
    return errors


def _check_encoding(artifacts_dir: Path, design_dir: Path) -> list[dict]:
    """Scan workbook cells and design JSONs for UTF-8→cp1252 corruption sequences.

    This is a smoke test for encoding discipline: the real fix is to open every
    file with ``encoding='utf-8'`` in the generator. When that discipline holds,
    this check stays green. When it slips, the classic corruption sequences
    (``Â§``, ``â€"``, …) will start showing up in workbook cells or design JSONs
    and this check flags them.
    """
    errors: list[dict] = []
    # Workbooks
    if load_workbook is not None:
        for xlsx in artifacts_dir.rglob("*.xlsx"):
            try:
                wb = load_workbook(xlsx, read_only=True, data_only=True)
            except Exception:
                continue
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                    for col_idx, val in enumerate(row, start=1):
                        if not isinstance(val, str):
                            continue
                        for seq in ENCODING_MOJIBAKE_SEQUENCES:
                            if seq in val:
                                errors.append(
                                    {
                                        "check": "encoding",
                                        "file": str(xlsx),
                                        "sheet": sheet,
                                        "row": row_idx,
                                        "col": col_idx,
                                        "sequence": seq,
                                        "sample": val[:120],
                                    }
                                )
                                break
    # Design JSONs
    for js in design_dir.rglob("*.json"):
        try:
            text = js.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for seq in ENCODING_MOJIBAKE_SEQUENCES:
            if seq in text:
                errors.append(
                    {
                        "check": "encoding",
                        "file": str(js),
                        "sequence": seq,
                    }
                )
                break
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--design-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    if not args.artifacts_dir.exists():
        print(f"artifacts-dir does not exist: {args.artifacts_dir}", file=sys.stderr)
        return 2
    if not args.design_dir.exists():
        print(f"design-dir does not exist: {args.design_dir}", file=sys.stderr)
        return 2

    report: dict[str, Any] = {
        "artifacts_dir": str(args.artifacts_dir),
        "design_dir": str(args.design_dir),
        "checks": {},
    }

    dq_errors = _check_dq_sql(args.artifacts_dir)
    er_errors = _check_er_mermaid(args.artifacts_dir, args.design_dir)
    encoding_errors = _check_encoding(args.artifacts_dir, args.design_dir)

    report["checks"]["dq_sql"] = {"passed": not dq_errors, "errors": dq_errors}
    report["checks"]["er_mermaid"] = {"passed": not er_errors, "errors": er_errors}
    report["checks"]["encoding"] = {"passed": not encoding_errors, "errors": encoding_errors}

    total_errors = len(dq_errors) + len(er_errors) + len(encoding_errors)
    report["total_errors"] = total_errors
    report["passed"] = total_errors == 0

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if total_errors:
        print(
            f"verify_artifact_semantics: {total_errors} error(s) — see {args.report}",
            file=sys.stderr,
        )
        return 1
    print(f"verify_artifact_semantics: all checks passed (report: {args.report})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
