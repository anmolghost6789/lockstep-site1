---
name: design-architecture
description: >-
  Produce the target architecture, target model, lineage, mappings, and DQ design from selected sources, then compute the dependency-safe generation plan (plan.json) in the same phase.
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
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# Design Architecture

Purpose: design the target architecture, target data model, transformations, lineage, and DQ rules using selected sources only, then turn that design into a dependency-safe generation plan — computed by script, reviewed by the model.

This phase is file-first and chat-light, and it is **JSON-as-source**: the model states each design fact exactly once, in `column_mappings.json` and `dq_rules_design.json`; every human-readable view is produced by a script. The model never types the same column twice. It uses a **strict per-table append loop** so no single tool call can breach the 32,000 output-token cap and so context grows linearly (not multiplicatively) as tables are designed.

## Required Reads
- CLAUDE.md
- config/project_config.json
- .claude/skills/design-agent/SKILL.md
- outputs/00_state/run_state.json when continuing an existing run

## Rules
- Run only this phase.
- Stop at the phase boundary and return control to the user.
- Do not auto-invoke the next slash skill, even if the user previously asked to do everything.
- Update outputs/00_state/run_state.json and root progress.json at most twice per phase: once at phase start and once at phase completion (fold human-wait status into those two writes). The phase-completion rewrite of root progress.json is MANDATORY before the final reply of the phase. See CLAUDE.md principle 14. (Per-table telemetry appends are the documented exception.)
- Keep chat concise; summarize and link to files rather than pasting report or artifact bodies.

## Idempotent re-entry

When this skill is invoked again for a run whose design already started (resume after a stream/timeout failure or a repeated command), do NOT restart from scratch. Detect what already exists and is valid, skip it, and continue from the first missing or stale step:

- `outputs/00_state/design/column_mappings.json` exists and is valid JSON → re-read it, list which tables are already present in its `tables` array, and continue the per-table loop with the next planned table. Do not restart tables that are already fully written (metadata + mappings + DQ rules present).
- Every planned table is present → skip the loop; re-run the renderer only if `target_model_design.md` is missing or older than either canonical JSON.
- `design_brief.md` present and current → keep it; otherwise (re)write it.
- `outputs/00_state/execution_plan/plan.json` present and newer than both canonical JSONs → the plan is current; go straight to publish + phase-completion bookkeeping. If a design JSON changed after the plan was computed, the plan is stale — re-run the planner.

## Canonical artifacts (model-written) vs rendered views (script-written)

| File | Written by | Role |
|---|---|---|
| `outputs/00_state/design/column_mappings.json` | model (per-table Edits) | CANONICAL: layers, per-table metadata, one entry per column |
| `outputs/00_state/design/dq_rules_design.json` | model (per-table Edits) | CANONICAL: one entry per DQ rule |
| `outputs/00_state/design/target_model_design.md` | `scripts/render_design_md.py` | RENDERED VIEW for human review — never hand-written, never hand-edited |
| `outputs/00_state/design/design_brief.md` | model (once, at the end) | Genuine judgment prose: business framing, key decisions, open questions |
| `outputs/00_state/execution_plan/plan.json` | `scripts/build_plan.py` | COMPUTED plan: waves, file plan, validation controls (+ model `notes` only for genuine judgment) |

## Part A — Design the target model (per-table append loop)

1. Read the Standard Input Set (`input_index.json` + the sidecar sections it points to), `source_discovery/source_decisions.json` (design only from `status: "selected"` entries plus explicit waivers), current context, governed reference patterns, and run state.
2. Design the layer architecture and target model top-down from business needs. Think through grain, SK strategy, and business rules for each table before writing anything.
3. Scaffold two empty files (one `Write` call each) under `outputs/00_state/design/`:
   - `column_mappings.json` (opens with `{"layers": [], "tables": [], "mappings": []}` — the trailing `]}` anchors per-table Edits). Immediately after scaffolding, `Edit` in the `layers` entries once: one `{"id", "title", "schema", "database"}` per layer.
   - `dq_rules_design.json` (opens with `{"rules": []}`)
