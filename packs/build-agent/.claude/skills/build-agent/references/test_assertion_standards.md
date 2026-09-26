# Test Assertion Standards

The minimum assertion matrices `/generate-tests` enforces (via the `artifact-writer`
sub-agent), plus the pipeline-test output format. Load this during `/generate-tests`.

## Data test minimum matrix

**For every table:**
- Row presence / existence check
- Key or uniqueness check (when PK or SK defined)
- Critical not-null check for required columns

**For transformation-heavy tables:**
- At least one business-rule assertion (e.g., NET_AMOUNT = QUANTITY * UNIT_PRICE)
- At least one derived-column assertion
- FK integrity check: all FK values exist in the referenced dimension OR equal the unknown-member SK value

**For SCD2 tables:**
- At most one IS_CURRENT = TRUE record per business key
- EFF_END_DT IS NULL for all IS_CURRENT = TRUE records
- EFF_START_DT <= EFF_END_DT for all expired records (where EFF_END_DT IS NOT NULL)
- RECORD_HASH changes between versions of the same business key

**For incremental tables:**
- Watermark column is non-null for all rows
- No rows with future-dated watermark values

**For DQ-heavy tables:**
- At least one assertion proving a critical DQ rule is represented

## Pipeline test output format

| pipeline_platform | Output file | Format |
|---|---|---|
| `databricks` | `pipeline_tests.py` | pytest module — see `references/pipeline_conventions/databricks.md` |
| `snowflake` | `pipeline_tests.sql` | SQL assertions — see `references/pipeline_conventions/snowflake.md` |
| `generic` | `pipeline_tests.yml` | Declarative assertion spec (YAML) |

## Pipeline test minimum matrix

**Structural / completeness:**
1. Every non-passthrough table in `lineage.tables[]` has a corresponding task in the pipeline
2. Every `dependency_graph.edge` maps to the correct `depends_on` / `AFTER` clause
3. No wave ordering violations (task in wave N does not depend on task in wave N+2)

**Operational / correctness:**
4. Every INCREMENTAL table declares a `watermark_column` in lineage
5. Every DML task references a load strategy compatible with idempotency (MERGE, INSERT OVERWRITE, CREATE OR REPLACE — checked via `lineage.tables[].load_strategy`, not SQL parsing)
6. Every entry in `lineage.external_sources[]` has at least one corresponding ingest task

**Platform-specific (Databricks):**
7. All tasks have `max_retries > 0`
8. All tasks have `timeout_seconds > 0`
9. All tasks have `job_cluster_key` or `existing_cluster_id` set

**Platform-specific (Snowflake):**
10. Root tasks (no predecessors) have `SCHEDULE` defined
11. Non-root tasks do NOT have `SCHEDULE`
12. All tasks reference the correct warehouse

**Generic:**
13. Every task has `inputs` and `outputs` defined
14. Every task has `load_strategy` set
