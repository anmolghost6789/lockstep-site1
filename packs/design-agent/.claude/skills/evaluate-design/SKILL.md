---
name: evaluate-design
description: >-
  Evaluate generated design artifacts with deterministic checks and semantic scoring, then close the run: capture governed learnings, resolve the reference-store decision, clean runtime scratch, and mark the run completed.
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
  - Bash(python3:*)
  - Bash(python:*)
  - Bash(py:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# Evaluate Design (Evaluate & Close)

Purpose: run one evaluation pass that combines deterministic validation and semantic quality scoring, then close the run — capture governed learnings, resolve the reference-store decision, clean runtime scratch, and mark the run completed. This is the final phase; there is no separate close phase.

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

## Evaluation steps

1. **Run deterministic semantic checks FIRST** (before delegating to design-evaluator). These are pure Python; the model does not need to read every workbook cell to know if SQL is valid, ER diagrams drifted, or encoding is corrupt:
   ```
   python .claude/skills/design-agent/scripts/verify_workbook_headers.py \
     --artifacts-dir outputs/05_artifacts \
     --report outputs/00_state/evaluation/header_check.json

   python .claude/skills/design-agent/scripts/verify_artifact_semantics.py \
     --artifacts-dir outputs/05_artifacts \
     --design-dir outputs/00_state/design \
     --report outputs/00_state/evaluation/semantic_check.json
   ```
   Both reports are inputs to the evaluator. Non-zero exit is not fatal for this phase (we want a full evaluation even when there are defects), but any failure MUST be surfaced in the final report and the recommendation MUST NOT be `APPROVE` while `semantic_check.json.passed == false`. Exit code 2 means the script could not run — usually missing dependencies (`openpyxl`, `sqlglot`); install them with `pip install -r .claude/skills/design-agent/scripts/requirements.txt` and rerun (the pod runtime ships them via `playground/backend/requirements.txt`).
2. Delegate to design-evaluator — **always spawn it for this phase**. The evaluator reads artifacts from disk, ingests the two reports above, and returns a bounded summary in context.
3. Check file count, sheet count, references, selected-source usage, layer reconciliation, template residue, and empty/dummy content.
4. Score business alignment, architecture quality, mapping quality, DQ quality, lineage quality, source faithfulness, over/under-engineering, and standards conformance. Standards conformance asks: does the design correctly apply the naming conventions (naming-conventions.md), layering rules (layering-logic.md), and DQ patterns (dq-patterns.md) it invokes — not just get the business facts right, but follow the house rules for using them? Any category that includes deterministic-check failures (DQ SQL parse failures, ER Mermaid column drift, encoding corruption, naming/layering/DQ-pattern convention violations) must cap that category's score at 6 regardless of narrative quality.
5. Write evaluation_report.md and evaluation_scores.json under outputs/00_state/evaluation/, rendering evaluation_report.md per references/report_grammar.md (output evaluation report spine §5) using references/OUTPUT_EVALUATION_REPORT.template.md. The report MUST include a top-level "Deterministic checks" section that summarizes `header_check.json` and `semantic_check.json` counts and links to the raw JSONs. Recommendation options:
   - `APPROVE` — only if both deterministic checks are green AND overall score ≥ 8.
   - `APPROVE_WITH_NOTES` — deterministic checks green, minor scoring notes only.
   - `NEEDS_REVISION` — any deterministic check failure OR any category score < 7. The report must list the concrete fixes and the phase/file to revise (e.g., "regenerate `outputs/00_state/design/dq_rules_design.json` for tables X, Y — expression contains leading `WHERE`, then re-render and regenerate the affected layers").
6. Publish `outputs/06_evaluation/`.

### Three lenses

Every scored dimension (step 4) answers one of three questions. Naming the
lens makes the coverage explicit instead of implicit — nothing added, just
labeled:

| Lens | Dimensions | Question answered |
|---|---|---|
| Input → output fidelity | Business alignment, Mapping quality, Source faithfulness | Does the design correctly and completely reflect the business rules, KPIs/KBQs, and context it was derived from — no invented sources, no dropped mappings, no drifted meaning? |
| Output sufficiency | Architecture quality, DQ quality, Lineage quality, Over/under-engineering | Read on its own, is the design artifact (data model, ER diagram, DQ rules) structurally complete, internally consistent, and appropriately scoped for downstream Build consumption? |
| Best-practice / standards conformance | Standards conformance | Does the design correctly apply the naming conventions (naming-conventions.md), layering rules (layering-logic.md), and DQ patterns (dq-patterns.md) it invokes — the house rules for using facts, not just the facts themselves? |

There is no fixed equal-weighting statement in this rubric (the scorecard's
`Weight` column is set per run). What holds each lens to account instead is
the deterministic-check cap in step 4: `dq_quality`, `lineage_quality`,
`source_faithfulness`, and `standards_conformance` are hard-capped at 6
whenever the paired deterministic check fails, regardless of narrative
strength — so a strong score in one lens (e.g. architecture quality) can
never mask a hard defect surfaced in another (e.g. source faithfulness or
standards conformance).

If the recommendation is `NEEDS_REVISION`, surface the fixes, recommend the phase to revise, and stop — do NOT run the closure tail below; the run stays open and is not complete. Re-run /evaluate-design after remediation.

## Closure tail (runs only when the evaluation recommendation is APPROVE or APPROVE_WITH_NOTES)

7. **Capture governed learnings.** Promote reusable process learnings into the top-level `memory/` markdown store — only safe, generic, non-confidential operational lessons about using this package. Conventions go into `memory/CONVENTIONS.md`, durable decisions into `memory/DECISIONS.md`, reusable patterns into `memory/PATTERN_LIBRARY.md`, other durable facts into `memory/MEMORY.md`. **Governance rule (hard):** learnings capture generalized patterns only — NO client names, client system names, dataset/table/column identifiers, file contents, PII/PHI, or unapproved business rules. If a learning cannot be stated without a client-specific identifier, generalize it or drop it.
8. **Reference-store inclusion decision — only if `context/reference/` exists.** If the folder exists, ask the human whether current-run material should be added to the governed reference store, using AskUserQuestion (primary) with options YES / NO / SELECTIVE and the yellow typed fallback when structured UI is unavailable. Set `waiting_for_user` + `awaiting_user_action = "reference_store_decision"` before asking; this decision is always explicit and is never auto-approved. If `context/reference/` does NOT exist, auto-skip the question and add one line to the final reply: "Reference store not configured — inclusion question skipped." On YES/SELECTIVE, deposit only the approved material under `context/reference/raw/` with governance defaults from `config/project_config.json`.
9. **Clean runtime scratch.** Delete `outputs/00_state/runtime_scratch/` if it exists (per CLAUDE.md principle 7 — runtime hygiene). Do NOT touch `inputs/`, do NOT touch snapshots, do NOT touch any other agent-internal state.
10. **Mark the run completed.** Set `outputs/00_state/run_state.json` `run_status`/`status` to `completed` and perform the mandatory final run-root `progress.json` rewrite (this is the phase-completion bookkeeping write — the evaluation and closure updates fold into it). Report completion with links to `outputs/`, and stop. There is no next command.

## End Of Turn
This is the final phase. If the evaluation recommendation is APPROVE or APPROVE_WITH_NOTES, the closure tail above has already marked the run completed — report that the design run is evaluated and closed, with links to `outputs/`. If the recommendation is NEEDS_REVISION, report the concrete fixes and recommend the phase to revise; the run stays open and the closure tail does not execute. Stop either way. Do not auto-invoke any skill.

Additional context from user invocation: $ARGUMENTS