4. Enter the **per-table append loop**. For each planned target table, in the order Layer 0 → Layer 1 → Layer 2 — at most 2 artifact Edits per table plus the DQ Edit and the telemetry bump:
   1. Design the one table in thinking: grain, SK strategy, columns, business purpose, AND DQ rules (see step 4.4 for the coverage minimum). Do not narrate this in chat.
   2. `Edit` `column_mappings.json`: insert this table's metadata entry into the `"tables"` array — `{"layer", "table", "purpose", "grain", "key_strategy", "table_type", "load_strategy", "frequency", "schema", "database"}` (schema/database may be omitted when they equal the layer's).
   3. `Edit` `column_mappings.json`: insert this table's column entries into the `"mappings"` array (append before the closing `]}`). One entry per column. This is the ONLY place a column is ever typed. (Steps 4.2 and 4.3 may be combined into a single Edit when the table is small; never more than 2 Edits to `column_mappings.json` per table.)
   4. `Edit` `dq_rules_design.json`: insert this table's DQ rule entries into the `"rules"` array. **This step is mandatory for every table.** Per R6, every table must have at least one rule entry. Skipping this step or writing zero entries is a phase failure. Common per-type minimums are in R6 below; if a table genuinely has no applicable checks after honest assessment, use the `NO_DQ_APPLICABLE` escape valve with a concrete per-table reason.
   5. `Edit` `progress.json`: bump the design phase table count and set `design.last_table_completed` to this table with an ISO timestamp. This is the per-table telemetry the operator uses to see live progress.
   6. Move to the next table. Assistant reply body ≤ 100 words per table (in most cases, no reply body between Edits — just proceed).
5. After every planned table is written, render the review markdown ONCE:
   ```
   python .claude/skills/design-agent/scripts/render_design_md.py \
     --design-dir outputs/00_state/design
   ```
   This produces `target_model_design.md` (per-layer sections, per-table metadata lines, column tables, DQ rule tables) for human review. If the review reveals a defect, fix the JSONs (per-entity Edit) and re-run the renderer — never patch the markdown.
6. Write `design_brief.md` once. Keep it short: business framing, layers, table counts per layer, key decisions, open questions. Link to the artifact files. Do NOT paste artifact bodies or repeat per-column facts.
7. Confirm `progress.json.design.tables_completed_total == tables_planned_total` before moving to Part B.

## Part B — Compute the execution plan

The plan is mechanical: generation waves are a topological sort of the FK/semantic relationships already declared in `column_mappings.json` (`join_conditions` cells), and output paths are formulas over the layer list. The model does not type these facts; it runs the shipped planner and adds judgment only where judgment exists.

8. Run the canonical planner:
   ```
   python .claude/skills/design-agent/scripts/build_plan.py \
     --design-dir outputs/00_state/design \
     --out outputs/00_state/execution_plan/plan.json
   ```
   `plan.json` contains: per-layer generation waves with `parallel_group` values (independent tables share a group; dependents land in later groups), automatic sub-wave splits when a layer exceeds 15 tables, the `file_plan` block (`STTM_{layer}.xlsx`, `DATA_MODEL_{layer}.xlsx`, `DQ_{layer}.xlsx`, `ER_DIAGRAM_{layer}.md` per layer plus `ER_DIAGRAM.xlsx` and `ER_DIAGRAM_LINEAGE.md`), delegation flags, and the validation-control list. It replaces the retired hand-written plan.md / file_plan.json / generation_order.json trio.
9. Review `plan.json`. Add a `notes` entry ONLY for genuine judgment: same-layer dependency waivers, unusual dependency handling, risky volumes, sub-wave rationale beyond the automatic split. For a routine run, an empty `notes` array is correct. If the computed plan is wrong, the design JSONs are wrong — fix them (per-entity Edit + re-render) and re-run the planner; never hand-edit computed waves or the file plan.
10. Optional: write a hand-written `plan.md` ONLY when the run has genuine multi-layer complexity worth narrating (e.g., documented same-layer waivers, cross-wave sequencing constraints a reviewer must understand). Routine runs skip it.
11. Same-layer physical transformation dependencies still require sub-layering or a documented waiver (recorded in `notes`).

