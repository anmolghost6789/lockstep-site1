# Quality Standards

Read this before any `/generate-<artifact>` command (`/generate-ddl`, `/generate-dml`, `/generate-dq`, `/generate-pipeline`, `/generate-tests`).

These are operational standards for generated artifacts. They are not optional style suggestions.

## Non-negotiable rules

### No placeholders
Do not generate TODO, FIXME, "implement later", or placeholder content in deliverable artifacts.

### No silent assumptions
If the artifact relies on an assumption, say so in the header and keep the confidence score aligned with that uncertainty.

### No hidden hardcoding
Do not hardcode environment-specific values unless the user explicitly asked for that pattern. Prefer parameters, configuration variables, or documented defaults.

### No production-ready claim with unresolved blockers
If an artifact depends on inferred schema, unresolved input gaps, or waived assumptions, it can still be useful, but it is not production-ready without that caveat.

### No silent instruction override
If the agent deviates from an explicit user instruction (e.g., join type, unknown-member SK value, column ordering, transformation convention), it must record a waiver in the assumptions register with: the instruction it deviated from, the source document, the rationale for deviation, and the alternative applied. The waiver must be surfaced at the next checkpoint. Unwaived instruction deviations automatically trigger a `blocker` in evaluation. The convention priority chain must be honored: user instructions > active memory > project context > domain context > enterprise context > dominant input pattern > sensible default.

### No unvalidated source column references
Before writing any DML, the agent must validate every planned `src.*` / source-alias column reference against the `source_column_registry.json` produced during analysis. Case sensitivity is honored per the target dialect (Snowflake = case-insensitive by default; BigQuery / Redshift / Postgres = case-sensitive). If a planned reference does not resolve, generation for that table halts and the user is notified — do not emit DML with unresolved references and "hope for the best." This prevents runtime "column not found" errors on case-sensitive platforms.

### No dialect-mismatched SQL functions
Every generated artifact must use functions and syntax valid for the target dialect declared in `effective_conventions.json` (derived from `enterprise_context.md::SQL Dialect` and any project/user overrides). Cross-dialect idioms copied from `legacy_patterns.sql` must be adapted to the target dialect before emission. The evaluator runs a dialect-compatibility scan and flags mismatches as `must_fix`.

## Required header fields

Every generated code file must include a structured header comment block with:
- Description
- Confidence
- Evidence Status: `confirmed`, `mixed`, or `assumed`
- Assumptions
- Source Tables
- Target Table
- Generated At
- Run ID
- Plan Reference

Include when relevant:
- Applied Conventions
- Inferred Logic
- Known Review Flags
- User Instructions Applied

## Confidence guidance

- `0.95-1.00` — nearly all logic backed by explicit evidence
- `0.80-0.94` — strong evidence with minor inference
- `0.65-0.79` — mixed evidence; review recommended
- `0.50-0.64` — significant assumptions; reviewer attention required
- `< 0.50` — do not generate deliverable code without explicit user approval

## Minimum artifact quality

### DDL
- all planned columns present
- data types present
- required audit columns present if conventions require them
- no unexplained drift from the plan

### DML
- load strategy matches the plan
- all required transformations implemented
- complex logic commented briefly
- configuration inputs documented clearly
- all derivation rules from the derivation catalog targeting this table must be implemented in the DML; missing derivation rules are a validation failure
- no-op CTEs (CTEs that pass through data unchanged without filtering, deduplicating, aggregating, or transforming) are prohibited unless explicitly justified in the artifact header as a defensive guard for known-dirty sources

### DQ

Emission format is governed by the `dq_framework` convention resolved during analysis (sourced from `enterprise_context.md`, overridable by project/user). Supported frameworks: `sql_procedural` (default), `dbt_tests`, `great_expectations`, `deequ`, `custom`. Framework-agnostic rules apply to every emission; framework-specific rules are scoped below.

