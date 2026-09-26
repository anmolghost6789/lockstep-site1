# Phases and checkpoints

## The phase sequence

```text
/start-design-run
  -> evaluate inputs, snapshot evidence, select sources, report gaps
/design-architecture
  -> state mappings, DQ rules, target architecture, lineage, and plan
/generate-artifacts
  -> generate workbook and ER outputs from the canonical design facts
/evaluate-design
  -> verify artifacts, capture governed learnings, close the run
```

Each command is a phase boundary. The agent writes state at phase start and completion,
gives a concise summary, recommends the next command, and stops. **The workflow does not
auto-chain**: the user invoking the next command is the approval to proceed — there is no
separate approval prompt or gate presentation at a phase boundary. If the user asks for
changes instead, the change is routed to the earliest phase that owns the decision (see
[Revisions and recovery](revisions-and-recovery.md)) rather than patched in place.

## Phase-by-phase detail

### `/start-design-run`

One continuous phase from raw inputs to a decided source universe:

1. Applies the empty-input guard — if no meaningful input exists under `inputs/<category>/`
   (ignoring `README.md`, `.gitkeep`, `.keep`, `.DS_Store`), it explains where to place
   files and stops without creating run files.
2. Hashes inputs and warns if they are identical to a previously completed run's inputs,
   requiring explicit confirmation before proceeding.
3. Snapshots `inputs/` and `context/guidance/`, then ingests every file into UTF-8 sidecars.
4. Publishes a thin `input_index.json` plus `input_set_evaluation_report.md` — the
   readiness assessment with gaps and a verdict.
5. **Conditional pause** — if the readiness verdict is error-grade (blocking gaps), the
   phase stops and asks the user to add or confirm missing evidence. Any other verdict
   (pass or warn-grade) does not pause; the phase continues into source discovery in the
   same turn.
6. Selects and gap-checks sources into `source_decisions.json` (one record per candidate
   source entity, `status: selected | rejected | missing`) plus `source_gap_report.md`.

### `/design-architecture`

The principal review gate. Designs the target architecture, target data model,
transformations, lineage, and DQ rules using **only** sources marked `status: "selected"`
in `source_decisions.json` (plus explicit waivers):

1. Scaffolds `column_mappings.json` and `dq_rules_design.json`.
2. Enters a per-table append loop — for every planned target table, in layer order
   (L0 -> L1 -> L2), it designs grain, surrogate-key strategy, columns, and DQ rules, then
   appends them to the two canonical JSON files (never rewriting the whole file).
3. Renders `target_model_design.md` once, via `render_design_md.py`, for human review —
   this file is a derived view and must never be hand-edited.
4. Writes `design_brief.md` (business framing, key decisions, open questions).
5. Runs `build_plan.py` to compute `plan.json` — the dependency-safe generation plan
   (waves, file plan, validation controls), derived mechanically from the design JSONs.

#### Design facts before files

The core design is stored as canonical facts — column mappings and DQ rules — not as
several independently edited workbook views. Deterministic renderers and generators create
the review markdown, workbooks, and diagrams from those facts. If an output is wrong,
correct the stated design fact and regenerate; do not manually patch multiple derived
artifacts until they disagree. This is why `/design-architecture` is the principal review
gate: the generator should render an approved design, not create a different design during
a spreadsheet export.

### `/generate-artifacts`

Generates STTM, data model, DQ, and ER diagram workbooks from the approved design and
execution plan by invoking the shipped canonical generator
(`.claude/skills/design-agent/scripts/generate_workbooks.py`) — no phase ever writes a new
Excel generation script during a run. After generation, `verify_workbook_headers.py` checks
every generated workbook against its canonical template; any mismatch is fatal for the
phase.

### `/evaluate-design`

The final phase; there is no separate close phase.

1. Runs deterministic checks first: `verify_workbook_headers.py` and
   `verify_artifact_semantics.py` (DQ SQL parse validity, ER Mermaid column drift, encoding
   corruption).
2. Always spawns the `design-evaluator` subagent, which scores business alignment,
   architecture quality, mapping quality, DQ quality, lineage quality, source
   faithfulness, over/under-engineering, and standards conformance. Any category whose
   deterministic check fails is capped at 6/10 regardless of narrative quality.
3. Writes `evaluation_report.md` and `evaluation_scores.json` with a recommendation of
   `APPROVE`, `APPROVE_WITH_NOTES`, or `NEEDS_REVISION`.
4. **Closure tail** (only when the recommendation is `APPROVE` or `APPROVE_WITH_NOTES`):
   captures governed learnings into `memory/`, resolves the reference-store inclusion
   decision (only if `context/reference/` exists), cleans
   `outputs/00_state/runtime_scratch/`, and marks the run `completed`.

If the recommendation is `NEEDS_REVISION`, the report lists concrete fixes and the phase to
revise; the run stays open and the closure tail does not run.

## Review points before Build

1. Confirm the selected sources and source grain are correct.
2. Review mappings for every target column, including derivation, joins, filters, and
   source references.
3. Confirm layer ordering and same-layer dependencies are either absent, sub-layered, or
   formally waived.
4. Confirm each DQ rule has a clear rule, scope, and source-backed reference.
5. Open the generated STTM and data model workbooks; do not review only the summary
   markdown.
6. Run `/evaluate-design` and resolve material findings before Build uses the artifacts.

## Next

See [Inputs and outputs](inputs-and-outputs.md) for the full folder contract, or
[Revisions and recovery](revisions-and-recovery.md) for how to route a change request.
