# REFERENCE STORE GOVERNANCE

## Purpose

The reference store improves reuse across runs, domains, and clients, but it can also amplify hallucinations if patterns are applied outside their valid context. These rules govern what may be reused, how it is tagged, and when it is only advisory.

## Required metadata for every reusable pattern

Every pattern extracted into `context/reference/processed/` must carry this metadata where available:

```json
{
  "pattern_id": "string",
  "pattern_type": "naming | mapping | dq_rule | layering | transformation | table_design | kpi_logic | source_usage | domain_knowledge",
  "domain": "string | unknown",
  "sub_domain": "string | unknown",
  "business_process": "string | unknown",
  "client": "string | unknown",
  "source_system": "string | unknown",
  "data_product": "string | unknown",
  "reuse_scope": "global | domain | client | project | do_not_reuse_directly",
  "approved_for_reuse": false,
  "approval_status": "approved | provisional | rejected | deprecated",
  "sensitivity": "internal_standard | public_pattern | client_specific | restricted",
  "confidence": 0,
  "human_approved": false,
  "approved_for_cross_client_reuse": false,
  "created_from_run_id": "string | null",
  "last_validated_at": "IST ISO timestamp | null",
  "known_limitations": [],
  "do_not_apply_when": []
}
```

## Conservative defaults

When metadata is missing, apply these defaults:

```json
{
  "reuse_scope": "client",
  "approved_for_reuse": false,
  "approval_status": "provisional",
  "sensitivity": "client_specific",
  "approved_for_cross_client_reuse": false,
  "known_limitations": [],
  "do_not_apply_when": []
}
```

Built-in generic standards created by this package may use:

```json
{
  "reuse_scope": "global",
  "approved_for_reuse": true,
  "approval_status": "approved",
  "sensitivity": "internal_standard",
  "approved_for_cross_client_reuse": true
}
```

## Reuse rules

1. Current project evidence always wins over reference-store evidence.
2. Explicit human input always wins over reference-store patterns.
3. Client-specific mappings may not be reused for another client unless `approved_for_cross_client_reuse = true` and `reuse_scope` is `global` or `domain`.
4. `restricted`, `rejected`, `deprecated`, and `do_not_reuse_directly` patterns may be read for cautionary context but must not ground a design decision.
5. `provisional` patterns may inform questions and comparison checks, but they cannot be the sole grounding for a table, column, transformation, KPI formula, or DQ rule.
6. If a pattern is reused, record `pattern_id`, reason for reuse, scope match, confidence impact, and any current-project evidence that supports it.
7. If a reference pattern conflicts with current inputs, record the conflict and follow current inputs.

## Pattern filtering order

Filter candidate patterns in this order:

1. Exclude restricted/rejected/deprecated/do_not_reuse_directly patterns.
2. Match by domain and sub-domain.
3. Match by business process and data product.
4. Match by source system and source table/column patterns.
5. Match by client only if the current client is the same, or cross-client reuse is explicitly approved.
6. Prefer human-approved and recently validated patterns.
7. Lower confidence for patterns with missing metadata or known limitations.

## Required outputs when reference store is used

03 - Discover_Sources and 04 - Design must write stage-specific reference-use audits when reference-store material is consulted:

```text
03 - Discover_Sources: outputs/00_state/source_discovery/reference_store_source_audit.json
04 - Design: outputs/00_state/design/reference_use_audit.json
```

Minimum audit structure:

```json
{
  "reference_store_consulted": true,
  "patterns_considered": [],
  "patterns_used": [],
  "patterns_rejected": [],
  "conflicts_with_current_inputs": [],
  "cross_client_patterns_blocked": [],
  "notes": "string"
}
```

This audit supports evaluation and prevents silent reference-store leakage.
