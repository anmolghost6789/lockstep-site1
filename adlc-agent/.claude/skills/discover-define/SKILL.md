---
name: discover-define
description: >-
  Phase 01. Turn a business intent into an AI Product Requirement Spec (AIPRS): clarifying questions,
  personas, user stories, functional and non-functional requirements, risks, constraints and
  measurable success criteria. Ends by requesting gate G1 from a product owner.
argument-hint: "[optional: path to intent file or one-line intent]"
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
---

# 01 Discover & Define

Purpose: produce `adlc/01-aiprs.md`, an approved statement of what the product must do and how success is measured. Every later phase traces back to the IDs defined here.

## Required Reads
- CLAUDE.md
- config/project_config.json
- .claude/skills/adlc/SKILL.md
- .claude/skills/adlc/templates/01-aiprs.template.md
- .claude/skills/adlc/utilities/human-gates.md
- context/guidance/ (enterprise → domain → project), and memory/MEMORY.md
- adlc/06-backlog.md from the previous cycle, if this intent came from it

## Rules
- Run only this phase. Stop at the phase boundary. Never auto-invoke /architect-design.
- This is the only phase with no upstream gate. If `adlc/.gates/G6.json` exists from a previous cycle, the new intent must be one of its backlog items marked `next_intent: true`.
- Classify every input with `config/project_config.json > data_classification`. Inputs above `internal` are referenced by path only; never quote them.
- Ask clarifying questions with `AskUserQuestion`, at most 4 per batch, each with a recommended default. Record answers in the AIPRS `Open Questions` table as resolved, with who answered.
- Every requirement has an ID (`US-`, `FR-`, `NFR-`, `RISK-`, `SC-` + 3 digits) and is testable. "Fast", "secure" and "accurate" are not requirements until they have a number.
- Every NFR that will be measured in phase 04 must state its threshold here. Phase 04 may not invent thresholds.

## Idempotent re-entry
- `adlc/01-aiprs.md` exists and `validate_artifact.py --phase discover-define` passes, and inputs are unchanged since the last run → skip to Phase completion.
- G1 was rejected → read the rejection comment from `adlc/.gates/G1.json`, revise only the affected sections, and re-request.

## Steps

1. Phase start: `python3 .claude/skills/adlc/scripts/state.py start --phase discover-define`.
2. Locate the intent: `$ARGUMENTS`, `inputs/instructions/intent.md`, or a Jira epic via the Atlassian MCP server. If none exists, explain where to put it and stop.
3. If inputs exceed the `requirements_analyst` thresholds, spawn `requirements-analyst` to index them; otherwise index inline. The index lists documents and pointers, not copied content.
4. Run up to three clarification rounds. Stop asking once every success criterion has a number and an owner.
5. Write `adlc/01-aiprs.md` from the template, one section per edit:
   Intent · Personas · User Stories · Functional Requirements · Non-Functional Requirements · Risks and Constraints · Success Criteria · Open Questions.
6. Validate: `python3 .claude/skills/adlc/scripts/validate_artifact.py --phase discover-define`. Fix and re-run until it passes.
7. Policy pack: `python3 .claude/skills/adlc/scripts/policy_check.py --phase discover-define` (no_secrets, pii_scan, trace_ids_present). Fix findings before continuing.

## Human Gate G1
- Approver: the **product owner** team, via CODEOWNERS for `adlc/01-aiprs.md`. The author cannot approve (GitHub blocks self-approval).
- Request (github mode): `python3 .claude/skills/adlc/scripts/gate_github.py request --gate G1 --intent <intent id>`. This opens a pull request labelled `adlc-gate-G1`.
- The approver reviews the pull request and approves it; merging passes the gate. Any later change to the artifact needs a new pull request and a new approval.
- Local mode: `adlc_gate.py request --gate G1 --summary "..."`, and the approver runs `/approve-gate G1`.

## Phase completion
8. `python3 .claude/skills/adlc/scripts/state.py complete --phase discover-define`.
9. Summary (≤ 300 words): counts of stories, FRs, NFRs, risks and success criteria; unresolved open questions; validation and policy results; link to the AIPRS.

## End Of Turn
Tell the user G1 is waiting for the product owner team in the gate pull request, with its link. Recommend `/architect-design` once G1 is approved. Stop.

Additional context from user invocation: $ARGUMENTS
