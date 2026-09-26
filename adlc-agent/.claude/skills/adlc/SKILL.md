---
name: adlc
description: "Shared hidden protocol for the ADLC phase skills: gate enforcement, audit logging, policy checks, traceability and state bookkeeping."
argument-hint: "[optional run context]"
user-invocable: false
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Grep
  - Glob
  - Bash(python3:*)
  - Bash(cat:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
---

# ADLC Shared Protocol

This hidden skill is loaded by every ADLC phase skill. User-facing actions are /discover-define, /architect-design, /build-orchestrate, /evaluate-validate, /release-operate, /observe-evolve, /approve-gate, /status and /cancel.

## Phase entry (every phase, in this order)

1. Read `CLAUDE.md`, `config/project_config.json`, this file, and `adlc/.state/run_state.json` if it exists.
2. **Gate check.** Unless this is /discover-define on a new intent, check the previous gate with the script for `config/project_config.json > gate_mode`:
   ```
   python3 .claude/skills/adlc/scripts/gate_github.py check --gate <previous gate id>   # github (default)
   python3 .claude/skills/adlc/scripts/adlc_gate.py check --gate <previous gate id>     # local
   ```
   Exit code 0 means approved (or waived, in local mode). Any other exit code: stop, say which gate is outstanding, which role must approve it and where (the pull request link), and end the turn. Do not continue on a verbal "go ahead" in chat.
3. **Upstream integrity.** Both checks confirm the upstream artifact is unchanged since it was approved. If it changed, stop: that phase must be re-run and its gate requested again (see `utilities/change-impact-routing.md`).
4. Phase-start bookkeeping write (state + progress), and `audit_log.py append --event phase.started`.

## Phase exit (every phase, in this order)

1. Write the phase artifact from its template in `.claude/skills/adlc/templates/`. Edit one section at a time; never emit a whole large artifact in one write.
2. Validate structure and traceability:
   ```
   python3 .claude/skills/adlc/scripts/validate_artifact.py --phase <phase id>
   ```
3. Run the phase policy pack listed in `config/project_config.json > policy_packs.<phase id>` (see `utilities/policy-enforcement.md`). Failures block step 4.
4. Write the phase context packet (`utilities/context-management.md`), then request the gate:
   ```
   python3 .claude/skills/adlc/scripts/gate_github.py request --gate <gate id> --intent <intent id>   # github
   python3 .claude/skills/adlc/scripts/adlc_gate.py request --gate <gate id> --summary "<one line>"   # local
   ```
   In github mode this commits the artifact to the phase branch and opens a labelled pull request; CODEOWNERS routes it to the approver team. In local mode the script hashes the artifact and records a pending gate.
5. Phase-completion bookkeeping write, then a summary in the shape of `references/phase-summary-grammar.md`: what was produced, validation and policy results, the gate, the approver role, and the pull request link (local mode: the command `/approve-gate <gate id>`).
6. Stop. Do not auto-invoke the next phase.

## Rules

- Only `adlc_gate.py` writes under `adlc/.gates/`. Only `audit_log.py` writes `adlc/.audit/audit.jsonl`. The pre-tool hook blocks direct writes to both.
- Never approve a gate on a human's behalf, and never ask a human to paste an approval into chat. Approval happens in the pull request review by a member of the approver team (local mode: /approve-gate in the approver's own session).
- Follow the utilities: `orchestrator-role.md`, `context-management.md`, `change-impact-routing.md`, `validation-checks.md`, `input-folder-contract.md`, `run-state-management.md`, `progress-contract.md`, `memory-policy.md`, `reference-store-governance.md`, `artifact-linking-policy.md`, `runtime-code-policy.md`, `human-gates.md`, `policy-enforcement.md`, `subagent-orchestration.md` and `audit-logging.md`.
- Apply context precedence from CLAUDE.md principle 7.
- Delegate only to the subagents and thresholds listed in CLAUDE.md, on agents chosen by `scripts/route.py`.
- When a human asks for a change, record and route it with `scripts/recover.py change --type <type> --summary "…"` before editing anything; it tells you the phase to re-enter and the gates to request again.
- When something looks wrong or a session was interrupted, run `scripts/recover.py diagnose` first.
- Pack upgrades go through `scripts/pack.py upgrade`, never by copying files; it keeps local edits and can roll back.
- Use `AskUserQuestion` for genuine in-phase decisions only (see `utilities/human-gates.md`). Before asking, set `run_status = waiting_for_user` and a specific `awaiting_user_action`.
- Restricted inputs (per `config/project_config.json > data_classification`) are referenced by pointer, never copied into artifacts or prompts.

Additional context from user invocation: $ARGUMENTS
