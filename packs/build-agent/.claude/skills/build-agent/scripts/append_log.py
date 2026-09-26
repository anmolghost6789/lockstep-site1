#!/usr/bin/env python3
"""
append_log.py — Append a phase timing section to logs/logs.md.

Usage:
    python append_log.py <run_id> <phase_name> <start_utc> <end_utc> \
        --steps "label|start|end" "label|start|end" ...

    Times must be HH:MM:SS UTC format.
    phase_name: the /command name, e.g. "generate-build"

Example:
    python append_log.py run_id_001 generate-build 12:06:26 12:45:05 \
        --steps \
        "Step 1: prep|12:06:26|12:07:30" \
        "Step 2 DDL: 4 waves parallel|12:07:30|12:13:31"

Calculates duration for each step automatically.
Appends (never overwrites) to logs.md.
"""
import sys
from pathlib import Path
from datetime import datetime


def hms_to_sec(t: str) -> int:
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def sec_to_dur(s: int) -> str:
    m, sec = divmod(s, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h {m}m {sec:02d}s"
    return f"{m}m {sec:02d}s"


def parse_steps(raw: list[str]) -> list[tuple[str, str, str, str]]:
    """Returns list of (label, start, end, duration)."""
    result = []
    for item in raw:
        parts = item.split("|")
        if len(parts) != 3:
            print(f"WARNING: skipping malformed step '{item}'")
            continue
        label, start, end = parts
        dur = sec_to_dur(hms_to_sec(end) - hms_to_sec(start))
        result.append((label.strip(), start.strip(), end.strip(), dur))
    return result


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: append_log.py <run_id> <phase_name> <start_utc> <end_utc> [--steps ...]")
        return 1

    run_id      = sys.argv[1]
    phase_name  = sys.argv[2]
    start_utc   = sys.argv[3]
    end_utc     = sys.argv[4] if len(sys.argv) > 4 else start_utc
    steps: list[str] = []

    if "--steps" in sys.argv:
        idx = sys.argv.index("--steps")
        steps = sys.argv[idx + 1:]

    base = Path(__file__).resolve().parents[4]
    log_path = base / "state" / run_id / "logs" / "logs.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    total_dur = sec_to_dur(hms_to_sec(end_utc) - hms_to_sec(start_utc))
    parsed_steps = parse_steps(steps)

    # Build section
    lines = [
        f"\n## /{phase_name}",
        f"*Started: 2026-05-04T{start_utc}Z*\n",
        "| Step | Start (UTC) | End (UTC) | Duration |",
        "|------|-------------|-----------|----------|",
    ]
    for label, s, e, dur in parsed_steps:
        lines.append(f"| {label} | {s} | {e} | {dur} |")
    lines.append(f"| **Phase total** | **{start_utc}** | **{end_utc}** | **{total_dur}** |")

    section = "\n".join(lines) + "\n"

    # Read existing content (create if absent)
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8")
    else:
        existing = f"# Run Log — {run_id}\n"

    log_path.write_text(existing + section, encoding="utf-8")
    print(f"Appended /{phase_name} section to {log_path} ({total_dur})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
