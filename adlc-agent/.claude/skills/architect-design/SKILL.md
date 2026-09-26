---
name: architect-design
description: >-
  Phase 02. From the approved AIPRS, create the Agentic Solution Blueprint: the Level-1 plan
  decomposed into units, agent topology and orchestration, model selection, knowledge and RAG
  design, tools/APIs/MCP integration, security and governance, with ADRs. Ends with gate G2.
argument-hint: "[optional architecture constraints]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(python3 .claude/skills/adlc/scripts/*:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
  - mcp__atlassian__*
  - mcp__github__*
---

# 02 Architect & Design

Purpose: produce `adlc/02-blueprint.md` and `adlc/adr/ADR-*.md`. The blueprint's Level-1 plan is the only list of units /build-orchestrate is allowed to build.

## Required Reads
- CLAUDE.md, config/project_config.json, .claude/skills/adlc/SKILL.md
- adlc/01-aiprs.md (approved)
- .claude/skills/adlc/templates/02-blueprint.template.md
- config/governance/model_policy.json and config/governance/mcp_allowlist.json
- context/guidance/ and memory/PATTERN_LIBRARY.md

## Entry gate
`python3 .claude/skills/adlc/scripts/adlc_gate.py check --gate G1` must exit 0. Otherwise report the outstanding gate and stop.

## Rules
- Run only this phase. Stop at the boundary. Never auto-invoke /build-orchestrate.
- Every unit (`UNIT-`), agent (`AGT-`) and decision (`ADR-`) has an ID and a `Trace:` line pointing to AIPRS IDs. A unit that traces to nothing is out of scope; remove it.
- Units are cohesive and independently testable. Target 1–8 units; more than 8 triggers `solution-architect`.
- Models may only be chosen from `approved_models`. Changing the phase pins in `config/project_config.json` requires an ADR.
- Tools and MCP servers may only be chosen from the allow-list. A needed server that is not listed becomes an open item for the platform team, not a design assumption.
- For every agent that can take an external action (write to a system of record, send a message, move money), specify its human-in-the-loop control and its failure mode.

## Idempotent re-entry
- Blueprint exists, validation passes and it was written after G1's approval → skip to Human Gate.
- G2 rejected → revise only the sections named in the rejection comment.

## Steps
1. `state.py start --phase architect-design`.
2. Business and domain flow: summarize the target process in the `Context` section, citing AIPRS IDs.
3. Level-1 plan: decompose into units. For each: goal, inputs, outputs, dependencies, acceptance tests, `Trace:`.
4. Agent topology and orchestration: which agents exist, what each may do, how they hand off, and where a human approves.
5. Model selection: per agent, model from the approved list, why, data classification it will see, fallback.
6. Knowledge and RAG design: sources, chunking, retrieval, citation policy, freshness, access control.
7. Tools, APIs and MCP integration: allow-listed servers, scopes, and dry-run strategy for write tools.
8. Security and governance: threat model summary, PII handling, guardrails, audit points, and the NFRs they satisfy.
9. Decisions: write one ADR per significant choice to `adlc/adr/ADR-NNN-<slug>.md` and list them in the blueprint.
10. `validate_artifact.py --phase architect-design`, then `policy_check.py --phase architect-design`.

## Human Gate G2
- Approver: the **architect** team, via CODEOWNERS for `adlc/02-blueprint.md`. The author cannot approve (GitHub blocks self-approval).
- Request (github mode): `python3 .claude/skills/adlc/scripts/gate_github.py request --gate G2 --intent <intent id>`. This opens a pull request labelled `adlc-gate-G2`.
- The approver reviews the pull request and approves it; merging passes the gate. Any later change to the artifact needs a new pull request and a new approval.
- Local mode: `adlc_gate.py request --gate G2 --summary "..."`, and the approver runs `/approve-gate G2`.

## Phase completion
11. `state.py complete --phase architect-design`.
12. Summary: unit count, agent count, ADR list, open items for the platform team, links.

## End Of Turn
G2 is waiting for an architect in the gate pull request; give its link. Recommend `/build-orchestrate` once approved. Stop.

Additional context from user invocation: $ARGUMENTS
