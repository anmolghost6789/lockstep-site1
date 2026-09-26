#!/usr/bin/env python3
"""Render the human-readable ``target_model_design.md`` from the canonical
design JSONs.

The design phase is JSON-as-source: the model writes each design fact exactly
once into ``column_mappings.json`` (columns + per-table/per-layer metadata) and
``dq_rules_design.json`` (DQ rules). This script produces the human-review
markdown as a pure derived view — per-layer sections, per-table metadata lines,
column tables, and DQ rule tables.

The rendered file must never be hand-edited. If the review reveals a problem,
fix the JSONs and re-render.

Deterministic and stdlib-only: same inputs always produce the same markdown.

Usage:
    python render_design_md.py --design-dir outputs/00_state/design
    python render_design_md.py --design-dir outputs/00_state/design \
        --out outputs/00_state/design/target_model_design.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COLUMN_HEADERS = [
    "Column", "Data Type", "Nullable", "PK", "Filter Conditions",
    "Join Conditions", "Source Reference", "Description",
]
DQ_HEADERS = [
    "Rule ID", "Column", "Rule Type", "Severity", "DQ Rule Expression",
    "Threshold", "Source Reference",
]

RENDER_BANNER = (
    "_Rendered from `column_mappings.json` + `dq_rules_design.json` by "
    "`render_design_md.py`. Do NOT hand-edit this file - edit the JSONs and "
    "re-render._"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _cell(value) -> str:
    """Markdown-table-safe cell text; '-' for empty."""
    text = str(value if value is not None else "").strip()
    if not text:
        return "-"
    return text.replace("|", "\\|").replace("\n", " ")


def _yn(value) -> str:
    if isinstance(value, bool):
        return "Y" if value else "N"
    text = str(value or "").strip().upper()
    return "Y" if text in {"Y", "YES", "TRUE", "1"} else "N"


def _md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def load_model(design_dir: Path) -> tuple[dict, dict, dict, list[str]]:
    """Return (layers_meta, tables_meta, grouped mappings, layer order)."""
    mapping_path = design_dir / "column_mappings.json"
    if not mapping_path.exists():
        raise SystemExit(f"FATAL: missing {mapping_path}")
    doc = _read_json(mapping_path)
    mappings = doc.get("mappings") or []
    if not mappings:
        raise SystemExit(f"FATAL: {mapping_path} has no 'mappings' entries")

    layers_meta: dict[str, dict] = {}
    layer_order: list[str] = []
    for layer in doc.get("layers") or []:
        lid = str(layer.get("id") or "").strip()
        if lid and lid not in layers_meta:
            layers_meta[lid] = layer
            layer_order.append(lid)

    tables_meta: dict[tuple[str, str], dict] = {}
    for tmeta in doc.get("tables") or []:
        lid = str(tmeta.get("layer") or "").strip()
        tname = str(tmeta.get("table") or tmeta.get("target_table") or "").strip()
        if lid and tname:
            tables_meta[(lid, tname)] = tmeta

    grouped: dict[str, dict[str, list[dict]]] = {}
    for entry in mappings:
        lid = str(entry.get("layer") or "").strip()
        tname = str(entry.get("target_table") or "").strip()
        cname = str(entry.get("target_column") or "").strip()
        if not lid or not tname or not cname:
            print(f"WARNING: skipping mapping entry missing layer/table/column: {entry}",
                  file=sys.stderr)
            continue
        if lid not in grouped:
            grouped[lid] = {}
            if lid not in layer_order:
                layer_order.append(lid)
        grouped[lid].setdefault(tname, []).append(entry)

    return layers_meta, tables_meta, grouped, layer_order


def load_rules(design_dir: Path) -> dict[tuple[str, str], list[dict]]:
    rules_path = design_dir / "dq_rules_design.json"
    if not rules_path.exists():
        print(f"WARNING: {rules_path} missing — DQ tables will be empty", file=sys.stderr)
        return {}
    grouped: dict[tuple[str, str], list[dict]] = {}
    for rule in _read_json(rules_path).get("rules") or []:
        lid = str(rule.get("layer") or "").strip()
        tname = str(rule.get("target_table") or "").strip()
        if lid and tname:
            grouped.setdefault((lid, tname), []).append(rule)
    return grouped


def render(design_dir: Path) -> str:
    layers_meta, tables_meta, grouped, layer_order = load_model(design_dir)
    rules = load_rules(design_dir)

    lines: list[str] = ["# Target Model Design", "", RENDER_BANNER, ""]
    for lid in layer_order:
        tables = grouped.get(lid, {})
        lmeta = layers_meta.get(lid, {})
        title = str(lmeta.get("title") or "").strip() or f"Layer {lid}"
        lines += [f"# {title}", ""]
        layer_schema = _cell(lmeta.get("schema"))
        layer_database = _cell(lmeta.get("database"))
        if layer_schema != "-" or layer_database != "-":
            lines += [f"Schema: {layer_schema}", f"Database: {layer_database}", ""]
        if not tables:
            lines += ["_(no tables designed for this layer)_", ""]
            continue
        for tname, cols in tables.items():
            tmeta = tables_meta.get((lid, tname), {})
            lines += [f"## {tname}", ""]
            lines.append(f"Grain: {_cell(tmeta.get('grain'))}")
            lines.append(f"SK Strategy: {_cell(tmeta.get('key_strategy') or tmeta.get('sk_strategy'))}")
            lines.append(f"Business Purpose: {_cell(tmeta.get('purpose'))}")
            lines.append(f"Load Strategy: {_cell(tmeta.get('load_strategy'))}")
            lines.append(f"Frequency: {_cell(tmeta.get('frequency'))}")
            lines.append(f"Schema: {_cell(tmeta.get('schema') or lmeta.get('schema'))}")
            lines.append(f"Database: {_cell(tmeta.get('database') or lmeta.get('database'))}")
            lines.append("")
            rows = []
            for c in cols:
                rows.append([
                    _cell(c.get("target_column")),
                    _cell(c.get("data_type")),
                    _yn(c.get("nullable")),
                    _yn(c.get("is_primary_key")),
                    _cell(c.get("filter_conditions")),
                    _cell(c.get("join_conditions")),
                    _cell(c.get("source_reference")),
                    _cell(c.get("description")),
                ])
            lines += _md_table(COLUMN_HEADERS, rows) + [""]
            table_rules = rules.get((lid, tname), [])
            lines += ["### DQ Rules", ""]
            if table_rules:
                rule_rows = []
                for r in table_rules:
                    rule_rows.append([
                        _cell(r.get("rule_id")),
                        _cell(r.get("target_column")),
                        _cell(r.get("rule_type")),
                        _cell(r.get("severity")),
                        _cell(r.get("dq_rule_expression")),
                        _cell(r.get("threshold_value")),
                        _cell(r.get("source_reference")),
                    ])
                lines += _md_table(DQ_HEADERS, rule_rows) + [""]
            else:
                lines += ["_(no DQ rules recorded — design-architecture rule R6 requires at least one entry per table)_", ""]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", required=True, type=Path,
                    help="outputs/00_state/design (column_mappings.json + dq_rules_design.json)")
    ap.add_argument("--out", type=Path, default=None,
                    help="output markdown path (default: {design-dir}/target_model_design.md)")
    args = ap.parse_args()

    out = args.out or (args.design_dir / "target_model_design.md")
    text = render(args.design_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    tables = text.count("\n## ")
    print(f"rendered {out} ({tables} tables)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
