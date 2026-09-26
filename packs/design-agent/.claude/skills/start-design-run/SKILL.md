---
name: start-design-run
description: >-
  Begin a design run end-to-end: apply the empty-input guard, snapshot and ingest inputs, publish the thin input index and readiness report, then select and document source systems, tables, gaps, and source-use decisions in the same phase.
argument-hint: "[optional context]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(cat:*)
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(grep:*)
  - Bash(mkdir:*)
  - Bash(cp:*)
  - Bash(mv:*)
  - Bash(rm:*)
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# Start Design Run

Purpose: one continuous phase that takes the run from raw inputs to a decided source universe. It verifies usable inputs exist, snapshots evidence once, ingests binaries to text sidecars, publishes a THIN input index plus the input set evaluation report, and then — in the same turn unless the readiness verdict is blocking — selects the source universe and documents rejected or missing sources, every candidate stated exactly once.

## Required Reads
- CLAUDE.md
- config/project_config.json
- .claude/skills/design-agent/SKILL.md
- outputs/00_state/run_state.json when continuing an existing run

## Rules
- Run only this phase.
- Stop at the phase boundary and return control to the user.
- Do not auto-invoke the next slash skill, even if the user previously asked to do everything.
- Update outputs/00_state/run_state.json and root progress.json at most twice per phase: once at phase start and once at phase completion (fold human-wait status into those two writes). The phase-completion rewrite of root progress.json is MANDATORY before the final reply of the phase. See CLAUDE.md principle 14.
- Keep chat concise; summarize and link to files rather than pasting report or artifact bodies.
- Do NOT restate ingested input content into JSON — index it and point at it.

## Idempotent re-entry

When this skill is invoked again for a run that already started (resume after an interruption, a stale-state recovery, or a repeated command), do NOT redo completed work. Detect what already exists and is valid, skip it, and continue from the first missing or stale step:

- `outputs/00_state/input_snapshot/` + ingest sidecars + `inputs_manifest.json` present and the snapshot matches current `inputs/` → skip snapshot + ingest. If `inputs/` changed since the snapshot (new/removed/modified meaningful files), re-snapshot and re-ingest.
- `outputs/00_state/standard_input_set/input_index.json` + `input_set_evaluation_report.md` present and newer than the ingest manifest → skip Part A writing; re-read the report's verdict and continue.
- `outputs/00_state/source_discovery/source_decisions.json` + `source_gap_report.md` present and newer than `input_index.json` → source discovery is done; go straight to publish + phase-completion bookkeeping.
- Anything missing, invalid JSON, or older than its upstream artifact is stale — redo only that piece.

## Part A — Ingest inputs and assess readiness

1. Apply the empty-input guard before creating run files. Meaningful inputs are user-provided files under inputs/<category>/; ignore README.md, .gitkeep, .keep, and .DS_Store.
2. If no meaningful input exists, explain where to place files and stop. If the user refuses input, say exactly: Sorry! I can't start the run without any input..
3. **Stale-input warning (before creating any run files).** Hash every meaningful input file (sha256) and compare the hash set against any prior `outputs/00_state/input_snapshot/` archive under `outputs/00_state/logs/history/` (or an equivalent archive location if configured). A python one-liner over both directory trees is enough — do not write a script for this. If the sets are identical to a previous completed run, WARN the user: "inputs identical to a completed prior run — the same design will result; replace inputs or confirm", and require explicit confirmation before proceeding. Do not silently start a duplicate run.
4. Initialize / resume run state at `outputs/00_state/run_state.json` and rewrite the run-root `progress.json`. Perform the phase-start state/progress write here.
5. Snapshot inputs/ to `outputs/00_state/input_snapshot/` and context/guidance/ to `outputs/00_state/context_snapshot/`. Run the shipped ingester over the snapshot to produce UTF-8 sidecars plus `inputs_manifest.json`:
   ```
   python .claude/skills/design-agent/scripts/ingest_inputs.py --root outputs/00_state --roots input_snapshot context_snapshot
   ```
   Downstream work reads sidecar text, never binaries.
6. Classify inputs. Use `input-analyzer` only when there are more than 15 input files OR total input snapshot size is greater than 15 MB OR the source inventory declares more than 30 tables. Below these thresholds, the orchestrator classifies inputs inline (spawning a subagent for a handful of files adds cold-start overhead that dominates the classification work itself).
7. When the threshold trips, fan out TWO input-analyzer subagents in parallel with disjoint scope arguments:
   - `scope=requirements` -> writes `input_index.requirements.json` (index entries for requirements, instructions, business rules, KPIs, KBQs, additional documents).
   - `scope=sources` -> writes `input_index.sources.json` (index entries for source systems, tables, schemas, samples).
   After both return, the orchestrator merges the two fragments into `input_index.json`, deletes the fragments, and writes `input_set_evaluation_report.md` itself.
