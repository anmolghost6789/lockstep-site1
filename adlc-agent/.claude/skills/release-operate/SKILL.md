---
name: release-operate
description: >-
  Phase 05. Package deployable units (code, config, prompts, infrastructure), set up CI/CD and
  environments, version models, prompts and agents, check security, access and compliance, and
  prepare monitoring, runbooks and a staged production rollout. Ends with gate G5 from a release
  manager, plus a security officer when risk is high.
argument-hint: "[optional: target environment]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(python3:*)
  - Bash(git status:*)
  - Bash(git tag:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
  - mcp__github__*
---

# 05 Release & Operate

Purpose: produce `adlc/05-release.md`, the governed release record. Nothing reaches production without it being approved, and the deployment pipeline reads its approval from `adlc/.gates/G5.json`.

## Required Reads
- CLAUDE.md, config/project_config.json, .claude/skills/adlc/SKILL.md
- adlc/02-blueprint.md, adlc/03-units.yaml, adlc/04-scorecard.json (all approved)
- .claude/skills/adlc/templates/05-release.template.md

## Entry gate
`adlc_gate.py check --gate G4` must exit 0, and `04-scorecard.json.verdict` must be `pass`.

## Rules
- **Always spawn `release-auditor`** to produce the readiness checklist independently.
- Pin every version: code commit, container digests, model IDs, prompt versions, agent config versions, dataset versions. `latest`, `main` and `*` are not versions.
- Initial rollout is `release.initial_rollout_percent` of traffic behind a flag, with automatic rollback criteria stated as numbers.
- If `release.require_rollback_rehearsal` is true, the rollback must be rehearsed in staging and the evidence linked.
- Write tools leave dry-run only here, and only for the rollout cohort.
- The agent never deploys to production itself. It prepares the release; the pipeline deploys after G5, checking that the G5 pull request was approved and merged and the release record is unchanged since.
- Assess risk (`low | medium | high | critical`) from blast radius, data classification touched, and write tools enabled. High or critical adds `security_officer` to G5.

## Idempotent re-entry
- Release record exists for the current scorecard sha256 and validation passes → skip to Human Gate.

## Steps
1. `state.py start --phase release-operate`.
2. Assemble deployable units and pin versions in the `Versions` section.
3. Deployment plan: environments, CI/CD workflow reference, feature flags, rollout stages and promotion criteria.
4. Rollback plan: trigger thresholds, steps, owner, rehearsal evidence.
5. Runbook: alerts, dashboards, on-call, known failure modes and responses, how to disable each agent.
6. Risk assessment with the resulting risk level.
7. Spawn `release-auditor` to write the readiness checklist into `Readiness Checklist`.
8. CI must produce an SBOM and write `adlc/.state/evidence/sbom_present.json`.
9. `validate_artifact.py --phase release-operate`, then `policy_check.py --phase release-operate` (no_secrets, sbom_present, rollback_plan, versions_pinned).

## Human Gate G5
- Approver: the **release manager** team, via CODEOWNERS for `adlc/05-release.md`. The author cannot approve (GitHub blocks self-approval).
- Request (github mode): `python3 .claude/skills/adlc/scripts/gate_github.py request --gate G5 --intent <intent id> --risk <level>`. This opens a pull request labelled `adlc-gate-G5`.
- The approver reviews the pull request and approves it; merging passes the gate. Any later change to the artifact needs a new pull request and a new approval.
- High or critical risk also adds the security officer team as a reviewer (`--risk <level>`); confirm their approving review before recommending release.
- Local mode: `adlc_gate.py request --gate G5 --summary "..." --risk <level>`, and the approver runs `/approve-gate G5`.

## Phase completion
10. `state.py complete --phase release-operate`.
11. Summary: release ID, risk level, required approvers, rollout plan, rollback trigger, links.

## End Of Turn
G5 is waiting for its approvers in the gate pull request; give its link. After approval the pipeline deploys; recommend `/observe-evolve` once the observation window in the release record has elapsed. Stop.

Additional context from user invocation: $ARGUMENTS
