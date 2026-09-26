#!/usr/bin/env python3
"""
patch_session.py — Apply key/value patches to session.json atomically.

Usage:
    python patch_session.py <run_id> key=value [key=value ...]

    key supports dot-notation for nested fields: generation_summary.ddl_complete=true
    value types: true/false → bool, numeric strings → int/float, else str
    Special value "null" → None

Examples:
    python patch_session.py run_id_001 status=complete active_phase=package_build_complete
    python patch_session.py run_id_001 generation_summary.ddl_complete=true
    python patch_session.py run_id_001 evaluation_summary.overall_score=90.0 evaluation_summary.verdict=pass
    python patch_session.py run_id_001 updated_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)

Exit 0 on success.
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone


def coerce(val: str):
    if val == "true":  return True
    if val == "false": return False
    if val == "null":  return None
    try: return int(val)
    except ValueError: pass
    try: return float(val)
    except ValueError: pass
    return val


def set_nested(d: dict, dotpath: str, value) -> None:
    parts = dotpath.split(".")
    for part in parts[:-1]:
        if part not in d or not isinstance(d[part], dict):
            d[part] = {}
        d = d[part]
    d[parts[-1]] = value


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: patch_session.py <run_id> key=value [key=value ...]")
        return 1

    run_id = sys.argv[1]
    patches = sys.argv[2:]

    base = Path(__file__).resolve().parents[4]
    session_path = base / "state" / run_id / "session.json"

    if not session_path.exists():
        print(f"ERROR: {session_path} not found", file=sys.stderr)
        return 1

    with open(session_path) as f:
        session = json.load(f)

    # Always update updated_at
    session["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for patch in patches:
        if "=" not in patch:
            print(f"WARNING: skipping malformed patch '{patch}' (no '=')")
            continue
        key, _, val = patch.partition("=")
        set_nested(session, key.strip(), coerce(val.strip()))
        print(f"  patched {key} = {coerce(val.strip())}")

    with open(session_path, "w") as f:
        json.dump(session, f, indent=2)

    print(f"session.json updated at {session['updated_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