**Framework-agnostic rules (apply regardless of `dq_framework`):**
- explicit rules implemented exactly as specified in the DQ input
- inferred rules labeled as inferred in the artifact header
- severity behavior consistent with conventions (critical vs advisory mapping)
- observability / result reporting pattern consistent across the run
- all column references in DQ artifacts must resolve to actual columns in the target DDL — if a rule references a column, that column must exist in the table's DDL

**`sql_procedural` (default)**
- Emit one `.sql` file per table containing check queries
- SQL must use valid single-level aggregate patterns; **never nest aggregate functions** (e.g., `SUM(CASE WHEN COUNT(...))` is invalid SQL in every platform). Use subquery or CTE patterns instead:
  - **Uniqueness check:** `SELECT key_col, COUNT(*) AS cnt FROM table GROUP BY key_col HAVING COUNT(*) > 1` or `SELECT COUNT(*) - COUNT(DISTINCT key_col) AS duplicate_count FROM table`
  - **Not-null check:** `SELECT COUNT(*) AS null_count FROM table WHERE column IS NULL`
  - **Allowed values check:** `SELECT COUNT(*) AS invalid_count FROM table WHERE column NOT IN ('val1', 'val2', ...)`
  - **Threshold check:** `SELECT COUNT(*) AS failed_count FROM table WHERE NOT (condition)`
- All SQL must be valid for the target dialect (see "No dialect-mismatched SQL functions" above)

**`dbt_tests`**
- Emit one `schema.yml` block per table with dbt generic tests (`not_null`, `unique`, `accepted_values`, `relationships`) — these map 1:1 from standard DQ checks
- Emit singular test `.sql` files under `tests/` for checks that don't map to generic tests (e.g., complex business-rule checks, SCD2 invariants, multi-column consistency)
- Reference columns by dbt convention (unquoted, lowercase by default unless `enterprise_context.md` specifies otherwise)
- Threshold handling: translate "NC" (non-critical) to `severity: warn`; "C" (critical) to `severity: error`

**`great_expectations`**
- Emit one `.py` expectation suite per table defining `ExpectColumnValuesToNotBeNull`, `ExpectColumnValuesToBeUnique`, `ExpectColumnValuesToBeInSet`, `ExpectTableRowCountToBeBetween`, etc.
- Emit one `expectations_config.yml` listing the suites and their datasource bindings
- Criticality: map "C" to `meta: {severity: critical}`; "NC" to `meta: {severity: advisory}`
- Do not hardcode datasource connection details — parameterize via config

**`deequ`**
- Emit one Scala file per table using `VerificationSuite`, `Check`, and constraint methods (`isComplete`, `isUnique`, `isContainedIn`, `satisfies`)
- Use `CheckLevel.Error` for critical rules, `CheckLevel.Warning` for non-critical
- Include a minimal `AnalysisRunner` section showing how to execute the checks on Spark

**`custom`**
- Before emitting the first DQ artifact for the run, the agent must ask the user for the exact emission format (extensions, directory layout, assertion DSL, result handling). Record the answer as a checkpoint decision and apply consistently across the run.

### SCD2
- business key column must be present and non-null
- EFF_START_DT must be present and non-null
- EFF_END_DT must be NULL for current records
- IS_CURRENT flag must agree with EFF_END_DT
- RECORD_HASH must cover all tracked columns in the exact order specified in the canonical model's `record_hash_column_order` field (sourced from business_rules.md or STTM); do not substitute a different column order
- MERGE logic must handle: new inserts, changed records (expire + insert new version), unchanged records (no-op)

### Tests
- not stubs
- use specific assertions
- cover at least one meaningful behavior

## Minimum test matrix

### For every table test file
- one existence or row-presence check
- one key or uniqueness check when a key exists
- one critical not-null check for required columns

### For transformation-heavy tables
- at least one business-rule assertion (e.g., FULL_NAME = TRIM(FIRST_NAME) || ' ' || TRIM(LAST_NAME))
- at least one derived-column assertion (e.g., NET_UNITS = units_sold - returns_units)
- at least one FK integrity check (all FK values exist in the referenced dimension, or are the unknown-member SK value)

