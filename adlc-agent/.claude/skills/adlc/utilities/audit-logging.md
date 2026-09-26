# Audit Logging

`adlc/.audit/audit.jsonl` is append-only and hash-chained. Each entry stores the previous entry's hash, so removing, editing or reordering any entry breaks the chain, and `audit_log.py verify` reports where.

## Events

| Event | Written by |
|---|---|
| phase.started, phase.completed, run.cancelled | state.py |
| gate.requested, gate.approval_recorded, gate.approved, gate.rejected, gate.denied, gate.waived | adlc_gate.py |
| policy.checked | policy_check.py |
| policy.blocked | pre_tool_guard.py |
| artifact.modified | post_tool_audit.py |

## Entry shape

`{seq, ts, event, phase, gate, actor, data, prev_hash, hash}`, with `ts` in ISO-8601 `+05:30`.

## For auditors

- Export: `audit_log.py export --format csv`.
- Integrity: `audit_log.py verify`.
- For stronger guarantees, ship the log to your SIEM or WORM storage on every commit, and anchor the latest hash in a signed git tag at each release.
