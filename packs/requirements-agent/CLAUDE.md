# Requirements Agent

Use the run filesystem as the source of truth. Produce only the selected BRD,
FRD, URS, and Jira Story Pack outputs.

Use progressive disclosure: load the active phase skill first, then only the
references and knowledge routes required for the current transaction.

## Workflow

Keep each slash command as an explicit checkpoint:

```text
/start-run -> /extract-requirements -> /generate-* or /generate-deliverables
           -> /evaluate-run -> optional /publish-to-jira
```

Do not auto-chain phases. Complete the invoked command, update state and
`progress.json` through the package scripts, recommend the next command, and
stop. Warn before accepting a request that bypasses the workflow; proceed only
when the user explicitly confirms the exception.

After every phase reaches a committed, no-op, or blocked result, read
`.claude/skills/requirements-agent/references/phase_completion.md` and render
its user-facing completion response. Do not expose raw worker output as the
phase summary.

## Always-on rules

- Read `.claude/skills/requirements-agent/references/INDEX.md`, then load only
  the references named for the active phase.
- Run `ingest_inputs.py` before reading binary evidence. Read prepared text from
  `inputs_manifest.json`; do not improvise binary parsing.
- Start graph traversal at `outputs/00_state/knowledge/index.md`. Retrieve only
  applicable concepts and a bounded typed neighborhood.
- Treat raw sources as extraction and evidence-repair inputs, not normal
  generation context.
- Preserve exact source facts, stable IDs, evidence, contradictions,
  assumptions, and insufficient-input markers.
- Treat run-local templates as authoritative. Package templates are defaults,
  not fixed schemas.
- Let model agents author semantic Markdown. Let `knowledge_layer.py` own
  hashes, state, graph validation, impact analysis, and atomic transactions.
- Use `RA-BLOCK` ownership for targeted document updates. Preserve unrelated
  blocks and stop on manual-edit conflicts.
- Keep private state in `outputs/00_state/`. Use the public paths declared in
  `workflow_manifest.json`; do not infer numbered folders.
- Use UTF-8 and read before editing.

## Workers

Delegate semantic extraction and input evaluation to `knowledge-curator`, one
document to each `deliverable-author`, and independent evaluation to
`quality-reviewer`. Workers inherit the parent tool set. Give them only the
compact prompt defined by the active phase skill; their agent definitions and
phase-selected references own the detailed procedure.
