# RUN STATE MANAGEMENT

## Purpose

Each run has one durable state file:

```text
outputs/00_state/run_state.json
```

This is the internal control ledger and is the pointer for `/status`, `/cancel`, and normal continuation. Runs are single-tenant in this package's flat-outputs layout — there is no top-level `runs/` folder and no cross-run index file.

## Run ID and timestamp standard

Generate run IDs only after the empty-input guard passes.

Recommended run ID format:

```text
RUN_YYYYMMDD_HHMMSS_IST
```

If a collision occurs, append `_NNN`.

All timestamps written to `run_state.json`, human-decision logs, manifests, reports, and run indexes must be accurate IST timestamps in ISO-8601 format with the `+05:30` offset, for example:

```text
2026-05-19T19:45:23+05:30
```

Do not use naive timestamps, UTC `Z` timestamps, or host-local timestamps without an offset. When generating timestamps in Python, use an explicit IST timezone, for example:

```python
from datetime import datetime, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))
now_ist = datetime.now(IST).isoformat(timespec="seconds")
```

## Required update points

Update `outputs/00_state/run_state.json` (and rewrite the run-root `progress.json` projection with it) **at most twice per phase** in the normal flow (CLAUDE.md principle 14):

1. **Phase start** — one write as the phase begins (for /start-design: after the empty-input guard passes and before file snapshot begins).
2. **Phase completion** — one write as the phase ends. Human-wait status for an in-phase question asked at the boundary (such as the evaluate-design closure reference-store inclusion) is folded into this write; the human's answer is recorded in the next write. The phase-completion write is MANDATORY before the phase's final chat reply.

Exceptional events get additional event-driven writes (outside the twice-per-phase budget) because recoverability depends on them:

- Whenever feedback is routed to an earlier stage.
- Whenever an error blocks progress.
- Whenever `/cancel` cancels a run.
- At final terminal completion, including successful completion, cancellation, or unrecoverable error (normally this coincides with the evaluate-design phase-completion write, whose closure tail marks the run completed).

Also update `outputs/00_state/run_state.json` whenever a run is created or reaches a terminal state.

## Project to `progress.json` (UI projection)

`run_state.json` is the internal control ledger. The playground UI reads a separate lean
`progress.json` at the run-root (seeded by the playground at run creation, or by standalone
`scripts/seed_progress.py --seed --run-id <active_run_id>` if missing). **Whenever you
update `run_state.json` (phase start, phase completion, or an exceptional event), also
rewrite `progress.json`** as its UI projection per `utilities/progress-contract.md`:

- mark the matching UI step `done` / `running` / `pending`, set `current_step` + `current_stage`;
- copy `awaiting_user_action` and set `blocker` when `run_status = waiting_for_user`, else null;
- set `next` to the recommended next slash command (`/status` when terminal, `null` only while a genuine in-phase human question is pending);
- stamp `updated_at`.

`progress.json` is **derived from** `run_state.json` — never a second source of truth. The
backend reads only `progress.json` (it never reads `run_state.json`); keep them consistent.
After stage-final user-facing artifacts are written in standalone mode, run
`scripts/publish_outputs.py --run-id <active_run_id>` so `outputs/` stays aligned
with `workspace_layout.yaml`.

## Status values

Use only these `run_status` values:

```text
not_started
in_progress
waiting_for_user
changes_requested
rerun_required
completed
cancelled
error
```

For compatibility with older instructions, if a file has `status`, keep it synchronized with `run_status`.

## Stage status values

```text
not_started
in_progress
completed
blocked
rerun_required
skipped
error
```

## Waiting action values

Use explicit `awaiting_user_action` values so `/status` can explain what is needed:

```text
stale_input_confirmation
input_clarification
reference_store_decision
cancel_confirmation
unexpected_output_decision
execution_blocker_decision
error_retry_decision
```

## Minimum schema

