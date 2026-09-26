# PROGRESS CONTRACT: `progress.json`

`progress.json` at the repo root is a UI projection for the Lockstep extension and dashboards. It is derived from `adlc/.state/run_state.json` and the gate records by `scripts/state.py`. Never edit it by hand.

## Schema (`progress-1.0`)

```json
{
  "schema_version": "progress-1.0",
  "run_id": "adlc-xxxxxxxx",
  "updated_at": "ISO timestamp",
  "run_status": "not_started | in_progress | waiting_for_user | cancelled | error | completed",
  "current_step": "architect-design",
  "awaiting_user_action": "gate_approval | clarification | blocker_resolution | cancel_confirmation | null",
  "steps": [
    {
      "id": "discover-define",
      "label": "01 Discover & Define",
      "status": "pending | running | done",
      "gate": { "id": "G1", "status": "not_requested | pending | approved | rejected | waived", "pull_request": "url | null" },
      "artifact": "adlc/01-aiprs.md",
      "completed_at": "ISO timestamp | null"
    }
  ],
  "next": { "command": "/architect-design", "why": "G1 is approved." }
}
```

## Mapping rules

- A step is `done` when its artifact is written and its gate requested; the gate status is shown separately.
- `next` is the first pending gate's approval, otherwise the first phase that is not done.
- When waiting on a human, `awaiting_user_action` names what they need to do; the extension shows it in the gate panel.

## Write points

Only at phase start, phase completion, a human wait, and cancellation.
