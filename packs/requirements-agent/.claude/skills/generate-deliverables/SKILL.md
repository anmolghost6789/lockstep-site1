---
name: generate-deliverables
description: >-
  Generate or target-update all dirty selected requirements deliverables from
  applicable linked knowledge and each run's authoritative templates.
---

# Generate selected deliverables

1. Prepare all selected outputs once:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . prepare-generation --selected
   ```

   Resolve ambiguous run-local templates by reading their content and rerunning
   only that deliverable with `--template <path>`. Never substitute the package
   default for an uploaded template.

2. Omit `no_op` outputs and stop on manual-edit conflicts. In one parallel
   fan-out, delegate one `deliverable-author` per remaining output with exactly:

   `Author <ID> from its prepared transaction. Follow the deliverable-author agent instructions exactly.`

   Each author loads the dynamic template, `references/document_authoring.md`,
   and only the output-specific reference named there. Do not paste receipts,
   graph content, templates, or quality rules into the delegation prompt.

   Retain every author agent ID and wait for each `Agent` call's terminal
   result. A quiet interval is normal while a model composes a large document;
   do not poll, schedule wakeups, or send a resume merely because no intermediate
   event was emitted. Only after an explicit API/transport failure, send one
   compact `SendMessage` to that same warm author:

   `Resume <ID> from its prepared transaction. Reuse context already loaded; write the pending document and run the required checks.`

   Send all required warm resumes in the same assistant turn so recovery stays
   parallel. A completion from one author must not serialize or delay another
   still-active author. Never interrupt a healthy author with status or resume
   messages.

   Do not launch a cold replacement. Allow one warm resume per output; if it
   fails or goes silent again, stop with that output's exact failure instead of
   waiting or retrying indefinitely.

3. After all authors pass their local checks, validate and commit the complete
   batch serially:

   ```bash
   python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . finalize-generation
   python .claude/skills/requirements-agent/scripts/seed_progress.py --from-state --run-dir .
   ```

Render the generation result using
`requirements-agent/references/phase_completion.md`; then stop.
