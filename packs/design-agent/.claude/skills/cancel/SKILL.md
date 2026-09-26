---
name: cancel
description: "Cancel the active run after confirmation while preserving run artifacts and output files. User-invoked only."
argument-hint: "[optional reason]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Grep
  - Glob
  - Bash(cat:*)
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(grep:*)
  - Bash(mkdir:*)
  - Bash(cp:*)
  - Bash(mv:*)
  - Bash(rm:*)
  - Bash(python3:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# /cancel

Terminate the current run while preserving the `outputs/` tree (deliverables and agent state under `outputs/00_state/`).

1. Read `outputs/00_state/run_state.json` to load the active run state.
2. Before asking, update `outputs/00_state/run_state.json` to `run_status = "waiting_for_user"`, compatibility `status = "waiting_for_user"`, `awaiting_user_action = "cancel_confirmation"`, and refresh `updated_at` with an IST `+05:30` timestamp.
3. Ask for confirmation using `AskUserQuestion` as the primary UI:

```json
{
  "questions": [
    {
      "question": "Cancel this run? Outputs and agent state will be preserved, but input files will be cleared after cancellation.",
      "header": "Cancel",
      "options": [
        { "label": "YES", "description": "Cancel this run and clear user-provided files from inputs/ while preserving README.md files." },
        { "label": "NO", "description": "Keep the run active and return to the current stage or gate." }
      ],
      "multiSelect": false
    }
  ]
}
```

If `AskUserQuestion` is unavailable, present this yellow fallback outside code fences:

```text
🟨 CANCEL CONFIRMATION

Current progress: {stage_name}
Outputs and agent state will remain: outputs/
Input files will be cleared from inputs/ except README.md files if cancellation is confirmed.

Type one option:
1. YES
2. NO
```

4. If confirmed:
   - Set `outputs/00_state/run_state.json` fields `run_status` and compatibility `status` to `cancelled`, set `awaiting_user_action = null`, record IST timestamp/reason, and append a stage-history/state event.
   - Clear actual user-provided files from `inputs/` while preserving every `README.md` file and the input category folder scaffold. Remove `inputs/midrun_uploads/` if present.
   - Write `outputs/00_state/logs/input_cleanup_report.json`.
   - Report: `Run cancelled. Outputs and agent state preserved under outputs/. Input files were cleared from inputs/ except README.md files.`
5. If not confirmed:
   - Restore the prior `run_status`, compatibility `status`, `current_stage`, `current_gate`, and `awaiting_user_action` from the run state snapshot taken before the confirmation prompt.
   - Continue normal workflow from the current stage/gate recorded in `outputs/00_state/run_state.json`.

Cancellation reason/context: $ARGUMENTS
