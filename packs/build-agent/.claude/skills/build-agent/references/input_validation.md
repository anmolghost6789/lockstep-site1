# Input Validation

Read this during `/start-build-run`.

The quality gate should be strict, honest, and evidence-backed. The goal is not to reject messy inputs. The goal is to explain what they allow, what they block, and what confidence the run can reasonably achieve.

## Template conformance check

Before running structural checks, assess whether inputs follow the golden template format. If they do, parsing is deterministic and the quality gate can run with higher precision. Template conformance is not required — it is a confidence accelerator.

Template signals:
- STTM: table_tracker sheet exists, per-table sheets have summary block (rows 1-10ish) and detail block with known column headers (Target Table, Target Column, Role, Target Data Type, etc.)
- Data Model: relationships sheet exists with From/To table columns
- DQ Rules: DQ Check, Criticality (C/NC), and Threshold columns present

If template conformance is detected, note it in the quality gate report.

## Required outputs of the quality gate

The quality gate report must include:
- overall assessment
- severity counts
- findings with affected tables or columns
- recommendation
- input completeness score
- input evidence notes for major findings
- template conformance status

## Severity levels

- `blocker` — reliable generation cannot proceed without a user override
- `critical` — generation can proceed, but output quality will be materially constrained
- `major` — the agent will need to infer or ask
- `minor` — documentation or edge-case weakness
- `info` — normalization or parsing note

## Structural checks

### Blockers
- duplicate target column names within a table
- invalid or unusable target column names
- empty stub tables with no usable lineage
- missing data types for required DDL output

### Critical
- SCD2 table with no business-key guidance and no clear inference path
- source table references that are likely broken or contradictory
- column mapping rows whose core fields contradict each other

### Major
- missing target grain
- missing load strategy
- source table specified but source column absent
- DQ severity values inconsistent or malformed

### Minor
- missing descriptions
- placeholder notes that do not block interpretation

## Semantic anomaly checks

In addition to structural checks, apply the following structured semantic-anomaly checklist. **Every check must be executed and its outcome written to `state/run_id_<ID>/discovery/semantic_checks.json`** conforming to `references/semantic_checks.schema.json`. A missing `semantic_checks.json` file is a phase completion failure — start-build-run cannot transition to analyze-inputs without it.

Each check has a stable `check_id`, severity, trigger condition, evidence requirement, and required action.

| check_id | severity | what it detects | trigger | required action on flag |
|---|---|---|---|---|
| `C-XDC-01` | critical | Cross-document contradiction between ANY pair of input files (e.g., one document specifies INNER JOIN for FK lookups while another documents unknown-member handling with SK=-1, implying LEFT JOIN) | Any pair of documents directs the agent toward mutually incompatible implementations for the same artifact | Flag the specific contradiction with both evidence refs; require explicit resolution at the first checkpoint; do NOT silently pick one |
| `C-QSV-01` | critical | User instruction that contradicts `quality_standards.md` best practices in a way that would cause data loss or broken referential integrity (e.g., "INNER JOIN all fact→dim lookups" on a fact with nullable FKs) | User instruction, when followed literally, would produce data correctness failures | Flag as a conflict to be resolved via waiver at first checkpoint; never silently override the user instruction, but require acknowledgement of the risk |
| `M-KG-01` | major | Any gaps or issues document claims "all issues resolved" or is empty / trivially populated when the domain or STTM size suggests active gaps should exist | File is missing, empty, or contains only stub placeholders in a run with >5 tables or non-trivial business rules | Flag as suspicious; recommend the user review before proceeding |
| `M-WO-01` | major | Wave ordering places downstream tables (facts) before their upstream dependencies (dimensions), or creates a cycle | User-supplied wave column in STTM table_tracker disagrees with the dependency graph derived from source/target lineage | Flag as a dependency violation; require user confirmation or correction before proceeding |
| `M-AB-01` | major | Annotated bugs or correction markers present in input files (e.g., `[M30]`, `[BUG]`, `[FIXME]`, `[TODO:]`) | Any input file contains a recognized annotation pattern | Flag each occurrence with evidence ref; resolutions must be tracked in the assumptions register during packaging |
| `N-RM-01` | minor | Input documents reference tables, columns, or business rules not present in the STTM or data model | Any input file mentions a table/column that has no corresponding STTM entry | Flag as a potential oversight; do not block progression |

### Semantic check output contract

Each run must produce `state/run_id_<ID>/discovery/semantic_checks.json` with one entry per check_id. Each entry must include:

- `check_id` — from the table above
- `status` — `passed` (ran and found nothing), `flagged` (ran and found a finding), or `n/a` (check not applicable — must include `n_a_reason`)
- `detail` — one-sentence human-readable summary of what was found
- `evidence_refs` — list of `{source_file, location}` objects pointing at the evidence (required when status is `flagged`)
- `severity` — copied from the table above
- `recommended_action` — what start-build-run should propose to the user

When a check is `flagged` at critical severity, start-build-run must block phase transition until the user acknowledges the finding at the first checkpoint. Flagged major findings require acknowledgement but do not hard-block. Minor findings are reported as info only.

## Evidence capture expectations

For every blocker, critical, or major finding, capture where the finding came from when possible:
- source file
- sheet or section
- table
- row or field

This evidence should be reusable during analysis, planning, and evaluation.

## Decision logic

### If blockers exist
- report them clearly
- recommend fixing before proceeding
- continue only if the user explicitly overrides

### If only critical issues exist
- recommend fixing first
- continue if the user chooses to proceed with documented assumptions

### If only major or minor issues exist
- proceed with clear disclosure of what will be inferred

## Completeness score

Score the presence of:
- STTM or mapping
- data model
- DQ rules
- context or standards
- legacy SQL or reference code

Report completeness as a plain percentage with a one-line explanation of the biggest missing categories.

## Input Evaluation Report

After completing all structural and semantic checks, the agent produces an Input Evaluation Report. This report is the first thing the user sees and determines their trust in the system.

The report includes:
- **Verdict**: pass / warn / error
- **Producible outputs matrix**: for each artifact type (DDL, DML, DQ, tests, deployment), the status (full / partial / not_possible) and confidence
- **Findings**: grouped by severity (blocker → critical → major → minor → info)
- **Recommendations**: concrete, actionable items
- **Assumptions**: documented with risk levels (only for warn verdicts)

### Verdict Logic
- `error` → any core output (DDL/DML) is `not_possible`, OR any blocker-severity finding
- `warn` → all core outputs are at least `partial`, AND one or more outputs are `partial` or have major findings
- `pass` → all core outputs are `full`, AND no major or higher findings

### Re-Evaluation Loop
After presenting the report:
- `error` → halt, user fixes inputs, re-runs `/start-build-run`
- `warn` → user accepts assumptions or fixes inputs
- `pass` → proceed

Maximum 3 re-evaluations before recommending the user seek additional help.
