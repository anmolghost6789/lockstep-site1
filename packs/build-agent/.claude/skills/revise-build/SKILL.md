---
name: revise-build
description: >-
  Apply controlled remediation after evaluation — targeted revisions (<=3 tables) in the supervisor, broad revisions delegated per artifact family — and patch lineage.json for changed tables. Use when the user wants to fix, revise, remediate, correct, or rework generated build artifacts (DDL/DML/DQ/pipeline/tests) after evaluation.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Revise Build

## Prerequisites
- `/evaluate-build` completed

## Required reads (supervisor)
- `references/quality_standards.md`
- `references/evaluation_rubric.md`
- `references/remediation_and_packaging.md`
- `session.json` — summary fields only
- `evaluation/evaluation.json` — remediation items list (compact, typically < 20 KB)
- `phase_handoff.json` from prior phase

**Context discipline:** The supervisor reads the evaluation JSON for the remediation item list, then determines scope and delegates. It MUST NOT read the actual artifact files being revised. Those are read and rewritten by the artifact-writer sub-agent.

## Goal

Resolve evaluation findings with minimal context load. Targeted scope stays in supervisor (small and fast). Broad scope delegates to artifact-writer (isolates per-artifact-family work).

## Step 1 — Read remediation items and classify scope

Read `evaluation/evaluation.json::remediation_actions`. Classify automatically:

- **Targeted:** ≤ 3 tables affected AND no cross-cutting convention change
  - Supervisor handles inline — reads only the specific affected artifact files (not entire generated/ directory)
  - Maximum artifact files read: 3 tables × 4 families = 12 files, each typically < 30 KB
- **Broad:** > 3 tables affected OR a shared convention / cross-cutting pattern must change
  - Delegate to artifact-writer per artifact family

## Step 2 — Lock the revision set

Record in `revision_notes/revision_<N>.json`:
```json
{
  "revision_id": "N",
  "scope": "targeted | broad",
  "remediation_ids": [],
  "affected_tables": [],
  "affected_artifact_families": ["ddl", "dml", "dq", "pipeline", "tests_data", "tests_pipeline"],
  "convention_changes": [],
  "lineage_dirty": []
}
```

**Lineage dirty tracking**: populate `lineage_dirty[]` with the `table_id` of every table in `affected_tables`. This list is used by Step 5 to patch `lineage.json` after artifact revisions are complete.

For broad revisions, this file is written BEFORE delegation begins so sub-agents know exactly which tables and families to revise.

## Step 3A — Targeted revision (supervisor inline)

For each affected table × artifact family:
1. Read the specific artifact file from disk (one at a time — do not load all affected files simultaneously)
2. Apply the targeted fix per the remediation item
3. Write the revised artifact back via the `Write` tool
4. Re-read it immediately to confirm the fix is present (`test -f`, then spot-check key lines via `Grep`)

Maximum per-file read size: follow the same 30 KB rule — if an artifact file exceeds 30 KB, use `Grep` to locate and `Edit` to patch the specific section rather than reading and rewriting the full file.

## Step 3B — Broad revision (delegate to artifact-writer)

For each artifact family with affected tables:
1. Build a delegation prompt specifying:
   - The exact remediation items targeting this family
   - File paths of affected artifacts (to read and rewrite)
   - File paths of discovery artifacts needed as reference (canonical_build_model, effective_conventions, etc.) — paths only, not contents
   - The revision_notes file path (sub-agent reads the locked revision set)
   - Output paths (same paths — overwrite in place)
2. Spawn one `artifact-writer` per artifact family with affected tables (up to 4 concurrent: DDL, DML, DQ, tests)
3. Cache-warm if spawning 3+ agents: launch first alone, wait for first tool result, then launch rest in parallel

After all artifact-writers complete:
- Validate each revised artifact: `test -f`, `wc -c` — confirm non-empty
- Do NOT read revised content into supervisor — trust the filesystem checks and handoff summaries

## Step 4 — Targeted re-evaluation of affected scope

- **Targeted revision:** Re-evaluate only the affected tables. Pass their artifact paths to a `build-evaluator` sub-agent scoped to those tables.
- **Broad revision:** Spawn a full `build-evaluator` pass across all generated artifacts.

Maximum 2 revise-evaluate cycles per run. After 2 cycles with unresolved blockers, escalate to user with a summary of what is not converging and why. A third cycle requires explicit checkpoint approval.

## Step 5 — Lineage patch, sync, and checkpoint

### 5A — Lineage patch (before sync)

If `planning_summary.lineage_generated = true` AND `revision_notes/revision_<N>.json::lineage_dirty` is non-empty:

For each `table_id` in `lineage_dirty[]`:
1. Read the revised `<table_name>_plan.json` from `plans/` to get updated column mappings and transformation notes.
2. In `lineage.json`, find the matching entry in `tables[]` where `table_id` matches.
3. Rebuild that table's `column_lineage[]` entries from the revised plan data:
   - Update `source_tables`, `transformation`, `logical_type`, `confidence` from the revised plan
   - Set `lineage_source: "reconciled"` on all rebuilt entries
4. If load strategy changed: update `load_strategy` and `watermark_column` fields.
5. Update `lineage.generated_at` to current timestamp.
6. Write patched `lineage.json` back.
7. Set `session.json → planning_summary.lineage_reconciled = true`.

If `lineage_dirty` is empty OR `planning_summary.lineage_generated = false`: skip lineage patch.

**Pipeline stale notice**: if `generation_summary.pipeline_complete = true` AND lineage was patched, add to checkpoint:
> "⚠️ Lineage was patched for N tables. Pipeline artifacts may be stale. Re-run `/generate-pipeline` for affected tables if pipeline accuracy is critical."

### 5B — Sync and checkpoint

Update `revision_notes/revision_<N>.json` with outcomes. Sync revised artifacts and `lineage.json` (if patched) to `outputs/`. Update session.json. Write `phase_handoff.json`.

Present results: remediation items resolved, items waived, items still open, lineage patch summary (N tables patched or "no changes"). Recommend: another `/revise-build` cycle if unresolved items remain, otherwise the run is complete — run `/inspect-build` for a status summary.

Tell user: "Run `/compact focus on: run_id, phase status, user decisions, next steps` then run the recommended command."

## Required writes
- Updated artifact files in `state/run_id_<ID>/generated/` (written by supervisor inline or by sub-agents)
- `state/run_id_<ID>/plans/lineage.json` (patched in-place if lineage_dirty is non-empty)
- `state/run_id_<ID>/revision_notes/revision_<N>.json`
- `state/run_id_<ID>/phase_handoff.json`
- `state/run_id_<ID>/session.json`
- Synced copies in `outputs/`
