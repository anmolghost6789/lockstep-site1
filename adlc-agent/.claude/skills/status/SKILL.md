---
name: status
description: "Show run state, phase and gate status, pending approvers, policy results, audit chain integrity and the next safe action. User-invoked only."
disable-model-invocation: true
allowed-tools:
  - Read
  - Bash(python3 .claude/skills/adlc/scripts/*:*)
---

# /status

1. If `adlc/.state/run_state.json` does not exist, say: `No active ADLC run. Use /discover-define to begin.` and stop.
2. Run `recover.py diagnose` (interrupted phases, invalid or changed artifacts, gate state, audit chain, CI evidence), `state.py show`, the gate status for the active mode (`gate_github.py status` or `adlc_gate.py status`), and `metrics.py show`.
3. Display: run ID and status; each phase with its status, gate status and required approver role; the diagnosis findings in severity order; key metrics (time in phase, approval wait, rejections); `progress.json > next` as the next safe action.
4. If the audit chain is broken, say so first and recommend contacting the platform team before any further gate decisions.
