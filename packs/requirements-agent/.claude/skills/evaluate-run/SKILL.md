---
name: evaluate-run
description: >-
  Evaluate selected requirements deliverables against the linked source and
  topic knowledge, write final quality artifacts, and update the existing evaluation.
---

# Evaluate requirements run

Always perform semantic evaluation; deterministic lint alone is insufficient.

1. Open an evaluation transaction:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py \
     --run-dir . prepare-evaluation
   ```

   This fails unless every selected deliverable is complete and returns the
   evaluation ID, exact source evidence paths and hashes, three content
   snapshot hashes, and pending output paths.
2. Delegate one `quality-reviewer`. It inherits all parent tools. The reviewer
   obtains the already-open receipt through the read-only `evaluation-context`
   command, then independently reads every source before trusting the knowledge
   graph, then evaluates the deliverables only against the validated knowledge.
   It writes the following three files under the returned `.pending/` paths:

   - `outputs/03_evaluation/.pending/evaluation_report.md`
   - `outputs/03_evaluation/.pending/quality_scores.json`
   - `outputs/03_evaluation/.pending/traceability.yaml`

   It must not edit the public evaluation files, write evaluation packets,
   cache lint JSON, or create a duplicate analysis graph.

   Use only this delegation prompt: `Evaluate the current run by following the
   quality-reviewer agent instructions exactly. Return its compact result.` Do not restate, expand, or override its rubric, ID conventions, graph policy,
   scoring policy, output schemas, or read strategy in the delegation prompt;
   the agent definition is the single evaluation authority.
3. Commit the transaction, then update progress. Commit rejects a stale or
   inconsistent bundle and preserves the last public evaluation on failure:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . \
     commit-evaluation
   python .claude/skills/requirements-agent/scripts/seed_progress.py \
     --from-state --completed evaluate
   ```

   If commit reports a reviewer schema error, resume that same reviewer once
   with the exact error and retry. Do not inspect the script or hand-edit the
   reviewer's pending artifacts.

Render the evaluation result using
`requirements-agent/references/phase_completion.md`; then stop.
