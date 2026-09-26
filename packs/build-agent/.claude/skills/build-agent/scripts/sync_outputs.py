#!/usr/bin/env python3
"""
sync_outputs.py — Mirror user-facing build artifacts from state/ to outputs/ for a run.

outputs/ is the ONLY thing the UI shows the user, so it is laid out as an ordered,
"read it one by one" tree with numbered phase folders:

    outputs/<run_id>/
      01_input_evaluation/  input_evaluation_report.md
      02_analysis/          canonical_build_model.json, effective_conventions.json,
                            relationships.json, dq_catalog.json, source_column_registry.json,
                            derivation_catalog.json, semantic_checks.json,
                            lineage.json, build_blueprint.json, table_index.json
      03_generated/         ddl/ dml/ dq/ pipeline/ tests_data/ tests_pipeline/
      04_evaluation/        <evaluation report + scores>
      logs.md

Internal machinery is NEVER synced — it stays in state/<run_id>/: session.json,
phase_handoff.json, progress.json, per-table *_plan.json, plan_handoff_summary.json,
generated/_validation/prevalidation_*.json, scratch/.

Usage:
    python sync_outputs.py <run_id> [--families ddl dml dq pipeline tests_data tests_pipeline]

If --families is omitted, all generated families are synced into 03_generated/.

Exit 0 on success. Exit 1 if state/<run_id>/ is missing.
"""
import sys
import shutil
from pathlib import Path

GENERATED_FAMILIES = ["ddl", "dml", "dq", "pipeline", "tests_data", "tests_pipeline"]

# discovery/<file> → 02_analysis/  (user-facing analysis JSONs; per-table plans excluded)
ANALYSIS_DISCOVERY = [
    "canonical_build_model.json", "effective_conventions.json", "relationships.json",
    "dq_catalog.json", "source_column_registry.json", "derivation_catalog.json",
    "semantic_checks.json",
]
# plans/<file> → 02_analysis/  (graph-level only; the 30 *_plan.json stay internal)
ANALYSIS_PLANS = ["lineage.json", "build_blueprint.json", "table_index.json"]


def package_root() -> Path:
    here = Path(__file__).resolve()
    candidate = here.parents[4]
    if (candidate / "state").is_dir() or (candidate / "outputs").is_dir():
        return candidate
    cwd = Path.cwd()
    for path in (cwd, *cwd.parents):
        if (path / "state").is_dir() and (path / "outputs").is_dir():
            return path
    return candidate


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sync(run_id: str, families: list[str]) -> int:
    root = package_root()
    state_root = root / "state" / run_id
    out_root = root / "outputs" / run_id

    if not state_root.exists():
        print(f"ERROR: state/{run_id}/ not found under {root}", file=sys.stderr)
        return 1

    synced: list[str] = []

    # 01_input_evaluation/
    ie = state_root / "discovery" / "input_evaluation_report.md"
    if ie.is_file():
        copy_file(ie, out_root / "01_input_evaluation" / ie.name)
        synced.append("01_input_evaluation/input_evaluation_report.md")

    # 02_analysis/
    n = 0
    for name in ANALYSIS_DISCOVERY:
        src = state_root / "discovery" / name
        if src.is_file():
            copy_file(src, out_root / "02_analysis" / name); n += 1
    for name in ANALYSIS_PLANS:
        src = state_root / "plans" / name
        if src.is_file():
            copy_file(src, out_root / "02_analysis" / name); n += 1
    if n:
        synced.append(f"02_analysis/ ({n} files)")

    # 03_generated/<family>/
    for fam in families:
        src = state_root / "generated" / fam
        if src.is_dir():
            count = 0
            for f in src.iterdir():
                if f.is_file():
                    copy_file(f, out_root / "03_generated" / fam / f.name); count += 1
            if count:
                synced.append(f"03_generated/{fam}/ ({count} files)")

    # 04_evaluation/
    ev = state_root / "evaluation"
    if ev.is_dir():
        count = 0
        for f in ev.iterdir():
            if f.is_file():
                copy_file(f, out_root / "04_evaluation" / f.name); count += 1
        if count:
            synced.append(f"04_evaluation/ ({count} files)")

    # logs.md (root)
    logs = state_root / "logs" / "logs.md"
    if logs.is_file():
        copy_file(logs, out_root / "logs.md")
        synced.append("logs.md")

    if not synced:
        print(f"WARNING: nothing to sync for {run_id}", file=sys.stderr)
    else:
        print(f"Synced state/{run_id}/ -> outputs/{run_id}/")
        for line in synced:
            print(f"  {line}")

    # Refresh the UI progress file (best-effort — never fail the sync over it).
    # progress.json is derived from session.json, which the calling skill has just
    # updated, so every phase-boundary sync keeps "done / current / next" current.
    try:
        from update_progress import write_progress
        if write_progress(root, run_id) is not None:
            print("  progress.json (refreshed)")
    except Exception as exc:  # noqa: BLE001 - progress is non-critical
        print(f"  (progress.json refresh skipped: {exc})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sync_outputs.py <run_id> [--families ddl dml ...]")
        sys.exit(1)
    run_id = sys.argv[1]
    if "--families" in sys.argv:
        idx = sys.argv.index("--families")
        fams = sys.argv[idx + 1:]
    else:
        fams = GENERATED_FAMILIES
    sys.exit(sync(run_id, fams))