### For incremental or SCD2 tables
- at least one merge or versioning behavior assertion
- one test that verifies at most one IS_CURRENT = TRUE record per business key
- one test that verifies EFF_END_DT IS NULL for all IS_CURRENT = TRUE records
- one test that verifies EFF_START_DT <= EFF_END_DT for all expired records

### For DQ-heavy tables
- at least one assertion proving a critical or advisory rule is represented

## Unknown member handling

For fact tables with foreign key columns:
- read the unknown-member SK value from `effective_conventions.json` (resolved during analysis from user instructions, business rules, or defaults); use that exact value in DDL unknown-member row inserts and DML COALESCE expressions
- the default is -1, but user instructions or business rules may override this (e.g., SK=0); the convention priority chain applies
- read the resolved join type for FK lookups from `effective_conventions.json`; this convention applies to **fact table DML only** — dimension-to-dimension enrichment joins in SCD2 DML should use LEFT JOIN + COALESCE unless the user explicitly specifies otherwise for dimension joins; if the agent believes the user's specified join type would cause data issues, record a waiver with rationale — never silently substitute a different join type
- log lookup misses as DQ events when DQ rules require it

## Self-validation checklist

After writing each artifact, re-read it from disk and verify:
1. file exists and is non-empty
2. header exists and required fields are populated
3. syntax is valid for the target language
4. the artifact matches its plan
5. confidence matches the level of uncertainty
6. no prohibited placeholder content exists
7. environment-specific values are parameterized or explicitly justified
8. all derivation rules from the derivation catalog for this table are present in the DML
9. RECORD_HASH column order matches the canonical model's `record_hash_column_order` specification (for SCD2 tables)
10. join type for FK lookups matches the resolved convention from `effective_conventions.json` — and is scoped to fact DML only (dimension SCD2 enrichment joins use LEFT JOIN unless explicitly overridden for dimensions)
11. unknown-member SK value matches the resolved convention from `effective_conventions.json` (not hardcoded to -1)
12. all source column references in DML (src.X, alias.X) resolve to actual columns in the source table per the STTM column list — no phantom column names that would cause "column not found" runtime errors
13. every column in the canonical model / STTM for this table exists in the DDL — no silently dropped columns
14. DQ SQL uses valid single-level aggregate patterns — no nested aggregates (SUM inside COUNT, etc.); use subquery or CTE patterns when multi-level aggregation is needed
15. DQ SQL only references columns that exist in the target table's DDL

Fix validation failures immediately before moving on.

## Inline Notice Format

When the agent makes an assumption in a generated artifact, add to the header comment block:

```
-- [ASSUMPTION] This artifact assumes [X] based on [evidence or industry norm].
-- If incorrect, provide [specific input] and re-run this phase.
-- Risk if wrong: [specific impact].
```

When the agent cannot generate part of an artifact due to missing input:

```
-- [INSUFFICIENT INPUT] This section requires [specific input type] to generate.
-- What to provide: [concrete description]
-- Where to add it: Place in inputs/[subfolder]/ and re-run.
```

These notices are used instead of omitting artifacts. Every planned table gets its artifacts generated — thin-evidence tables get documented notices, not exclusion.

## SCD2 conventions (mandatory defaults)

These defaults apply to every SCD2 table in every run unless the active
run's user_instructions.md explicitly overrides them.

scd2_current_record_marker: sentinel
scd2_sentinel_value_timestamp: CAST('9999-12-31 00:00:00' AS TIMESTAMP)
scd2_sentinel_value_date: DATE '9999-12-31'
scd2_closed_record_condition: eff_end_date IS NOT NULL
  (or eff_end_dt IS NOT NULL for DATE-typed SCD2 columns)

Mixing sentinel and NULL conventions across SCD2 tables in the same run
is never permitted. Every artifact-writer invocation must apply the same
marker regardless of which wave it is processing. If effective_conventions.json
contains a scd2_current_record_marker entry, use that. If it does not,
use the sentinel default defined here.