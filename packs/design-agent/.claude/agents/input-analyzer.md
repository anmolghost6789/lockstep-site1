---
name: input-analyzer
description: Analyze large or complex design input sets when thresholds are met.
model: inherit
memory: project
---

# input-analyzer

Spawn only when the run has more than 15 input files OR the total input snapshot size is greater than 15 MB OR the source inventory declares more than 30 tables. Runs below these thresholds are fast enough for the orchestrator to classify inputs inline and do not need a subagent.

When the thresholds trigger, the orchestrator spawns TWO input-analyzer instances in parallel with disjoint file assignments. Each instance receives an explicit `scope` argument and writes ONE thin-index fragment (pointer entries `{"id", "topic", "where"}` per the /start-design-run contract — no restated content bodies):

- `scope=requirements` -> `outputs/00_state/standard_input_set/input_index.requirements.json`
  (index entries for requirements, instructions, business rules, KPIs, KBQs, additional documents, plus run-level assumptions found)
- `scope=sources` -> `outputs/00_state/standard_input_set/input_index.sources.json`
  (index entries for source systems, declared tables, schemas, samples, catalogs)

Each instance reads the ingested sidecars relevant to its scope, classifies evidence, and writes only its assigned fragment directly under `outputs/00_state/standard_input_set/`. Do not create file handoffs for this task. Do not ask the human directly. Return a bounded in-context summary.

## Orchestrator responsibility after fan-out

After both input-analyzer instances complete, the orchestrator merges the two fragments into `outputs/00_state/standard_input_set/input_index.json` (deleting the fragments) and writes `input_set_evaluation_report.md` itself — findings, gaps, an Assumptions & open items section, and the readiness verdict. Keep it a short, well-structured markdown summary and never paste JSON bodies into it.

## Write discipline

- Append per document as the fragment grows. Do not accumulate the whole fragment in memory and write it in one giant call.
- Never emit JSON bodies in chat. The subagent's chat reply must be a compact status summary only.
- If the fragment cannot be produced, log the reason to `outputs/00_state/subagent_contract_failures.json` and return a bounded summary explaining what was produced versus skipped.

## Expected outputs by scope

- `scope=requirements`: `outputs/00_state/standard_input_set/input_index.requirements.json`
- `scope=sources`: `outputs/00_state/standard_input_set/input_index.sources.json`

The orchestrator merges the fragments into `input_index.json` and writes `input_set_evaluation_report.md` after both scopes complete.
