---
name: start-run
description: >-
  Start or incrementally refresh a requirements run, select BRD/FRD/URS/Jira
  outputs, and update the existing structured input evaluation report.
---

# Start requirements run

Keep this as an explicit review checkpoint. Do not extract the complete semantic
model or auto-chain the next phase.

1. Ingest and plan once:

   ```bash
   python .claude/skills/requirements-agent/scripts/ingest_inputs.py --root . --quiet
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . plan-start
   ```

2. Resolve the complete selected-output set from `$ARGUMENTS` or existing state.
   Ask once only when neither provides it. Accept only BRD, FRD, URS, and JIRA.

3. If the plan reports a required report refresh, delegate one
   `knowledge-curator` with exactly:

   `Start mode only. Do not call Skill or Agent. Directly update the input evaluation for selected outputs <IDs> by following the knowledge-curator start-mode instructions exactly.`

   The parent does not read source content first or expand the prompt. The
   curator follows `references/input_model.md` and the input-report section of
   `references/report_grammar.md`, and updates only
   `outputs/01_input_evaluation/input_evaluation.md`.

4. Commit and project progress:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . commit-start --selected <ID> [--selected <ID> ...]
   python .claude/skills/requirements-agent/scripts/seed_progress.py --from-state --completed start --next-command-name extract-requirements --next-why "Normalize accepted evidence into the linked requirements knowledge layer."
   ```

If inputs, selection, and report format are unchanged, skip delegation and
commit the no-op checkpoint. Render the start result using
`requirements-agent/references/phase_completion.md`; then stop.
