#!/usr/bin/env python3
"""Recovery-only tool: rebuild column_mappings.json from surviving inputs.

This script is NOT part of the default /design-architecture happy path. The default
path writes column_mappings.json directly via per-table Edits from the orchestrator.

Use this script only when:
  * column_mappings.json got corrupted mid-run (invalid JSON, truncated write), OR
  * a legacy run wrote per-layer chunk files (``column_mappings_L*.json``) that need
    merging into the single canonical file, OR
  * you have a good target_model_design.md but the JSON was lost.

Merge path (if per-layer chunks are present): reads ``column_mappings_L*.json`` (or
``column_mappings_{layer}.json``) and concatenates them, deduplicating.

Fallback path (if no chunks): parses ``target_model_design.md`` into JSON entries.
Each target table is a level-2 Markdown heading followed by grain/SK strategy lines
and a columns table with headers:
  Column, Data Type, Nullable, PK, Filter Conditions, Join Conditions, Source Reference, Description

Usage:
    python generate_column_mappings.py --design-dir outputs/00_state/design
    python generate_column_mappings.py --design-dir outputs/00_state/design --output custom_path.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FORBIDDEN_RE = re.compile(
    r"(ADDITIONAL_|PLACEHOLDER_|REMAINING_|TBD|TO_BE_DEFINED|TO_BE_DETERMINED|_columns\b)",
    re.IGNORECASE,
)
TABLE_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
SUBHEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
NO_FILTER_CONDITION = "-"
NO_JOIN_CONDITION = "-"


def split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def has_forbidden(value: Any) -> bool:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return bool(FORBIDDEN_RE.search(text))


def parse_target_model(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    tables: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        table_match = TABLE_HEADING_RE.match(line)
        if table_match:
            if current:
                tables.append(current)
            current = {
                "table_name": table_match.group(1).strip(),
                "grain": "",
                "sk_strategy": "",
                "columns": [],
            }
            i += 1
            continue

        if current and line.lower().startswith("grain:"):
            current["grain"] = line.split(":", 1)[1].strip()
        elif current and line.lower().startswith("sk strategy:"):
            current["sk_strategy"] = line.split(":", 1)[1].strip()
        elif current and SUBHEADING_RE.match(line):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("|"):
                j += 1
            if j + 1 < len(lines):
                headers = [normalize_header(cell) for cell in split_markdown_row(lines[j])]
                required = ["column", "data_type", "nullable", "pk", "source_reference", "description"]
                if all(header in headers for header in required):
                    j += 2
                    while j < len(lines) and lines[j].strip().startswith("|"):
                        values = split_markdown_row(lines[j])
                        if len(values) == len(headers):
                            row = dict(zip(headers, values))
                            column_name = row.get("column", "").strip()
                            if column_name:
                                source_reference = row.get("source_reference", "").strip()
                                needs_review = not source_reference
                                current["columns"].append(
                                    {
                                        "column_name": column_name,
                                        "data_type": row.get("data_type", "").strip(),
                                        "nullable": row.get("nullable", "").strip(),
                                        "pk": row.get("pk", "").strip(),
                                        "filter_conditions": (
                                            row.get("filter_conditions", "").strip()
                                            or row.get("filter_condition", "").strip()
                                            or NO_FILTER_CONDITION
                                        ),
                                        "join_conditions": (
                                            row.get("join_conditions", "").strip()
                                            or row.get("join_condition", "").strip()
                                            or NO_JOIN_CONDITION
                                        ),
                                        "source_reference": source_reference or "[NEEDS_HUMAN_REVIEW]",
                                        "source_reference_reason": (
                                            "Missing Source Reference in target_model_design.md"
                                            if needs_review
                                            else ""
                                        ),
                                        "description": row.get("description", "").strip(),
                                    }
                                )
                        j += 1
                    i = j - 1
        i += 1

    if current:
        tables.append(current)
    return tables


def load_layer_chunks(design_dir: Path) -> list[dict[str, Any]]:
    """Merge per-layer chunks in a deterministic order.

    Accepts either ``column_mappings_L*.json`` or ``column_mappings_{layer}.json``.
    Duplicate (table, column) across chunks is a hard error.
    """
    chunks = sorted(design_dir.glob("column_mappings_*.json"))
    chunks = [c for c in chunks if c.name != "column_mappings.json"]
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for chunk in chunks:
        payload = json.loads(chunk.read_text(encoding="utf-8"))
        tables = payload.get("tables", payload if isinstance(payload, list) else [])
        for table in tables:
            table_name = table.get("table_name") or table.get("name")
            columns = table.get("columns", [])
            normalized_columns = []
            for column in columns:
                column_name = (
                    column.get("column_name")
                    or column.get("name")
                    or column.get("column")
                )
                key = (str(table_name), str(column_name))
                if key in seen:
                    raise ValueError(
                        f"Duplicate column across chunks: {table_name}.{column_name}"
                    )
                seen.add(key)
                normalized_column = {**column, "column_name": column_name}
                if "filter_conditions" not in normalized_column and "filter_condition" in normalized_column:
                    normalized_column["filter_conditions"] = normalized_column["filter_condition"]
                if "join_conditions" not in normalized_column and "join_condition" in normalized_column:
                    normalized_column["join_conditions"] = normalized_column["join_condition"]
                normalized_columns.append(normalized_column)
            merged.append({**table, "table_name": table_name, "columns": normalized_columns})
    return merged


def validate_tables(tables: list[dict[str, Any]]) -> tuple[int, int, int]:
    flagged = 0
    column_count = 0
    for table in tables:
        if has_forbidden(table.get("table_name", "")):
            raise ValueError(f"Forbidden pattern in table name: {table.get('table_name')}")
        for column in table.get("columns", []):
            column_count += 1
            if has_forbidden(column):
                raise ValueError(
                    f"Forbidden pattern in column mapping: {table.get('table_name')}.{column}"
                )
            if not column.get("source_reference"):
                column["source_reference"] = "[NEEDS_HUMAN_REVIEW]"
                column["source_reference_reason"] = "Missing source reference"
            if not str(column.get("filter_conditions") or column.get("filter_condition") or "").strip():
                column["filter_conditions"] = NO_FILTER_CONDITION
            if not str(column.get("join_conditions") or column.get("join_condition") or "").strip():
                column["join_conditions"] = NO_JOIN_CONDITION
            if str(column.get("source_reference", "")).startswith("[NEEDS_HUMAN_REVIEW]"):
                flagged += 1
    return len(tables), column_count, flagged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--design-dir",
        type=Path,
        required=True,
        help="Path to outputs/00_state/design",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output column_mappings.json path (default: <design-dir>/column_mappings.json)",
    )
    args = parser.parse_args()

    design_dir = args.design_dir
    target_model = design_dir / "target_model_design.md"

    try:
        tables = load_layer_chunks(design_dir)
        if not tables:
            if not target_model.exists():
                print(
                    "ERROR: no column_mappings_*.json chunks and no target_model_design.md fallback",
                    file=sys.stderr,
                )
                return 1
            tables = parse_target_model(target_model)
        if not tables:
            raise ValueError(
                "No target tables parsed from column_mappings chunks or target_model_design.md"
            )
        table_count, column_count, flagged = validate_tables(tables)
    except Exception as exc:  # noqa: BLE001 - CLI should print any validation error clearly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "schema_version": "column-mappings-1.0",
        "tables": tables,
        "summary": {
            "table_count": table_count,
            "column_count": column_count,
            "needs_human_review_count": flagged,
        },
    }
    output = args.output or (design_dir / "column_mappings.json")
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{table_count} tables, {column_count} columns, {flagged} flagged for human review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