ER markdown requirement carried into generation: ER files contain fenced Mermaid blocks so they render in Markdown viewers and can be copied directly into Mermaid tools; the shipped generator derives them from `column_mappings.json`.

## Phase completion

12. Publish to `outputs/03_design/` (design_brief.md, target_model_design.md, column_mappings.json, dq_rules_design.json) and `outputs/04_plan/` (plan.json, plus plan.md if written).
13. Perform the mandatory phase-completion bookkeeping write: update outputs/00_state/run_state.json and rewrite the run-root progress.json (step `design-architecture` done, `next` = /generate-artifacts).

## Why JSON is the source and markdown is the view

The alternative (model writes the markdown, a parser reconstructs the JSON) was evaluated and rejected: parsing model-written markdown reintroduces a fragile contract (heading regexes, table alignment, silent drops on format drift) exactly where precision matters most, and it makes the model restate every column twice (markdown table + JSON entry) or makes the JSON hostage to a parser. Writing the JSON once and rendering the markdown deterministically gives the generator, the planner, and the verifier a single machine-readable source of truth, and the human still gets a readable review document — produced by `render_design_md.py`, not by model tokens.

## Why single files, not per-layer chunks

Per-layer chunk files (`column_mappings_L0.json`, `_L1.json`, `_L2.json`) proved slower and less reliable in practice: they required either a merge step or per-layer subagents, both of which multiplied context and startup overhead. Keeping one file per artifact and appending per table gives the same token safety at a fraction of the wall-clock cost. The `layer` field inside each JSON entry preserves the layer distinction that the per-layer split was trying to give.

## Mandatory rules (violations fail /evaluate-design)

### R1 - Column completeness

For every target table declared in the `"tables"` array of `column_mappings.json`, the `"mappings"` array must contain an explicit entry per column. The following column-name patterns are forbidden and must never appear:

- `ADDITIONAL_*`
- `PLACEHOLDER_*`
- `REMAINING_*`
- `TBD`, `TO_BE_DEFINED`, `TO_BE_DETERMINED`
- Any name ending in `_columns` when used as a bulk placeholder

### R2 - DQ Rule Expression required

Every entry in `dq_rules_design.json` must populate `dq_rule_expression`:

- If the check type matches a template in `knowledge/dq-patterns.md` (NOT_NULL, UNIQUENESS, FK_INTEGRITY, RANGE, REGEX_MATCH, etc.), populate with the predicate from the template, substituting column/table names. The catalog expressions are bare boolean predicates by design — never re-add `SELECT`/`WHERE` scaffolding around them (see R8).
- If it is a custom business rule not in the template library, populate with `[NEEDS_HUMAN_REVIEW]` and add `dq_rule_expression_reason`.
- Blank is never acceptable.

### R6 - DQ coverage floor per table (active check during per-table loop)

Every target table in `column_mappings.json` must have **at least one entry** in `dq_rules_design.json`. Recommended minimum is 2 rules per table. During the per-table loop, when you finish designing a table, actively assess DQ before moving on:

- **Dimension (d_*)**: at least PK not-null OR PK uniqueness. Prefer both.
- **Fact (f_*)**: at least one grain-safety rule (PK not-null or SK uniqueness) AND at least one FK integrity check when FKs exist.
- **Ref (ref_*)**: at least PK not-null.
- **Staging / Conformed (L1)**: at least one source-completeness rule (row-count > 0 or mandatory-source-key not-null).
- **Raw (L0)**: at least one load-completeness rule (row-count > 0 or business-key not-null).

**Escape valve for genuinely-no-DQ tables.** If, after honest assessment, a table has zero applicable checks (e.g., a pure lookup/reference table that carries no substantive data; a passthrough view; a scratch table), write ONE entry in `dq_rules_design.json` with:

