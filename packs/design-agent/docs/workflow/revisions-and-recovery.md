# Revisions and recovery

## Revising a design decision

Because the design is stored once as canonical facts (`column_mappings.json`,
`dq_rules_design.json`), a revision always means: **fix the stated fact at its owning
phase, then let downstream phases regenerate.** Never hand-patch a workbook, the rendered
`target_model_design.md`, or `plan.json` directly — they are derived views and the next
regeneration would overwrite an undocumented manual fix anyway.

When a reviewer requests a change, the change is routed to the earliest phase that owns
that decision, and every phase downstream of it is re-run to keep artifacts consistent:

| Change type | Examples | Earliest phase to re-run | Downstream work required |
|---|---|---|---|
| Cosmetic/output formatting only | Column widths, labels, a comment typo with no design meaning. | `/generate-artifacts` | Regenerate affected outputs, then re-run `/evaluate-design`. |
| Output population bug | Missing `References`, wrong row order, generated value not matching approved design. | `/generate-artifacts` | Regenerate affected artifacts, then re-run `/evaluate-design`. |
| Execution plan / file structure | Add/remove a planned workbook, wrong layer file list, dependency-order issue. | `/design-architecture` (plan step) | Re-run the planner, then `/generate-artifacts`, `/evaluate-design`. |
| Architecture/design change | Add/remove a table or column, change grain, PK/FK, a mapping, a transformation, a DQ rule, a layer assignment. | `/design-architecture` | Re-run design + plan, then `/generate-artifacts`, `/evaluate-design`. |
| Source selection change | Use a different source, add a missing source, reject a previously selected source. | `/start-design-run` (source-discovery step) | Re-run source decisions, then `/design-architecture`, `/generate-artifacts`, `/evaluate-design`. |
| Standard input change | New/changed BRD, source inventory, KPI formula, business rule, context-hierarchy decision, user instruction. | `/start-design-run` | Re-ingest/re-index the updated evidence, then re-run downstream phases as needed. |

Bulk feedback is collected as one batch when possible — several small changes can combine
into a deeper rollback need than any single item suggests on its own.

## Resuming via `/status`

Run `/status` any time you are unsure what state a run is in. It reads
`outputs/00_state/run_state.json` (never advancing a stage) and reports:

- run ID, current stage, and `run_status` (`not_started | in_progress | waiting_for_user |
  changes_requested | rerun_required | completed | cancelled | error`);
- `awaiting_user_action`, if a phase is paused on a human decision;
- stage history, links to generated artifacts, and the recommended next command.

## Idempotent re-entry (safe resume rules)

Every phase detects existing valid artifacts on re-invocation and continues from the first
missing or stale step — it never blindly restarts:

- **`/start-design-run`** — skips the snapshot/ingest step if `inputs/` has not changed
  since the last snapshot; skips source discovery if `source_decisions.json` and
  `source_gap_report.md` already exist and are current.
- **`/design-architecture`** — re-reads `column_mappings.json`, identifies which tables are
  already fully written, and continues the per-table loop from the next planned table.
  Re-runs the renderer only if `target_model_design.md` is missing or older than either
  canonical JSON. Re-runs the planner only if a design JSON changed after `plan.json` was
  last computed.
- **`/generate-artifacts`** — regenerates only per-layer workbooks that are missing,
  corrupt (below a 5 KB size threshold), or stale (their design source was modified after
  the workbook was written). Always re-runs the header verifier regardless of which layers
  were regenerated.

A 32k output-token error mid-phase is treated as a phase execution failure, not data loss —
recovery resumes from the files already on disk.

## Safe recovery table

| Situation | Safe response |
|---|---|
| Input readiness is blocking. | Add the missing requirements or source evidence; do not start architecture on a guessed source set. |
| A source was rejected or a gap is reported. | Resolve it in the source decision or record a waiver before design. |
| Generated workbook looks wrong. | Check the canonical mapping/DQ fact and re-run the generator — do not hand-edit the workbook. |
| A run was interrupted. | Run `/status` and inspect `outputs/00_state/run_state.json`; do not delete outputs. |
| A design fact changes after review. | Re-enter the affected phase, regenerate affected artifacts, and re-evaluate. |
| Inputs are identical to a previously completed run. | `/start-design-run` warns and requires explicit confirmation before starting a duplicate run — replace the inputs or confirm intentionally. |
| A lower context tier conflicts with a higher one (e.g. a user instruction contradicts project context). | The agent asks for explicit confirmation before applying the override; it never silently overrides a higher tier. |

## Cancelling a run

`/cancel` asks for confirmation (`AskUserQuestion`, with a typed fallback), then, only if
confirmed:

- preserves `outputs/` (deliverables and agent state under `outputs/00_state/`) in full;
- clears user-provided files from `inputs/` while preserving every `README.md` file and the
  category folder scaffold, and removes `inputs/midrun_uploads/` if present;
- writes `outputs/00_state/logs/input_cleanup_report.json`.

If not confirmed, the run returns to its prior stage/status with no change.

## Next

See [Command reference](../how-to-run/command-reference.md) for the exact command syntax,
or [Troubleshooting FAQ](../reference/troubleshooting-faq.md) for specific error scenarios.
