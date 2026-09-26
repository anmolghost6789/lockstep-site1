#!/usr/bin/env python3
"""Seed or project the Requirements Agent's run-root progress.json.

The playground calls ``--seed`` at run creation. Phase skills call
``--from-state`` after updating ``outputs/00_state/state.json``. ``--recover``
clears stale running UI status after an interrupted turn.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any


PRE_STEPS = [
    {"id": "start", "command": "/start-run", "label": "Start Run"},
    {"id": "extract", "command": "/extract-requirements", "label": "Extract Requirements"},
]
POST_STEPS = [
    {"id": "evaluate", "command": "/evaluate-run", "label": "Evaluate Run"},
    {"id": "publish", "command": "/publish-to-jira", "label": "Publish to Jira"},
]
WHY = {
    "extract": "Normalize accepted source knowledge into linked requirement topics.",
    "evaluate": "Score the selected final deliverables before handoff or publication.",
    "publish": "Publish the approved Jira Story Pack.",
}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def workflow_manifest() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "workflow_manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def deliverable_steps(workflow: dict[str, Any]) -> list[dict[str, str]]:
    outputs = {
        str(item.get("id")): item
        for item in (workflow.get("outputs") or [])
        if isinstance(item, dict) and item.get("id")
    }
    order = workflow.get("generationOrder") or list(outputs)
    result: list[dict[str, str]] = []
    for code in order:
        output = outputs.get(str(code))
        if not output:
            continue
        result.append(
            {
                "id": str(code).lower(),
                "code": str(code),
                "command": str(output.get("command") or f"/generate-{str(code).lower()}"),
                "label": f"Generate {output.get('label') or code}",
            }
        )
    return result


def is_done(
    step: dict[str, str],
    state: dict[str, Any],
    artifact_exists: dict[str, bool] | None = None,
) -> bool:
    step_id = step["id"]
    if step_id == "start":
        return (state.get("phases", {}).get("start") or {}).get("status") == "complete"
    if step_id == "extract":
        return (state.get("extraction") or {}).get("status") == "complete"
    if step_id == "evaluate":
        return (state.get("evaluation") or {}).get("status") == "complete"
    if step_id == "publish":
        publication = state.get("publication") or {}
        return publication.get("status") == "published"
    code = step.get("code")
    if not code:
        return False
    committed = (state.get("generation_summary", {}).get(code) or {}).get("status") == "complete"
    return committed and (artifact_exists is None or artifact_exists.get(code, False))


def build_progress(
    state: dict[str, Any],
    workflow: dict[str, Any],
    completed: str | None,
    at: str | None,
    running: str | Iterable[str] | None = None,
    next_command: str | None = None,
    next_why: str | None = None,
    artifact_exists: dict[str, bool] | None = None,
) -> dict[str, Any]:
    selected = [str(value) for value in (state.get("selected_outputs") or [])]
    selected_set = set(selected)
    running_ids = {running} if isinstance(running, str) else {str(value) for value in (running or [])}
    canonical = [*PRE_STEPS, *deliverable_steps(workflow), *POST_STEPS]
    steps: list[dict[str, Any]] = []
    for step in canonical:
        code = step.get("code")
        skipped = bool(code and selected and code not in selected_set)
        if step["id"] == "publish" and "JIRA" not in selected_set:
            skipped = True
        if step["id"] in running_ids:
            status = "running"
        elif skipped:
            status = "skipped"
        elif is_done(step, state, artifact_exists):
            status = "done"
        else:
            status = "pending"
        steps.append(
            {
                "id": step["id"],
                "label": step["label"],
                "command": step["command"],
                "status": status,
                "completed_at": at if step["id"] == completed and status == "done" else None,
            }
        )

    done = [step["id"] for step in steps if step["status"] == "done"]
    active = [step["id"] for step in steps if step["status"] == "running"]
    current = active[0] if active else (completed if completed else (done[-1] if done else None))
    pending = next((step for step in steps if step["status"] == "pending"), None)
    recommendation = None
    if not active:
        command = next_command or (pending or {}).get("command")
        if command:
            source = next((step for step in canonical if step["command"] == command), None)
            label = (source or {}).get("label") or command.lstrip("/").replace("-", " ").title()
            step_id = (source or {}).get("id")
            recommendation = {
                "command": command,
                "label": label,
                "why": next_why or WHY.get(step_id) or f"{label} is the recommended next step.",
            }
    return {
        "schema_version": "progress-1.0",
        "updated_at": at,
        "selected_outputs": selected,
        "current_step": current,
        "steps": steps,
        "next": recommendation,
    }


def _load_state(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "outputs" / "00_state" / "state.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def update_from_state(
    run_dir: Path,
    completed: str | None,
    running: str | Iterable[str] | None = None,
    next_command: str | None = None,
    next_why: str | None = None,
    preserve_existing_next: bool = False,
) -> Path:
    state = _load_state(run_dir)
    workflow = workflow_manifest()
    now = _now()
    path = run_dir / "progress.json"
    prior_payload: dict[str, Any] = {}
    if path.is_file():
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            prior_payload = value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
    prior_next = prior_payload.get("next")
    if preserve_existing_next and not next_command and isinstance(prior_next, dict):
        next_command = str(prior_next.get("command") or "") or None
        next_why = str(prior_next.get("why") or "") or next_why
    artifact_exists = {
        str(output.get("id")): bool(
            output.get("outputPath")
            and (run_dir / str(output["outputPath"])).is_file()
            and (run_dir / str(output["outputPath"])).stat().st_size > 0
        )
        for output in (workflow.get("outputs") or [])
    }
    payload = build_progress(
        state,
        workflow,
        completed,
        now,
        running=running,
        next_command=next_command,
        next_why=next_why,
        artifact_exists=artifact_exists,
    )
    prior: dict[str, str | None] = {}
    prior = {
        step.get("id"): step.get("completed_at")
        for step in prior_payload.get("steps", [])
        if isinstance(step, dict)
    }
    for step in payload["steps"]:
        if step["status"] == "done" and not step["completed_at"]:
            step["completed_at"] = prior.get(step["id"]) or now
    _write(path, payload)
    return path


def seed_progress(run_dir: Path) -> Path:
    path = run_dir / "progress.json"
    _write(path, build_progress({}, workflow_manifest(), None, None))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--seed", action="store_true")
    modes.add_argument("--from-state", action="store_true")
    modes.add_argument("--recover", action="store_true")
    lifecycle = parser.add_mutually_exclusive_group()
    lifecycle.add_argument("--completed")
    lifecycle.add_argument("--running", action="append")
    parser.add_argument("--next")
    parser.add_argument("--next-command-name")
    parser.add_argument("--next-why")
    parser.add_argument("--run-dir", default=".")
    args = parser.parse_args()
    if args.next and args.next_command_name:
        parser.error("pass only one of --next or --next-command-name")
    next_command = args.next
    if args.next_command_name:
        token = args.next_command_name.strip().lstrip("/")
        if not token or any(char.isspace() for char in token):
            parser.error("--next-command-name must be one command token")
        next_command = f"/{token}"
    run_dir = Path(args.run_dir).resolve()
    if args.seed:
        output = seed_progress(run_dir)
        print(f"Wrote {output} (seed baseline)")
        return 0
    if args.recover and (args.completed or args.running or next_command):
        parser.error("--recover does not accept lifecycle or next-step overrides")
    output = update_from_state(
        run_dir,
        completed=None if args.recover else args.completed,
        running=None if args.recover else args.running,
        next_command=next_command,
        next_why=args.next_why,
        preserve_existing_next=args.recover,
    )
    print(f"Wrote {output} (from state)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
