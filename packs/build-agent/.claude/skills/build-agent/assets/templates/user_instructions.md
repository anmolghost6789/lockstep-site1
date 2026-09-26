# User Instructions

> Use this file to give the Build Agent explicit directives for this run. These instructions take the highest priority when the agent resolves conventions and makes decisions.
>
> Be specific. The more concrete your instructions, the fewer assumptions the agent needs to make.

## Must-Follow Rules

> Hard constraints the agent must respect. These override defaults, patterns, and inferred conventions.

- [e.g., Always use MERGE for SCD2 loads, never DELETE+INSERT]
- [e.g., Every DDL must include all audit columns: INRT_DT, INRT_BY, UPDT_DT, UPDT_BY, CYCL_TIME_ID]
- [e.g., Surrogate keys must use BIGINT AUTO_INCREMENT, not sequences]
- [e.g., Do not generate DML for tables marked skip_dml in the STTM]

## Output Preferences

> How the agent should organize and format generated artifacts.

- [e.g., One folder per table: generated/{table_name}/]
- [e.g., File naming: {table_name}_ddl.sql, {table_name}_dml.sql, {table_name}_dq.sql]
- [e.g., Include a header comment block in every generated file]
- [e.g., Use 4-space indentation in all SQL]

## What to Generate

> Explicitly state what artifact types the agent should produce.

- [e.g., DDL for all tables]
- [e.g., DML for all non-skip_dml tables]
- [e.g., DQ scripts for all tables with DQ rules defined]
- [e.g., Test scripts for L2 and L3 tables only]

## What to Skip

> Explicitly state what the agent should NOT generate.

- [e.g., Do not generate tests for L0 staging tables]
- [e.g., Do not generate documentation markdown — only SQL files]
- [e.g., Do not create aggregate/mart layer tables]

## Convention Overrides

> Use this section to override specific enterprise or domain conventions for this run.

- [e.g., Use lowercase table names instead of UPPER_CASE]
- [e.g., Use CTE-based transformations instead of temp tables]
- [e.g., Environment variable pattern is {database}_{env} not {project}_db_{env}]

## Priorities

> Tell the agent what matters most for this run.

- [e.g., Correctness over speed — take time to get SCD2 logic right]
- [e.g., Prioritize L2 dimensions — L3 facts can be lower confidence for now]
- [e.g., DQ completeness is critical — every column should have at least one check]

## Additional Guidance

- [e.g., If a source column is ambiguous, ask me before assuming]
- [e.g., For unknown member handling in facts, always use -1 as the default SK]
- [e.g., Reference legacy_patterns.sql for the current MERGE pattern — follow that style]