```json
{
  "schema_version": "4.7",
  "run_id": "RUN_YYYYMMDD_HHMMSS_IST",
  "created_at": "2026-05-19T19:45:23+05:30",
  "updated_at": "2026-05-19T19:45:23+05:30",
  "run_status": "in_progress",
  "status": "in_progress",
  "current_stage": "start-design",
  "current_blocker": null,
  "awaiting_user_action": null,
  "paths": {
    "inputs_root": "inputs/",
    "outputs_root": "outputs/",
    "active_output_root": "outputs/",
    "active_run_root": "outputs/00_state/",
    "input_snapshot": "outputs/00_state/input_snapshot/",
    "context_snapshot": "outputs/00_state/context_snapshot/guidance/",
    "run_state": "outputs/00_state/run_state.json",
    "runtime_scratch": "outputs/00_state/runtime_scratch/",
    "validation_log": "outputs/00_state/validation_log.json",
    "evidence_registry": "outputs/00_state/traceability/evidence_registry.json"
  },
  "run_context": {
    "enterprise_name": null,
    "domain_name": null,
    "client_name": null,
    "project_name": null,
    "target_platform": null
  },
  "stages": {
    "start-design": {"status": "not_started", "started_at": null, "completed_at": null, "summary": null},
    "design-architecture": {"status": "not_started", "started_at": null, "completed_at": null, "summary": null},
    "generate-artifacts": {"status": "not_started", "started_at": null, "completed_at": null, "summary": null},
    "evaluate-design": {"status": "not_started", "started_at": null, "completed_at": null, "summary": null}
  },
  "stage_history": [],
  "human_decision_history": [],
  "user_instructions": {
    "file_present": false,
    "source_files": [],
    "total_directives": 0,
    "pending": 0,
    "applied": 0,
    "deferred_with_confirmation": 0,
    "rejected_with_confirmation": 0,
    "unaddressed": 0
  },
  "context_overrides": {
    "user_overrides_project": 0,
    "user_overrides_domain": 0,
    "user_overrides_enterprise": 0,
    "project_overrides_domain": 0,
    "project_overrides_enterprise": 0,
    "domain_overrides_enterprise": 0,
    "all_overrides_confirmed": true
  },
  "metrics": {
    "layers_identified": [],
    "tables_per_layer": {},
    "total_human_interactions": 0,
    "overall_confidence": null,
    "past_learnings_loaded": {
      "agent": 0,
      "input_set": 0,
      "human": 0
    }
  },
  "risk_manifest_path": null,
  "last_error": null
}
```

## Stage update contract

At stage start:

```json
{
  "run_status": "in_progress",
  "status": "in_progress",
  "current_stage": "{stage_name}",
  "stages.{stage_name}.status": "in_progress",
  "stages.{stage_name}.started_at": "IST ISO timestamp",
  "updated_at": "IST ISO timestamp"
}
```

`{stage_name}` must be one of `start-design`, `design-architecture`, `generate-artifacts`, or `evaluate-design` (the evaluate stage's closure tail also captures learnings, resolves the reference-store decision, and marks the run completed — there is no separate close stage).

At stage completion:

```json
{
  "stages.{stage_name}.status": "completed",
  "stages.{stage_name}.completed_at": "IST ISO timestamp",
  "stages.{stage_name}.summary": "short summary",
  "stage_history += event",
  "updated_at": "IST ISO timestamp"
}
```

There is no approval step between phases: the phase-completion write is followed by the concise summary and the recommended next slash command, and the run waits for the user to invoke it.

When presenting any in-phase human decision point:

```json
{
  "run_status": "waiting_for_user",
  "status": "waiting_for_user",
  "current_stage": "{stage_name}",
  "awaiting_user_action": "specific_action_value",
  "updated_at": "IST ISO timestamp"
}
```

## User-instruction counter synchronization

Whenever `outputs/00_state/standard_input_set/user_instructions.json` directive statuses change, update both:

1. `outputs/00_state/standard_input_set/user_instructions.json` counters.
2. `outputs/00_state/run_state.json.user_instructions` counters.

/evaluate-design treats any remaining `unaddressed` directive as a critical failure.

## Atomic update discipline

When dynamically generating Python or shell helpers, update `run_state.json` atomically:

1. Read existing JSON if present.
2. Merge new fields without discarding existing history.
3. Write to `outputs/00_state/run_state.json.tmp`.
4. Validate the temp file as JSON.
5. Rename temp file to `outputs/00_state/run_state.json`.

Do not rewrite run state from scratch after /start-design unless rebuilding a corrupt state file with a clear error log.

## Terminal state: no cleanup

When a run reaches a terminal state (`completed`, `cancelled`, or unrecoverable `error`), nothing is deleted. `inputs/`, `outputs/00_state/` (including `runtime_scratch/`), and `outputs/` are all preserved (owner decision, consistent with the other agents). The terminal write updates `run_state.json`, `outputs/00_state/run_state.json`, and the run-root `progress.json` only.
