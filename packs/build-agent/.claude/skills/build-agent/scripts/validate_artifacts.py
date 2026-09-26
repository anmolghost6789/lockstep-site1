#!/usr/bin/env python3
"""
validate_artifacts.py — Check that all expected artifact files exist and are non-empty.

Usage:
    python validate_artifacts.py <run_id> <family> <expected_count>

    family: ddl | dml | dq | pipeline | tests_data | tests_pipeline

Exits 0 if count matches and no zero-byte files.
Exits 1 with details if mismatch or zero-byte files found.

Also supports a full-run check:
    python validate_artifacts.py <run_id> --all

which checks all families against session.json generation_summary counts.
"""
import sys
import json
from pathlib import Path

FAMILY_SUBDIR = {
    "ddl": "generated/ddl",
    "dml": "generated/dml",
    "dq": "generated/dq",
    "pipeline": "generated/pipeline",
    "tests_data": "generated/tests_data",
    "tests_pipeline": "generated/tests_pipeline",
}

SESSION_KEY_MAP = {
    "ddl": "ddl_tables",
    "dml": "dml_tables",
    "dq": "dq_tables",
    "pipeline": None,           # pipeline uses file count = 4 (Snowflake) or wave+2
    "tests_data": "tests_data_tables",
    "tests_pipeline": None,     # always 1 file
}


def check_family(state_root: Path, family: str, expected: int) -> list[str]:
    """Return list of error strings. Empty = pass."""
    errors = []
    d = state_root / FAMILY_SUBDIR[family]
    if not d.exists():
        errors.append(f"{family}: directory {d} does not exist")
        return errors

    files = [f for f in d.iterdir() if f.is_file()]
    actual = len(files)

    if actual != expected:
        errors.append(f"{family}: expected {expected} files, found {actual}")

    zero_byte = [f.name for f in files if f.stat().st_size == 0]
    if zero_byte:
        errors.append(f"{family}: zero-byte files: {zero_byte}")

    if not errors:
        print(f"  {family}: {actual}/{expected} files OK")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate_artifacts.py <run_id> <family> <expected_count>")
        print("       validate_artifacts.py <run_id> --all")
        return 1

    run_id = sys.argv[1]
    base = Path(__file__).resolve().parents[4]
    state_root = base / "state" / run_id

    if not state_root.exists():
        print(f"ERROR: state/{run_id}/ not found", file=sys.stderr)
        return 1

    all_errors = []

    if len(sys.argv) == 3 and sys.argv[2] == "--all":
        # Read expected counts from session.json
        session_path = state_root / "session.json"
        if not session_path.exists():
            print("ERROR: session.json not found", file=sys.stderr)
            return 1
        with open(session_path) as f:
            session = json.load(f)
        gen = session.get("generation_summary", {})

        checks = [
            ("ddl",          gen.get("ddl_tables", 0)),
            ("dml",          gen.get("dml_tables", 0)),
            ("dq",           gen.get("dq_tables", 0)),
            ("tests_data",   gen.get("tests_data_tables", 0)),
        ]
        # Pipeline and tests_pipeline: just check directory is non-empty
        for fam in ("pipeline", "tests_pipeline"):
            d = state_root / FAMILY_SUBDIR[fam]
            if d.exists():
                count = sum(1 for f in d.iterdir() if f.is_file())
                if count == 0:
                    all_errors.append(f"{fam}: directory exists but is empty")
                else:
                    print(f"  {fam}: {count} files OK")

        for family, expected in checks:
            all_errors.extend(check_family(state_root, family, expected))

    else:
        if len(sys.argv) != 4:
            print("Usage: validate_artifacts.py <run_id> <family> <expected_count>")
            return 1
        family = sys.argv[2]
        expected = int(sys.argv[3])
        all_errors.extend(check_family(state_root, family, expected))

    if all_errors:
        for e in all_errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("All artifact checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
