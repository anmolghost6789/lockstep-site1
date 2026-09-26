# Progress Contract — `progress.json` (UI projection)

`outputs/00_state/run_state.json` stays your **internal control ledger** (stages,
`awaiting_user_action`, rerun routing, resumability). In addition, you maintain a lean
`progress.json` at the **run root** (the playground run dir, i.e. your `cwd`'s run root) as
the **UI projection** the playground reads. The backend seeds the baseline once at run
creation and is a GENERIC `progress.json` reader — it never reads `run_state.json`.

Write `progress.json` at the same boundaries where you update `run_state.json`: **at most
twice per phase** — once at phase start and once at phase completion (fold human-wait
status into those two writes; see CLAUDE.md principle 14). The phase-completion rewrite is
mandatory before the phase's final reply. It is a small projection of `run_state.json`,
never a second source of truth — derive it from `run_state.json`. (The per-table telemetry
appends during `/design-architecture` are the documented exception and do not count as
bookkeeping rewrites.)

> Note on location: in the playground, the backend run dir is the `cwd`, and the seeded
> `progress.json` sits at its root. When you also keep an inner `outputs/00_state/` workspace,
> write `progress.json` to the run-dir root the backend seeded (the same file), not inside
> `outputs/00_state/`.
> Preserve the seeded `run_id` value in app mode. In standalone Claude Code mode, if no
> backend created the file, seed it once from the package root with
> `seed_progress.py --seed --run-id <active_run_id>`.

## Schema (`progress-1.0`)

```json
{
  "schema_version": "progress-1.0",
  "run_id": "<run_id>",
  "updated_at": "<ISO8601, the time you write this>",
  "selected_outputs": [],
  "current_step": "<id of the running/last-done UI step, or null>",
  "current_stage": "<run_state.current_stage, or null>",
  "awaiting_user_action": "<run_state.awaiting_user_action, or null>",
  "blocker": null,
  "steps": [
    {"id": "start-design",        "label": "Start Design",         "description": "Ingests inputs, assesses readiness, and decides sources",           "status": "done",    "completed_at": "<ISO8601>"},
    {"id": "design-architecture", "label": "Design Architecture",  "description": "Maps business needs to target architecture and computes the plan",  "status": "running", "completed_at": null},
    {"id": "generate-artifacts",  "label": "Generate Artifacts",   "description": "Creates STTM, data model, DQ, and ERD outputs",                      "status": "pending", "completed_at": null},
    {"id": "evaluate-design",     "label": "Evaluate & Close",     "description": "Checks outputs, captures learnings, closes the run",                 "status": "pending", "completed_at": null}
  ],
  "next": {"command": "/generate-artifacts", "label": "Generate Artifacts", "why": "Generate the planned workbooks from the approved design."}
}
```

Keep all four steps present in every write. `selected_outputs` stays `[]` (design's outputs
STTM/DATA_MODEL/DQ/ERD are always produced; they're not user-selected).

## Mapping `run_state.json` → `progress.json`

**Steps** — the four UI steps map one-to-one onto the four phase skills:

- The phase currently executing is `running`; completed phases are `done` (with
  `completed_at`); later phases are `pending`.
- `current_step` = the `running` step's id, or the last `done` step id if none is running.
- `current_stage` = `run_state.current_stage` verbatim.

**Awaiting a human decision** — when `run_state.run_status` is `waiting_for_user` (an
in-phase question such as the stale-input confirmation, the start-design error-grade
readiness pause, a blocker decision, or the evaluate-design reference-store inclusion),
set `awaiting_user_action` to the same enum value and set `blocker` so the UI shows a card:

```json
"blocker": {"code": "<awaiting_user_action>", "label": "<Title Cased>", "description": "Waiting for your decision before the workflow can continue."}
```

When not waiting, `awaiting_user_action` is `null` and `blocker` is `null`.

**`next`** — every phase stops at its boundary; the user invoking the next command is the
approval to proceed:

- Before the run exists / at seed: `{"command": "/start-design", "label": "Start Design", "why": "Reviews inputs, confirms design readiness, and decides sources."}`.
- At each phase completion: the next phase's slash command (`/design-architecture`,
  `/generate-artifacts`, `/evaluate-design`).
- While a genuine in-phase human question is pending (`blocker` set): `null` — the blocker
  card conveys the wait.
- Terminal (`completed`/`cancelled`/`error`): `{"command": "/status", "label": "Show status", "why": "Inspect the final run state."}`.

`updated_at` = now (ISO-8601). Always derive from `run_state.json` so the two never disagree.

> **Contract alignment:** The step `id` values in this file are contractually
> identical to the phase `id` values in `playground/backend/agents/design/profile.py` and
> to `scripts/seed_progress.py`. Never change a step `id` here without also updating both.
