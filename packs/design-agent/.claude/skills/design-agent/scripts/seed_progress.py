#!/usr/bin/env python3
"""Seed the baseline progress.json for a new split-phase design run."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STEPS = [
    {"id": "start-design-run", "label": "Start design", "description": "Checks inputs and initializes the design run", "outcome": "produces the input readiness summary"},
    {"id": "discover-sources", "label": "Discover Sources", "description": "Confirms source systems, tables, and gaps", "outcome": "produces source decisions"},
    {"id": "design-architecture", "label": "Data Design", "description": "Maps business needs to target architecture", "outcome": "produces design and lineage decisions"},
    {"id": "plan-execution", "label": "Plan Generation", "description": "Sets output order and validation checks", "outcome": "produces generation plan"},
    {"id": "generate-artifacts", "label": "Generate Artifacts", "description": "Creates STTM, data model, DQ, and ERD outputs", "outcome": "produces artifact package"},
    {"id": "evaluate-design", "label": "Evaluate Design", "description": "Checks generated outputs before closeout", "outcome": "produces evaluation scores and findings"},
    {"id": "close-design-run", "label": "Close Run", "description": "Captures learnings and cleans scratch files", "outcome": "completes the run"},
]


def seed_progress(workspace: Path) -> Path:
    """Write the baseline progress.json with all split phases pending."""
    steps = [
        {**step, "status": "pending", "completed_at": None}
        for step in STEPS
    ]
    payload = {
        "schema_version": "progress-1.0",
        "updated_at": None,
        "selected_outputs": [],
        "current_step": None,
        "current_stage": None,
        "awaiting_user_action": None,
        "steps": steps,
        "next": {
            "command": "/start-design-run",
            "label": "Start design",
            "why": "Reviews inputs and confirms design readiness.",
        },
    }
    out = workspace / "progress.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="store_true", help="Write baseline progress.json to the workspace root.")
    args = parser.parse_args()
    if not args.seed:
        print("ERROR: this script only supports --seed; the agent writes progress.json inline.", file=sys.stderr)
        return 1
    out = seed_progress(Path.cwd())
    print(f"Wrote {out} (seed baseline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