```json
{
  "layer": "...",
  "target_table": "...",
  "target_column": "-",
  "rule_id": "DQ_{layer}_{table}_NO_DQ",
  "rule_type": "NO_DQ_APPLICABLE",
  "severity": "INFO",
  "dq_rule_expression": "[NO_DQ_APPLICABLE]",
  "dq_rule_expression_reason": "concrete explanation grounded in this table's design (e.g., 'ref_market_definition is a governance-managed lookup with two rows; upstream steward review is the control')",
  "threshold_value": "-",
  "threshold_value_reason": "not applicable; NO_DQ_APPLICABLE marker",
  "source_reference": "column_mappings.json > tables > {table}"
}
```

Blanket phrases like "not applicable", "not needed", "handled upstream", or "downstream layers inherit" are NOT acceptable reasons. The reason must reference this specific table's grain, purpose, or design property that makes DQ inapplicable. If you cannot write a concrete reason, the table needs real DQ rules — do not use the escape valve to skip work.

### R7 - Threshold Value required

Every entry in `dq_rules_design.json` (except NO_DQ_APPLICABLE entries) must populate `threshold_value`. A DQ rule without a threshold is documentation, not an executable check.

- Numeric thresholds preferred: `0` (zero nulls / duplicates / out-of-range), `1` (at least one row), `95` (≥95% pass rate), etc.
- Threshold expressions allowed: e.g., `< 1%`, `>= 99%`, `<= 24h`.
- For custom rules where the threshold is a business decision the design cannot infer, use `[NEEDS_HUMAN_REVIEW]` and add `threshold_value_reason`.
- Blank is never acceptable.

### R8 - dq_rule_expression must be a bare boolean predicate

Every `dq_rule_expression` value must be a **bare boolean predicate** — the condition that would live inside a `WHERE` clause. Do NOT include a leading `WHERE`, `SELECT`, `FROM`, `HAVING`, or any other SQL keyword that positions the predicate. The workbook DQ cell carries this bare predicate **verbatim** — the generator never prefixes `WHERE`. The wrapping happens downstream: the verifier (and the DQ runtime) compose `SELECT 1 FROM {table} WHERE ({filter_conditions}) AND ({dq_rule_expression})` around the cell value.

```
Correct:   "dq_rule_expression": "BUSINESS_PARTNER_ID IS NULL"
Correct:   "dq_rule_expression": "EFFECTIVE_END_DT IS NOT NULL"
Correct:   "dq_rule_expression": "AMOUNT >= 0"
Incorrect: "dq_rule_expression": "WHERE BUSINESS_PARTNER_ID IS NULL"
Incorrect: "dq_rule_expression": "SELECT * FROM t WHERE ..."
```

Reason: the verifier/runtime wraps every DQ cell as `SELECT 1 FROM t WHERE ({filter_conditions}) AND ({dq_rule_expression})`. If the cell itself contains `WHERE`, the composed SQL becomes `WHERE ... WHERE ...`, which is a syntax error in every standard SQL dialect. This class of bug was observed shipping in prior runs (the generator used to bake `WHERE {filter} AND ({expr})` into the cell and the verifier then wrapped it again) and is prevented at the schema level here: the cell is always a bare predicate; exactly one downstream layer adds `WHERE`.

Exceptions:
- Row-count rules that require an aggregate over the whole table (e.g., `COUNT(*) > 0`) are still bare predicates and correct as-is; the generator wraps them appropriately based on `rule_type`.
- Rules of `rule_type: "CUSTOM_SQL"` where a full query is genuinely required must set `dq_rule_expression: "[CUSTOM_SQL]"` and populate a separate `custom_sql` field with the complete query; the generator emits that field verbatim to the workbook without WHERE composition.

Default thresholds by rule type (use unless the design context indicates otherwise):

