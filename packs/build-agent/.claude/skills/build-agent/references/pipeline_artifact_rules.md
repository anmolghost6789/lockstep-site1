# Pipeline Artifact Rules

What the `artifact-writer` (pipeline mode) produces and the rules it enforces. Load this
during `/generate-pipeline`. Platform-specific syntax detail lives in
`references/pipeline_conventions/{databricks,snowflake}.md`.

## What artifact-writer generates (per platform)

**Databricks:**
- `workflow_wave_{N}.yml` — one per wave (tasks for that wave only)
- `workflow_master.yml` — all tasks, all waves, full `depends_on` wiring
- `pipeline_readme.md` — deployment guide per conventions spec

**Snowflake:**
- `pipeline_tasks.sql` — all CREATE TASK statements in correct creation order
- `pipeline_activate.sql` — RESUME statements (leaf tasks first, root tasks last)
- `pipeline_suspend.sql` — SUSPEND statements for teardown
- `pipeline_readme.md` — deployment guide per conventions spec

**Generic:**
- `pipeline_wave_{N}.yml` — one per wave
- `pipeline_master.yml` — all tasks, all waves, full dependency wiring
- `pipeline_readme.md` — deployment guide

## Wave-generator pipeline mode rules

The artifact-writer reads `lineage.json` and `pipeline_conventions/{platform}.md`. It must:

1. **Map every non-passthrough table** in `lineage.tables[]` to exactly one task. Tables with `raw_passthrough: true` become ingest tasks (Databricks notebook_task stub / Snowflake stored procedure stub / Generic ingest task).

2. **Wire dependencies** from `lineage.dependency_graph.edges`:
   - Databricks: `depends_on[].task_key`
   - Snowflake: `AFTER` clause (fan-in barrier tasks when multi-predecessor — see conventions)
   - Generic: `depends_on[]` list
   - `circular_dependency_flagged` edges: include with comment, do not omit.

3. **Embed DML for Snowflake**: read the `dml_file` path from `lineage.tables[].dml_file` and inline the content inside the `TASK AS` block. If DML file does not exist (DML was skipped): generate a stub with `[ASSUMPTION]` notice.

4. **Use variable substitution** (`{{placeholder}}`) for all environment-specific values per conventions spec.

5. **Add header comment** to every generated file: run_id, generated_at, platform, lineage_source status (planned/reconciled/mixed), wave count.

6. **Mark all `lineage_source: "planned"` columns** in the header if any column in any table has `lineage_source != "reconciled"`. This signals the pipeline was generated from unreconciled lineage.
