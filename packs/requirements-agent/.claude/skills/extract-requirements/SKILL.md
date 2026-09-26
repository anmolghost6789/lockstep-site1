---
name: extract-requirements
description: >-
  Create or incrementally update the linked Markdown requirements knowledge
  layer from accepted evidence while preserving coverage, relationships, and stable IDs.
---

# Extract requirements

This phase maintains knowledge; it does not author deliverables.

1. Plan once:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . plan-extract
   ```

   When `changed_sources` is empty, skip semantic delegation and render the
   no-op completion response from current committed state.

2. Delegate one cross-source `knowledge-curator` with exactly:

   `Full extraction only. Do not call Skill or Agent. Extract changed requirements for selected outputs <IDs> by following the knowledge-curator full-extraction instructions exactly.`

   The same curator owns cross-source synthesis, deduplication, stable IDs, and
   graph repair. It loads `references/knowledge_layer.md` and
   `references/evidence_rules.md`, reads changed evidence plus only impacted
   graph neighborhoods, writes canonical concepts and exception-only coverage,
   and runs the read-only `validate` preflight. Do not partition fresh sources
   across workers: independent source lanes duplicate semantic concepts and
   lose cross-source judgment even when their file writes are disjoint.

   Accept only a graph that passes the parent's independent read-only
   `validate` check. The preferred worker response is:

   `Knowledge authoring valid; parent must commit.`

   Ignore any worker-authored phase summary or commit claim. Run `validate`
   once; if it fails, resume the same curator in its warm context with only the compact exact
   validation lines. The curator repairs all listed defects together and reruns
   `validate`. Do not start a cold replacement, mapper, integrator, or a second
   repair round. If the warm repair still fails, stop with the remaining exact
   errors so a later targeted rerun can resolve them. Do not redirect validation
   output into scratch files.

3. Commit once and project progress:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . commit-extract
   python .claude/skills/requirements-agent/scripts/seed_progress.py --from-state --completed extract --next-command-name generate-deliverables --next-why "Generate selected deliverables from applicable linked knowledge."
   ```

Run `commit-extract` exactly once after the clean independent preflight. If it
returns validation errors, stop with the exact errors; do not reopen the repair
loop or retry the commit.
The parent does not rewrite semantic pages or create packets, fragments, plans,
or a duplicate graph.

Render the extraction result using
`requirements-agent/references/phase_completion.md`; then stop.