8. Write exactly TWO files under `outputs/00_state/standard_input_set/`:
   - `input_index.json` — a THIN pointer index, NOT a restatement of ingested content. One entry per requirement / rule / KPI / KBQ / declared source table / open item found: `{"id": "REQ-001", "topic": "<= 10 words", "where": "<sidecar file> > <section/table anchor>"}`, plus a `documents` list (filename, category, sidecar path, one-line purpose) and a per-category note for empty input folders. No copied text bodies — later work follows the pointers into the sidecars.
   - `input_set_evaluation_report.md` — the readiness assessment: files received, strength score per dimension, gaps and their design impact, an **Assumptions & open items** section (this absorbs the former assumptions register — run-level assumptions needing confirmation live here, not in a separate JSON), and the readiness verdict.
   Do NOT write user_instructions.json, data_requirements.json, source_inventory.json, additional_documents.json, assumptions_register.json, or any other stub/empty JSON — those restatement files are retired; the index plus sidecars carry the same information without stating it twice.
9. Do not read entire large sidecars in this phase. Read each document's structure (headings/tables) and only the sections needed to score readiness; source discovery below reads the sections the index points it to.

## Readiness checkpoint — conditional pause (the ONLY mid-phase stop)

After writing `input_set_evaluation_report.md`, inspect its readiness verdict:

- **Error-grade verdict (blocking gaps)** — the input set cannot support source discovery (e.g. no source inventory evidence at all, requirements unreadable, verdict Insufficient, or a critical blocker that makes source selection guesswork): STOP HERE. Set `waiting_for_user` + `awaiting_user_action = "input_clarification"` (folded into the bookkeeping writes per CLAUDE.md principle 14), link the readiness report, list the blocking gaps and exactly what the user should add or confirm, and end the turn. On the next invocation the idempotent re-entry rules resume from source discovery once the gaps are resolved (or the user explicitly says to proceed at documented risk).
- **Any non-blocking verdict (pass or warn-grade)** — do NOT pause, do NOT ask for confirmation, do NOT end the turn. Note gaps in the report and continue immediately to Part B in the same turn. Warnings and open items are recorded as assumptions/gaps, never used as an excuse to stop.

## Part B — Discover and decide sources

10. Read `outputs/00_state/standard_input_set/input_index.json` and follow its pointers into the ingested sidecars for source evidence. Consult governed reference-store patterns as advisory hints only; current-run evidence wins.
11. Identify required source concepts from requirements, instructions, business rules, KPIs, and KBQs; match them to available sources.
12. Write exactly TWO files under `outputs/00_state/source_discovery/`:
    - `source_decisions.json` — ONE record per candidate source entity: `{"id", "entity", "source_system", "source_table", "status": "selected | rejected | missing", "rationale", "evidence": [index ids / sidecar pointers], "gaps": [...]}`. Plus top-level blocks: `required_concepts` (id -> one-line concept), `reference_store_audit` (`{"store_present": bool, "patterns_consulted": [...], "influence": "advisory only — current-run evidence wins"}`), and `waivers`.
    - `source_gap_report.md` — the human-facing view: selected-sources table, gaps table with design impact and mitigation, verdict.
    Do NOT write required_source_concepts.json, candidate_source_matches.json, selected_sources.json, rejected_sources.json, source_selection_decisions.json, or a separate evidence-map file — those are all views of `source_decisions.json` and are retired.
13. If a genuine ambiguity requires a human choice, ask that ONE clarification (AskUserQuestion primary, yellow typed fallback) and record the answer as a confirmed clarification inside `source_decisions.json`.

Downstream contract: /design-architecture designs only from `source_decisions.json` entries with `status: "selected"` (plus explicit waivers). Nothing else in the run may re-list the selected sources.

## Phase completion

14. Publish `input_set_evaluation_report.md` to `outputs/01_inputs/` and `source_decisions.json` + `source_gap_report.md` to `outputs/02_sources/`.
15. Perform the mandatory phase-completion bookkeeping write: update `outputs/00_state/run_state.json` and rewrite the run-root `progress.json` (step `start-design-run` done, `next` = /design-architecture).
16. Give a concise summary (readiness verdict, selected/rejected/missing source counts, key gaps) with clickable links.

## End Of Turn
Recommend /design-architecture. Stop. Do not auto-invoke the next phase, even if the user previously said to do everything.

Additional context from user invocation: $ARGUMENTS
