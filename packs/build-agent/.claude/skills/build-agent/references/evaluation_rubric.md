# Evaluation Rubric

Read this before `/evaluate-build`.

This rubric produces deterministic scoring and concrete remediation.

## Core rule

Re-read generated files from disk before scoring. Never evaluate from memory of what was generated earlier in the conversation.

## Fixed dimensions and weights

Each fixed dimension is scored from 0 to 10. Overall score is:

`overall_score = sum(score * weight * 10)`

Weights:
- Faithfulness to Inputs — 0.20
- Coverage — 0.15
- Artifact Quality — 0.15
- Implementation Readiness — 0.15
- Traceability — 0.10
- Internal Consistency — 0.10
- Handling Uncertainty — 0.10
- Readability — 0.05

These weights always sum to 1.00. Dynamic dimensions do not change the math.

## Fixed dimensions

### Faithfulness to Inputs
Does the output reflect the actual inputs, user instructions, and documented assumptions without fabrication?

**Mandatory Faithfulness Checklist** — execute this checklist before scoring Faithfulness. Document each result. Use the checklist results as primary evidence for the score:
1. Did the join type in FK lookup DML match the user instruction or resolved convention? Was it correctly scoped to fact DML only (not dimension-to-dimension joins)?
2. Did the unknown-member SK value match the user instruction or resolved convention?
3. Did the RECORD_HASH column order match the business_rules.md specification for each SCD2 table?
4. Were all derivation rules from business_rules.md and the derivation catalog implemented in the corresponding DML? Are the derived columns present in the DDL?
5. Were DQ and test artifacts limited to the user-specified scope (not over-generated)? Count actual files vs expected files.
6. Were all instruction deviations recorded as waivers in the assumptions register?
7. Do all source column references in DML resolve to actual source columns per the STTM? (No phantom column names.)
8. Does every column in the STTM for each table exist in the generated DDL? (No silently dropped columns.)
9. Is all DQ SQL syntactically valid? (No nested aggregates, no references to columns missing from the DDL.)
10. **Lineage consistency check** (conditional — skip if `plans/lineage.json` does not exist):
    - Does every `table_id` in `lineage.tables[]` exist in `table_index.json`?
    - Does every `column_lineage[].target_column` entry exist in the corresponding DDL file? (Check via column name lookup — do not read full DDL into evaluator context; delegate column existence check to build-evaluator sub-agent.)
    - Does every `table_id` referenced in `dependency_graph.edges` (both `from` and `to`) exist in `lineage.tables[]`?
    - Any mismatch on items above auto-promotes to `must_fix` remediation.
    - If `lineage.json` is absent: record as `"lineage_consistency": "not_evaluated — lineage.json absent"`. Do not block packaging for runs predating the lineage feature.

If any checklist item (1–9) fails and no waiver is recorded, Faithfulness cannot score above 5. Item 10 failures do not cap Faithfulness below 5 on their own but always produce `must_fix` remediation items.

**Scoring anchors:**
- 9–10: all user instructions followed or waived with documentation; all derivation rules present
- 7–8: minor omissions (e.g., one missing non-critical derivation rule); no unwaived instruction overrides
- 5–6: one or more instruction deviations without waivers, or multiple missing derivation rules
- 3–4: multiple instruction deviations, core conventions overridden without disclosure
- 0–2: output bears little relationship to input instructions

### Coverage
Are planned tables, columns, rules, and artifacts fully represented?

### Artifact Quality
Are the files substantive, structurally sound, and free of placeholder content?

### Implementation Readiness
Could an engineer act on the artifacts immediately with the documented configuration and caveats?

**Scoring anchors:**
- 7+: no runtime-breaking mismatches (e.g., SK values consistent between DDL and DML, join types consistent with conventions, dialect functions valid for declared target)
- 5–6: one mismatch that would cause runtime failure (e.g., DDL inserts SK=-1 but DML COALESCEs to 0, or a single dialect-incompatible function)
- 3–4: multiple mismatches that would cause runtime failures, including dialect-incompatible functions across multiple artifacts

**Dialect compatibility sub-check:**
Implementation Readiness scoring must include a dialect-compatibility scan. Read the target dialect from `effective_conventions.json` and flag any generated SQL function that is invalid for that dialect. Common mismatches to flag:

