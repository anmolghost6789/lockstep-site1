# TRACEABILITY AND REFERENCES POLICY

## Purpose

Every generated artifact row must explain where the data/design decision came from. The `References` column in STTM, Data Model, DQ, and ER Diagram workbooks is not optional for populated data/detail rows where the template/spec includes it. It provides auditability across source inputs, human clarifications, configuration defaults, reference-store advice, and agent derivations.

## Traceability grain

Default grain is row-level. Each populated row in a target-table or ER detail sheet must have a non-empty `References` value. If different cells in the same row come from different evidence, list all material sources in the row-level `References` cell. Use the `Comments` cell for short clarifications when the reference list needs explanation.

Cell-level traceability is optional and may be represented in `outputs/00_state/traceability/evidence_registry.json` when a row is complex, controversial, carries documented risk, or combines many sources.

## Evidence registry

Create and maintain:

```text
outputs/00_state/traceability/evidence_registry.json
```

Recommended structure:

```json
{
  "run_id": "RUN_YYYYMMDD_HHMMSS_IST",
  "evidence_items": [
    {
      "evidence_id": "BRD-001",
      "type": "input_requirement",
      "source_path": "outputs/00_state/input_snapshot/requirements/brd.docx",
      "locator": "section/page/sheet/row/column when available",
      "excerpt_or_summary": "Short non-sensitive summary",
      "confidence": 95
    }
  ],
  "row_references": [
    {
      "artifact": "outputs/L2/STTM_L2.xlsx",
      "sheet": "f_sales",
      "row": 10,
      "target_table": "f_sales",
      "target_column": "SALES_AMT",
      "references": ["BRD-001", "SRC-014", "RULE-003"]
    }
  ]
}
```

## Reference value format

Use compact, human-readable reference tokens separated by semicolon and a space:

```text
BRD-001; SRC-014; RULE-003
```

Allowed prefixes:

| Prefix | Meaning | Example |
|---|---|---|
| `INPUT` | General input-file evidence | `INPUT-002` |
| `SRC` | Source inventory/table/column evidence | `SRC-014` |
| `BRD` | Business requirement evidence | `BRD-001` |
| `RULE` | Business/transformation rule evidence | `RULE-003` |
| `KPI` | KPI definition evidence | `KPI-002` |
| `KBQ` | Key business question evidence | `KBQ-004` |
| `PRODUCT` | Data product/report/API/feed requirement evidence | `PRODUCT-001` |
| `DQREQ` | Data quality requirement evidence | `DQREQ-003` |
| `CTX` | Enterprise/domain/project/user-instruction context | `CTX-007` |
| `SUPPORT` | Current-run additional document evidence | `SUPPORT-005` |
| `HUMAN` | Human clarification or review feedback | `HUMAN-Q-SRC-003` |
| `CONFIG` | Project config/default package setting | `CONFIG-audit-columns` |
| `PKG` | Built-in package rule/template pattern | `PKG-dq-patterns-business-key` |
| `REFSTORE` | Governed reference-store pattern used as advisory evidence | `REFSTORE-MAP-009` |
| `INFERRED` | Agent derivation from listed evidence | `INFERRED-LINEAGE-004` |
| `RISK` | Documented-risk manifest item | `RISK-SRC-002` |

If a row is inferred, do not use `INFERRED` alone. Pair it with the evidence that supported the inference.

## Artifact requirements

- STTM column `References` (P): mandatory for every populated detail row.
- Data Model column `References` (M): mandatory for every populated detail row.
- DQ column `References` (K): mandatory for every populated detail row.
- ER Diagram `References` columns: mandatory for every populated lineage, relationship, or layer-diagram row when present in the ER template/spec.
- Audit/system-generated rows reference `CONFIG-audit-columns` and/or the relevant package/template rule.
- Surrogate-key rows reference `CONFIG-surrogate-key` plus the target entity/design evidence.
- `[BEST-GUESS]` rows reference the relevant `RISK-*` item and include `[BEST-GUESS]` in Comments.

## Validation rule

A blank `References` cell in a populated detail row is a deterministic validation failure unless the row is explicitly a blank spacer/sample row that should have been removed. Sample rows must not remain in generated outputs.
