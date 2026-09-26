---
name: analyze-inputs
description: >-
  Normalize messy inputs, detect template conformance, resolve conventions, capture source evidence, and build the canonical model. No mid-phase questions. Use when the user wants to analyze or normalize the build inputs, resolve naming/type conventions, or build the canonical model — after /start-build-run.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Analyze Inputs

## Prerequisites
- `/start-build-run` completed
- Run ledger exists

## Required reads (supervisor — small files only)
- `session.json` — read summary fields only, not full content
- `phase_handoff.json` from prior phase
- `state/run_id_<ID>/discovery/input_evaluation_report.json` — read this for the pre-classified file list and complexity score

**The supervisor MUST NOT read raw input files.** The input classification and word counts are already in `input_evaluation_report.json::input_summary.corpus_inventory`. Read that manifest — not the source files. Pass file paths to the sub-agent; the sub-agent reads the actual content.

## Delegation thresholds

**Delegate to `input-analyzer` sub-agent when ANY of these are true:**
- Total input word count > 5,000 words (read from `input_evaluation_report.json::input_summary.total_words`)
- More than 3 input files
- Any single STTM file exceeds 100 rows (read from `input_evaluation_report.json`)
- Complexity = `moderate` or `high` in `input_evaluation_report.json`

Below ALL thresholds: supervisor may analyze inline. But delegation is always safer for context budget.

## Goal

Produce evidence-backed discovery artifacts. No mid-phase questions. The supervisor's job is to orchestrate and write the handoff — not to read raw inputs.

## Step 1 — Read phase handoff and classification manifest

Read `phase_handoff.json` and `input_evaluation_report.json`. Extract:
- List of classified input file paths (from `corpus_inventory`)
- Total word count and complexity tier
- Which artifact types are selected (`scope_selection` from session.json)

Do not read any input file at this point.

## Step 2 — Decide delegation path

**Path A — delegate (above thresholds or recommended):**

Build the delegation prompt with:
- All input file paths (from corpus_inventory) — not file contents
- Output paths for all discovery artifacts
- References to read first: `runtime_contract.md`, `quality_standards.md`
- The resolved `scope_selection` so the sub-agent knows which artifact families are active

Spawn `input-analyzer` sub-agent. While it runs, the supervisor holds only the session summary and delegation context — nothing else.

**Path B — inline (below all thresholds):**

Read ONLY the files listed in corpus_inventory, one at a time. Apply the same Steps 2–4 inline. Do not accumulate all files in context simultaneously — read, extract findings to a local notes structure, then clear the file content before reading the next.

## Step 3 — Receive handoff and validate

After the sub-agent (or inline pass) completes:
- Validate handoff: `completion_status` present, all `outputs_written` files actually exist on disk (`test -f`)
- Do NOT re-read the discovery artifact contents to "verify" them — trust the filesystem check
- If validation fails, re-delegate or escalate at checkpoint

## Step 4 — Write conflicts_resolved and sync

The sub-agent writes `effective_conventions.json`. The supervisor reads only the `conflicts_resolved` array length from it (to confirm it was written) and records the count in session.json. Do not read the full file.

**Mandatory: `effective_conventions.json` must contain a `conflicts_resolved` array** (written by the sub-agent per its instructions). This is the authoritative source for the run's assumptions register surfaced during `/evaluate-build` and `/revise-build`.

Sync to `outputs/`. Update session.json. Write phase_handoff.json.

Present to user: analysis summary with table count, convention decisions made, assumption count, conflict count, issues. Recommend: `/plan-build`.

Tell user: "Run `/compact focus on: run_id, phase status, user decisions, next steps` then run `/plan-build`."

## Jira traceability

Follow the canonical traceability protocol in `.claude/skills/build-agent/references/jira_integration.md#traceability-protocol`. Phase summary line for this skill:

> `Input analysis complete. Canonical model built. <N> source columns registered. <N> conventions resolved.`

## Required writes
- All discovery artifacts written by sub-agent (or inline pass):
  - `state/run_id_<ID>/discovery/effective_conventions.json`
  - `state/run_id_<ID>/discovery/canonical_build_model.json`
  - `state/run_id_<ID>/discovery/source_column_registry.json`
  - `state/run_id_<ID>/discovery/derivation_catalog.json`
  - `state/run_id_<ID>/discovery/dq_catalog.json`
  - `state/run_id_<ID>/discovery/relationships.json`
- Supervisor writes:
  - `state/run_id_<ID>/phase_handoff.json`
  - `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