| rule_type | threshold_value | intent |
|---|---|---|
| NOT_NULL | 0 | zero nulls allowed |
| UNIQUENESS | 0 | zero duplicates |
| FK_INTEGRITY | 0 | zero orphan children |
| RANGE / MIN / MAX | 0 | zero out-of-range |
| REGEX_MATCH | 0 | zero pattern mismatches |
| ROW_COUNT_NOT_ZERO | 1 | at least one row |
| FRESHNESS | 24 | max hours since load (adjust per SLA) |
| COMPLETENESS_% | 95 | at least 95% populated |

### R3 - Grain declaration required

Every table's entry in the `"tables"` array must populate `grain`:

- `"grain": "one row per (customer, month)"`
- `"grain": "one row per transaction event"`
- `"grain": "one row per business partner (SCD Type 1)"`

The renderer emits it as the `Grain:` line in the review markdown.

### R4 - Surrogate key strategy required

Every fact and dimension table's entry in the `"tables"` array must populate `key_strategy`:

- `"key_strategy": "hash(business_key_1, business_key_2) with monotonic seed"`
- `"key_strategy": "identity column"`
- `"key_strategy": "composite natural key (no SK required for this ref table)"`

### R5 - STTM completeness

Every entry in the `"mappings"` array:

- Populate `filter_conditions`. Use `-` if no row-level filter applies. Never blank.
- Populate `join_conditions`. Use `-` if no join or lookup applies. Never blank.
- Populate `source_reference` with a source file/section/line. If missing, set `source_reference` to `[NEEDS_HUMAN_REVIEW]` and add `source_reference_reason`.

## column_mappings.json structure

```json
{
  "layers": [
    {"id": "L0", "title": "Layer 0 - Raw", "schema": "client_rw", "database": "client_db_{env}"}
  ],
  "tables": [
    {
      "layer": "L0",
      "table": "rw_iqvia_xponent_weekly",
      "purpose": "Landing table for weekly IQVIA Xponent extracts",
      "grain": "one row per (customer, product, week)",
      "key_strategy": "composite natural key (no SK at raw)",
      "table_type": "raw",
      "load_strategy": "full refresh",
      "frequency": "weekly",
      "schema": "client_rw",
      "database": "client_db_{env}"
    }
  ],
  "mappings": [
    {
      "layer": "L0",
      "target_table": "rw_iqvia_xponent_weekly",
      "target_column": "customer_id",
      "data_type": "VARCHAR(64)",
      "nullable": false,
      "is_primary_key": true,
      "source_system": "IQVIA_XPONENT",
      "source_table": "raw_xponent_weekly",
      "source_column": "cust_id",
      "transformation": "TRIM(UPPER(cust_id))",
      "filter_conditions": "-",
      "join_conditions": "-",
      "source_reference": "IQVIA_STTM.xlsx > sheet 'Xponent' > row 12",
      "notes": ""
    }
  ]
}
```

