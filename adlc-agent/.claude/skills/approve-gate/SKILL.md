---
name: approve-gate
description: "Local gate mode only: record a human decision on an ADLC gate (approve, reject with reason, or waive). In github mode, gates are approved in the pull request review instead. Must be run by the approver in their own session. User-invoked only."
argument-hint: "<gate id, e.g. G2>"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Read
  - Bash(python3 .claude/skills/adlc/scripts/*:*)
---

# /approve-gate

Use this only when `config/project_config.json > gate_mode` is `local`. In github mode, tell the user that gates are approved by reviewing the gate pull request, give its link (`gate_github.py status`), and stop.

The approver runs this. The agent presents the evidence and records the approver's choice; it never chooses on their behalf.

1. Read `CLAUDE.md` and `.claude/skills/adlc/SKILL.md`. Gate id from `$ARGUMENTS`; if missing, run `adlc_gate.py status` and ask which gate.
2. Run `python3 .claude/skills/adlc/scripts/adlc_gate.py check --gate <id>`. If the gate is not pending, say so and stop.
3. Show a review brief (≤ 250 words): the artifact link, the requester's summary, validation result from `adlc/.state/validation/<phase>.json`, policy result from `adlc/.state/policy/<phase>.json`, and the required roles. Do not paste the artifact.
4. Ask with `AskUserQuestion`: **Approve** · **Reject (needs a reason)** · **Not now**. Also show the same options as plain text in case the picker does not render.
5. Record exactly what was chosen:
   - Approve: `adlc_gate.py approve --gate <id> --comment "<optional>"`
   - Reject: `adlc_gate.py reject --gate <id> --comment "<reason>"`
   - Waive (only if the user explicitly asks and holds `waiver_approver`): `adlc_gate.py waive --gate <id> --reason "<reason>" --days <n>`
6. Report the script's output verbatim. If it refused (missing role, separation of duties, artifact changed), explain what that means and who can act. Never retry under a different identity.

Additional context from user invocation: $ARGUMENTS
