# RUN STATE MANAGEMENT

## One ledger

`adlc/.state/run_state.json` is the single source of truth for where a run is. It is written only by `scripts/state.py`, at most twice per phase plus human waits.

```json
{
  "schema_version": "adlc-state-1.0",
  "run_id": "adlc-xxxxxxxx",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "run_status": "not_started | in_progress | waiting_for_user | cancelled | error | completed",
  "current_phase": "build-orchestrate",
  "awaiting_user_action": "gate_approval | clarification | blocker_resolution | cancel_confirmation | null",
  "phases": {
    "build-orchestrate": { "status": "running", "started_at": "…", "completed_at": null }
  }
}
```

## Transitions

| From | Event | To |
|---|---|---|
| not_started | a phase starts | in_progress |
| in_progress | a question or gate needs a human | waiting_for_user |
| waiting_for_user | the human answers, or the gate is approved and the next phase starts | in_progress |
| any | /cancel confirmed | cancelled |
| in_progress | an unrecoverable error | error |
| in_progress | G6 approved | completed |

## One active phase

Only one phase may be `running`. If a phase is found `running` at start (for example after a crash), treat it as interrupted: resume using the phase's idempotent re-entry rules rather than starting over.

## Interrupted runs

On network errors, timeouts or restarts, nothing is lost that was written to disk. Run `/status`, then re-invoke the phase; re-entry skips completed work.

## Cancelled runs

Cancellation preserves every artifact, gate record and the audit log. A new intent starts a new run ID.
