# Command reference

| Claude Code | Copilot Chat | What it does |
|---|---|---|
| `/discover-define [intent]` | `@lockstep discover` | Intent to AI Product Requirement Spec; requests G1 |
| `/architect-design` | `@lockstep architect` | Spec to blueprint, Level-1 plan and ADRs; requests G2 |
| `/build-orchestrate [UNIT-00N]` | `@lockstep build` | Builds units in bolts, one pull request per unit; requests G3 |
| `/evaluate-validate` | `@lockstep evaluate` | Independent evaluation against the spec's thresholds; requests G4 |
| `/release-operate [environment]` | `@lockstep release` | Pinned, governed release with rollback and runbook; requests G5 |
| `/observe-evolve [window]` | `@lockstep observe` | Outcomes vs success criteria, backlog and next intent; requests G6 |
| `/status` | `@lockstep status` | Phases, gates, approvers, validation, audit chain, next step |
| `/cancel` | `@lockstep cancel` | Stops the run; keeps every artifact and record |
| `/approve-gate <gate>` | (not needed) | Local gate mode only: record an approval, rejection or waiver |
| `/refresh-reference-store` | (Claude Code only) | Rebuild governed reusable patterns |

## Scripts

All in `.claude/skills/adlc/scripts/`, standard library only:

| Script | Purpose |
|---|---|
| `setup_codeowners.py` | Generate CODEOWNERS from gate roles; print branch protection |
| `gate_github.py` | Request, check and list pull-request gates |
| `adlc_gate.py` | Local gate mode: request, approve, reject, waive, check |
| `validate_artifact.py` | Structure, placeholders, IDs and traceability |
| `policy_check.py` | The phase's policy pack |
| `state.py` | Run state and `progress.json` |
| `audit_log.py` | Append, verify and export the audit log |
| `eval_run.py` | Run an evaluation suite against thresholds from the approved spec; compare with and without a pack |
| `recover.py` | Diagnose interrupted or inconsistent runs; route changes to the phase that owns them |
| `route.py` | Choose the approved agent and model for each phase or unit, with reasons |
| `metrics.py` | Delivery metrics per phase; opt-in push to your registry |
| `pack.py` | Install, upgrade, verify and roll back packs from a Lockstep registry |
