#!/usr/bin/env python3
"""Emit the execution plan (plan.json) from the canonical design JSONs.

The plan is mechanical: generation waves are a topological sort of the
FK/semantic relationships already declared in ``column_mappings.json``
(``join_conditions`` cells), and output paths are formulas over the layer
list. The model does not type these facts — it runs this script and adds a
judgment ``notes`` entry only when judgment genuinely exists (waivers,
sub-wave splits on big layers, risky volumes).

Deterministic and stdlib-only.

Usage:
    python build_plan.py --design-dir outputs/00_state/design \
        --out outputs/00_state/execution_plan/plan.json \
        [--artifacts-root outputs/05_artifacts]
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

MAX_TABLES_PER_WAVE = 15
SUBAGENT_TABLE_THRESHOLD = 15

REL_RE = re.compile(r"([A-Za-z_][\w]*)\.([\w]+)\s*(?:=|->)\s*([A-Za-z_][\w]*)\.([\w]+)")
SHORT_REL_RE = re.compile(r"(\w+)\s*->\s*([A-Za-z_][\w]*)\.([\w]+)")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_design(design_dir: Path) -> dict:
    """Group column_mappings.json into {layer: {table: [column entries]}}."""
    mapping_path = design_dir / "column_mappings.json"
    if not mapping_path.exists():
        raise SystemExit(f"FATAL: missing {mapping_path}")
    doc = _read_json(mapping_path)
    mappings = doc.get("mappings") or []
    if not mappings:
        raise SystemExit(f"FATAL: {mapping_path} has no 'mappings' entries")
    layers: dict[str, dict[str, list[dict]]] = {}
    for entry in mappings:
        lid = str(entry.get("layer") or "").strip()
        table = str(entry.get("target_table") or "").strip()
        column = str(entry.get("target_column") or "").strip()
        if not lid or not table or not column:
            print(f"WARNING: skipping mapping entry missing layer/table/column: {entry}",
                  file=sys.stderr)
            continue
        layers.setdefault(lid, {}).setdefault(table, []).append(entry)
    doc["_grouped_layers"] = layers
    return doc


def relationships(layers: dict[str, dict[str, list[dict]]]) -> list[dict]:
    """Derive FK/semantic edges from join_conditions cells (generator-compatible)."""
    rels, seen = [], set()
    for lid, tables in layers.items():
        for tname, cols in tables.items():
            for col in cols:
                jc = str(col.get("join_conditions") or "").strip()
                if not jc or jc == "-":
                    continue
                kind = "FK" if jc.startswith("FK:") else "semantic"
                matched = False
                for g in REL_RE.finditer(jc):
                    a_t, a_c, b_t, b_c = g.groups()
                    ft, fc, tt, tc = a_t, a_c, b_t, b_c
                    if ft != tname and tt == tname:
                        ft, fc, tt, tc = b_t, b_c, a_t, a_c
                    if ft == tt:
                        continue
                    matched = True
                    key = (ft, fc, tt, tc)
                    if key not in seen:
                        seen.add(key)
                        rels.append({"from_table": ft, "from_column": fc,
                                     "to_table": tt, "to_column": tc,
                                     "kind": kind, "layer": lid})
                if not matched:
                    g2 = SHORT_REL_RE.search(jc)
                    if g2:
                        key = (tname, g2.group(1), g2.group(2), g2.group(3))
                        if key not in seen:
                            seen.add(key)
                            rels.append({"from_table": tname, "from_column": g2.group(1),
                                         "to_table": g2.group(2), "to_column": g2.group(3),
                                         "kind": "semantic", "layer": lid})
    return rels


def topo_waves(tables: list[str], rels: list[dict]) -> list[list[str]]:
    """Group tables into dependency waves: a table lands one wave after the
    deepest table it references. Cycles flatten instead of recursing forever."""
    deps = defaultdict(set)
    tset = set(tables)
    for r in rels:
        if r["from_table"] in tset and r["to_table"] in tset:
            deps[r["from_table"]].add(r["to_table"])
    depth: dict[str, int] = {}

    def d(t: str, stack: frozenset = frozenset()) -> int:
        if t in depth:
            return depth[t]
        if t in stack:
            return 0
        depth[t] = 1 + max((d(p, stack | {t}) for p in deps.get(t, ())), default=-1)
        return depth[t]

    for t in tables:
        d(t)
    waves: dict[int, list[str]] = defaultdict(list)
    for t in tables:
        waves[depth[t]].append(t)
    return [sorted(waves[k]) for k in sorted(waves)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design-dir", required=True, type=Path,
                    help="outputs/00_state/design (column_mappings.json)")
    ap.add_argument("--out", required=True, type=Path,
                    help="outputs/00_state/execution_plan/plan.json")
    ap.add_argument("--artifacts-root", default="outputs/05_artifacts",
                    help="Root path used in file_plan entries (default: outputs/05_artifacts)")
    args = ap.parse_args()

    doc = load_design(args.design_dir)
    layers = doc["_grouped_layers"]
    layer_meta = {str(l.get("id") or "").strip(): l for l in doc.get("layers") or []}
    rels = relationships(layers)
    out_root = args.artifacts_root

    layers_out, files, waves_out = [], [], []
    total_tables = 0
    group = 0
    for lid, tables in layers.items():
        table_names = list(tables.keys())
        total_tables += len(table_names)
        lmeta = layer_meta.get(lid, {})
        layers_out.append({
            "layer": lid,
            "tables": len(table_names),
            "schema": str(lmeta.get("schema") or "-"),
            "database": str(lmeta.get("database") or "-"),
        })
        for wave in topo_waves(table_names, [r for r in rels if r["layer"] == lid]):
            chunks = [wave[i:i + MAX_TABLES_PER_WAVE]
                      for i in range(0, len(wave), MAX_TABLES_PER_WAVE)] or [wave]
            for chunk in chunks:
                group += 1
                waves_out.append({"parallel_group": group, "layer": lid, "tables": chunk})
        for art, ext in (("STTM", "xlsx"), ("DATA_MODEL", "xlsx"), ("DQ", "xlsx"), ("ER_DIAGRAM", "md")):
            files.append({"path": f"{out_root}/{lid}/{art}_{lid}.{ext}", "artifact": art, "layer": lid})
    files.append({"path": f"{out_root}/ER_DIAGRAM.xlsx", "artifact": "ER_DIAGRAM_XLSX", "layer": "ALL"})
    files.append({"path": f"{out_root}/ER_DIAGRAM_LINEAGE.md", "artifact": "ER_LINEAGE_MD", "layer": "ALL"})

    plan = {
        "schema_version": "plan-2.0",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "generated_by": ("build_plan.py (computed from column_mappings.json; "
                         "waves = topological sort of join_conditions relationships)"),
        "layers": layers_out,
        "total_tables": total_tables,
        "waves": waves_out,
        "file_plan": files,
        "delegation": {
            "artifact_writer": total_tables > SUBAGENT_TABLE_THRESHOLD,
            "design_evaluator": True,
            "threshold": SUBAGENT_TABLE_THRESHOLD,
        },
        "validation_controls": [
            "verify_workbook_headers.py (template fidelity)",
            "verify_artifact_semantics.py (DQ SQL validity, ER Mermaid vs design, encoding)",
            "row-level References non-empty on populated detail rows",
            "STTM Filter/Join Conditions populated ('-' when n/a)",
            "stale-output safety: 05_artifacts must match plan.json#file_plan; stop-and-ask on unexpected files",
        ],
        "notes": [],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"plan.json written: {total_tables} tables, {len(waves_out)} waves, {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
