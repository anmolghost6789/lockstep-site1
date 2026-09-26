---
name: build-orchestrate
description: >-
  Phase 03. Implement the approved Level-1 plan unit by unit in bolts: small build-and-validate
  cycles that produce agents, skills, tools, guardrails, RAG pipelines, integrations and generated
  code with unit tests. Each unit's diff is accepted by an engineer. Ends with gate G3.
argument-hint: "[optional: UNIT-00N to build a single unit]"
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
  - Bash(npm test:*)
  - Bash(pytest:*)
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git switch:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
  - mcp__github__*
---

# 03 Build & Orchestrate

Purpose: turn the blueprint into a working agentic product and record the build in `adlc/03-units.yaml`, which is the ledger of what was built, by which agent, in which bolt, with which tests.

## Required Reads
- CLAUDE.md, config/project_config.json, .claude/skills/adlc/SKILL.md
- adlc/01-aiprs.md and adlc/02-blueprint.md (both approved), adlc/adr/
- .claude/skills/adlc/templates/03-units.template.yaml
- .claude/skills/adlc/utilities/subagent-orchestration.md

## Entry gate
`adlc_gate.py check --gate G2` must exit 0.

## Rules
- Build only units listed in the blueprint's Level-1 plan. New scope goes back to /architect-design.
- Work on a branch named `adlc/<intent_id>/<unit>`. Never commit to the default branch. Never force-push.
- A **bolt** is one build-and-validate cycle: at most `bolts.max_files_changed_per_bolt` files and `bolts.max_minutes_per_bolt` minutes, ending with tests run. A bolt that fails its tests is fixed in the next bolt, not skipped.
- Every bolt records `tests_run`, `tests_passed`, `files_changed` and a `trace:` list of FR/NFR IDs it serves.
- Write tools (anything that changes a system of record) are built dry-run first and must stay dry-run until /release-operate.
- Generated prompts and agent configs are code: they live in the repo, are reviewed in the diff, and are versioned.
- Never place secrets in code or config. Reference secret names from your vault only.

## Subagents
If the plan has more than `bolt_builder_min_independent_units` units with no dependency between them, spawn one `bolt-builder` per unit with a disjoint file scope. Otherwise build inline. Record the builder in each unit's `built_by`.

## Idempotent re-entry
- Units with `status: accepted` and unchanged files are skipped.
- `$ARGUMENTS` naming a unit rebuilds only that unit.

## Steps
1. `state.py start --phase build-orchestrate`. Write the header of `adlc/03-units.yaml` (intent_id, blueprint_sha256 from the G2 gate file).
2. Route the work: `python3 .claude/skills/adlc/scripts/route.py units` assigns each unit an approved agent and model by capability, data level and cost, and records why in `adlc/.state/routing.json`. Record each unit's `built_by` from it. A unit with no eligible agent is a blocker for the platform team, not something to work around.
3. Order units by dependency. For each unit:
   a. Plan the bolts (usually 2–5).
   b. For each bolt: implement, run tests, append the bolt record to `03-units.yaml`.
   c. When the unit's acceptance tests pass, open a pull request (GitHub MCP) or present the diff, and set `status: in_review`.
   d. **Per-diff review:** an engineer accepts or rejects the diff. Record the decision under the unit's `review:` with reviewer identity. Rejections return the unit to (b).
4. After all units are accepted: `validate_artifact.py --phase build-orchestrate` and `policy_check.py --phase build-orchestrate` (no_secrets, pii_scan, mcp_allowlist, tests_per_bolt, license_scan). `license_scan` passes only with CI evidence in `adlc/.state/evidence/license_scan.json`.

## Human Gate G3
- Approver: the **engineer** team, via CODEOWNERS for `adlc/03-units.yaml`. The author cannot approve (GitHub blocks self-approval).
- Request (github mode): `python3 .claude/skills/adlc/scripts/gate_github.py request --gate G3 --intent <intent id>`. This opens a pull request labelled `adlc-gate-G3`.
- The approver reviews the pull request and approves it; merging passes the gate. Any later change to the artifact needs a new pull request and a new approval.
- Local mode: `adlc_gate.py request --gate G3 --summary "..."`, and the approver runs `/approve-gate G3`.

## Phase completion
5. `state.py complete --phase build-orchestrate`.
6. Summary: units, bolts, tests, pull requests, agents used, anything left dry-run, links.

## End Of Turn
G3 is waiting for an engineer in the gate pull request; give its link. Recommend `/evaluate-validate` once approved. Stop.

Additional context from user invocation: $ARGUMENTS