| Declared dialect | Flag if found in generated SQL |
|---|---|
| `snowflake` | `GETDATE()`, `SYSDATE`, `HASHBYTES(`, `PARSENAME(`, `ISNULL(` (use IFNULL/COALESCE), `NVL(` (use COALESCE), `FARM_FINGERPRINT(`, `SAFE_OFFSET(` |
| `bigquery` | `DATEADD(`, `SPLIT_PART(`, `MD5(` without `TO_HEX()` wrap, `GETDATE()`, `SYSDATE`, `ISNULL(` (use `IFNULL` / `COALESCE`), `||` for string concat (use `CONCAT`), unquoted fully-qualified identifiers |
| `synapse` (T-SQL) | `SPLIT_PART(`, `\|\|` for string concat (use `+` or `CONCAT`), `CURRENT_DATE` without parens (use `CAST(SYSUTCDATETIME() AS DATE)`), `COALESCE(` where `ISNULL(` is idiomatic, `MD5(` (use `HASHBYTES('MD5',...)`), `FARM_FINGERPRINT(`, `MERGE` on dedicated SQL pool (flag with note — not supported on dedicated pools, only serverless) |
| `databricks` (Spark SQL) | `GETDATE()`, `SYSDATE`, `ISNULL(`, `HASHBYTES(`, `PARSENAME(`, `TOP ` clause (use `LIMIT`), `MD5(` returning binary without hex wrap |
| `redshift` | `GETDATE()` (use `SYSDATE` or `CURRENT_TIMESTAMP`), `HASHBYTES(`, `FARM_FINGERPRINT(`, `IFNULL(` (use `NVL` or `COALESCE`), `PARSENAME(`, Delta Lake / Spark idioms |

Flagged dialect mismatches auto-promote to `must_fix` remediation unless the user instruction explicitly authorized cross-dialect usage. If more than one distinct mismatch exists across generated artifacts, Implementation Readiness cannot score above 6. Record the scan result and each flagged occurrence in evaluation evidence.

### Traceability
Can a reviewer trace code back to plans and plans back to evidence-bearing discovery artifacts?

### Internal Consistency
Do naming, types, dependencies, and DQ behavior agree across artifacts?

### Handling Uncertainty
Are assumptions, low-confidence areas, inferred schemas, and waivers disclosed clearly?

### Readability
Is the output organized, professional, and easy to review?

## Dynamic dimensions

Score and report dynamic dimensions only when they apply:
- SCD2 Correctness
- Multi-Source Merge Quality
- Incremental Load Correctness
- DQ Rule Coverage
- Test Coverage

Dynamic dimensions do not change the numeric overall score. They can:
- trigger must-fix remediation
- create blockers for packaging
- limit a run to "pass with actions" instead of "pass"

## Input quality disclosure

This section is mandatory and must appear before scores.

State:
- what was missing from the inputs
- what was inferred
- what assumptions affected output quality
- what additional inputs would improve confidence
- if inputs contained annotated bugs, anomalies, or contradictions, how each was resolved and why (e.g., "[M30] RECORD_HASH formula bug — used corrected 6-column formula per annotation")
- if cross-document conflicts were detected, how each was resolved with rationale

## Remediation classes

- `blocker` — packaging must stop until resolved or explicitly waived
- `must_fix` — delivery can proceed only if the user accepts the risk or the issue is resolved
- `should_fix` — improves quality but does not block packaging

## Blocking conditions

The run is automatically blocked from production-ready packaging if any of the following are true:
- unresolved inferred source schema on a generated table
- missing expected artifact families without documented approval
- any critical fixed dimension below 5
- artifact contains placeholder or structurally invalid content
- evaluation evidence is incomplete or contradictory
- instruction deviation without a recorded waiver in the assumptions register

Critical fixed dimensions:
- Faithfulness to Inputs
- Artifact Quality
- Implementation Readiness

## Verdict rules

### Pass
- overall score >= 85
- no fixed dimension below 7
- no blockers

### Pass with actions
- overall score >= 70
- no critical fixed dimension below 5
- blocker-free, but must-fix or should-fix items remain

### Fail
- overall score < 70
- or any critical fixed dimension below 5
- or any blocker remains unresolved

## Required outputs

### `evaluation.json`
Must include: run_id, evaluated_at, input_quality_disclosure, fixed_dimensions, dynamic_dimensions, per_table_scores, overall_score, verdict, blockers, remediation_actions, recommendation.

### `evaluation_summary.md`
Must include:
1. input quality disclosure first
2. overall score and verdict
3. blocking items
4. top strengths
5. top risks
6. per-dimension scoring
7. dynamic dimensions
8. per-table scores sorted worst first
9. remediation actions grouped by priority
10. readiness statement for revision or packaging
