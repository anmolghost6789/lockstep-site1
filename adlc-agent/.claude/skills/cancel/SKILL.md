---
name: cancel
description: "Cancel the current ADLC run, preserving artifacts, gate records and the audit log. User-invoked only."
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Read
  - Bash(python3 .claude/skills/adlc/scripts/*:*)
---

# /cancel

1. Read `adlc/.state/run_state.json`. If there is no active run, say so and stop.
2. `state.py wait --phase <current> --action cancel_confirmation`, then ask with `AskUserQuestion`: **Cancel run** · **Keep going**, with a plain-text fallback.
3. On confirmation: `state.py cancel --reason "<user's reason>"`. Artifacts, `adlc/.gates/` and `adlc/.audit/` are never deleted; audit retention is governed by `config/project_config.json > audit.retention_days`.
4. Confirm what was preserved and how to start again (`/discover-define`).