`layers` carries per-layer metadata (title, schema, database) once. `tables` carries per-table metadata once — purpose, grain, key strategy, table type, load strategy, frequency, and schema/database overrides (omit when equal to the layer's). `mappings` carries one entry per column. The generator, the planner (`build_plan.py`), the renderer (`render_design_md.py`), and the verifier all consume this one file; no other artifact restates these facts.

## dq_rules_design.json structure

```json
{
  "rules": [
    {
      "layer": "L0",
      "target_table": "rw_iqvia_xponent_weekly",
      "target_column": "customer_id",
      "rule_id": "DQ_L0_XPONENT_001",
      "rule_type": "NOT_NULL",
      "severity": "CRITICAL",
      "dq_rule_expression": "customer_id IS NOT NULL",
      "dq_rule_expression_reason": "",
      "threshold_value": "0",
      "threshold_value_reason": "",
      "source_reference": "DQ_POLICY.md > NOT_NULL_KEYS"
    }
  ]
}
```

`threshold_value` and `threshold_value_reason` are required per R7. See the default-thresholds table in R7 for common values by rule_type. See R6 for per-table coverage minimums and the `NO_DQ_APPLICABLE` escape valve.

## Write discipline (mandatory)

1. **Append per table, always.** Never accumulate several tables and write them in one call. Never overwrite a whole file after the initial scaffold Write.
2. **Never hand-write or hand-edit `target_model_design.md`.** It is produced only by `render_design_md.py`. Fix the JSONs and re-render.
3. **Never paste artifact bodies in chat.** Chat may only include phase status, files written, table counts, blockers, and next command.
4. **Do NOT spawn subagents in the default path.** The per-table append loop keeps every tool call safely under the token cap without them. Spawn `design-writer` only in the rare escape-hatch case defined in `.claude/agents/design-writer.md` (single layer >10 tables AND early per-table timings look bad).
5. **Do NOT construct a runtime script to write the JSONs.** Use `Edit` directly. The only scripts this phase runs are the shipped `render_design_md.py`, `build_plan.py` (and `generate_column_mappings.py` in the rare recovery case below).
6. **Recovery:** if `column_mappings.json` is damaged mid-run and a previously rendered `target_model_design.md` exists, `generate_column_mappings.py` can reconstruct the mappings from the markdown (recovery-only path). In the normal flow there are no fragments and no reconstruction — the JSON is written directly.
7. **Resume on failure:** follow the idempotent re-entry rules above — re-read `column_mappings.json`, list which tables are already present, and continue with the next planned table.

## Per-table telemetry (progress.json contract)

After every table's artifact Edits complete, `Edit` `progress.json` to append/update:

```json
{
  "phase": "design-architecture",
  "design": {
    "tables_planned_total": 51,
    "tables_completed_total": 7,
    "last_table_completed": {
      "table": "rw_iqvia_xponent_weekly",
      "layer": "L0",
      "at": "ISO-8601"
    },
    "per_table_elapsed_seconds": {
      "rw_iqvia_xponent_weekly": 42
    }
  }
}
```

This gives the operator a live per-table pace. If per-table elapsed exceeds 90s on the first three tables, halt and surface — the phase will not hit its wall-clock target and something is wrong (usually context bloat or thinking-loop).

These per-table telemetry appends are the documented exception to the twice-per-phase bookkeeping rule (CLAUDE.md principle 14). They do not replace the mandatory full state/progress writes at phase start and phase completion.

## Chat output hard limit

The final orchestrator chat reply for this phase must be under 400 words and must include only:

- phase status,
- files written (paths, not bodies),
- table/layer counts and wave counts,
- open questions or blockers,
- recommended next command `/generate-artifacts`.

A 32k output-token error is treated as a phase execution failure. Recovery must resume from existing files, not restart from scratch.

## Escape hatch: `design-writer` subagent

Only spawn `design-writer` when ALL of the following hold:

- A single layer has more than 10 target tables, AND
- The per-table telemetry (progress.json) shows the first 3 tables of that layer averaging over 90 seconds each, AND
- Orchestrator context is estimated over 120k tokens (rough signal: significant Read of source docs already happened in this session).

When spawned, the design-writer's only job is to append tables for one layer to the same shared files (`column_mappings.json`, `dq_rules_design.json`). It receives a pre-computed list of table specs as its prompt so it does NOT need to Read source docs. See `.claude/agents/design-writer.md`. The orchestrator still runs the renderer once after all layers are complete.

The orchestrator is always responsible for:

- Deciding layer architecture, grain, SK strategy, and column design.
- Scaffolding the two canonical JSON files up front.
- Running `render_design_md.py` once after the loop to produce the review markdown.
- Running `build_plan.py` to compute `plan.json` and reviewing it.
- Writing `design_brief.md` at the end (short summary; no artifact bodies).
- Confirming `progress.json.design.tables_completed_total == tables_planned_total` before computing the plan.

## End Of Turn
Recommend /generate-artifacts. Stop. Do not auto-invoke the next phase, even if the user previously said to do everything.

Additional context from user invocation: $ARGUMENTS
