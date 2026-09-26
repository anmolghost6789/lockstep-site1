# Execution Plan Template

This reference defines the schema and markdown rendering for the Build Execution Plan. Generated alongside the Input Evaluation Report at the end of `/start-build-run` and presented to the user before they decide to proceed.

## Role of the Plan

The Execution Plan answers: "Given your inputs, scope selection, and detected conventions, here's what I'll build, in what order, and what you should expect." It helps the user confirm scope before expensive analysis and generation begins.

The plan is generated from data available after input classification (Step 3) — near-zero additional token cost.

## JSON Schema

```json
{
  "run_id": "string",
  "generated_at": "ISO 8601",
  "scope_selection": {
    "ddl": true, "dml": true, "dq": true,
    "pipeline": true, "tests": true
  },
  "table_inventory": {
    "total": 22,
    "by_layer": [
      {"layer": "L0 (Raw)", "count": 6, "tables": ["raw_iqvia_laad", "..."], "type": "Ingestion stubs"},
      {"layer": "L1 (Staging)", "count": 6, "tables": ["stg_rx_transactions", "..."], "type": "Cleanse + conform"},
      {"layer": "L2 (Dimensions)", "count": 6, "tables": ["d_product", "..."], "type": "SCD2/SCD1"},
      {"layer": "L3 (Facts)", "count": 4, "tables": ["f_rx_weekly", "..."], "type": "Incremental/MERGE"},
      {"layer": "Seeds", "count": 2, "tables": ["seed_veltrex_products", "..."], "type": "Static reference"}
    ]
  },
  "phase_plan": [
    {
      "phase": "/analyze-inputs",
      "what": "Convention resolution, canonical model, derivation catalog",
      "estimated_tables": "all",
      "depends_on": "Input eval approved"
    }
  ],
  "wave_preview": [
    {"wave": 0, "description": "Seeds (no dependencies)", "tables": ["seed_*"]},
    {"wave": 1, "description": "L0 Raw tables (source ingestion)", "tables": ["raw_*"]},
    {"wave": 2, "description": "L1 Staging (depend on L0)", "tables": ["stg_*"]},
    {"wave": 3, "description": "L2 Dimensions (depend on L1)", "tables": ["d_*"]},
    {"wave": 4, "description": "L3 Facts (depend on L2)", "tables": ["f_*"]}
  ],
  "convention_preview": {
    "naming": "snake_case with layer prefixes (raw_/stg_/d_/f_/seed_)",
    "scd2_marker": "detected or default value",
    "audit_columns": "detected or default set",
    "dq_framework": "detected or default",
    "load_strategy_mix": "SCD2: N, SCD1: N, incremental: N, full_refresh: N, static: N"
  },
  "known_gaps": [
    {
      "source": "input eval finding ID",
      "description": "brief gap description",
      "impact": "which artifacts affected",
      "assumption": "what the agent will assume"
    }
  ],
  "estimated_effort": {
    "analyze_inputs": "3-5 min",
    "plan_build": "3-5 min",
    "generate_ddl": "5-10 min",
    "generate_dml": "10-20 min",
    "generate_dq": "5-10 min",
    "generate_pipeline": "3-5 min",
    "generate_tests": "5-10 min",
    "evaluate_build": "3-5 min",
    "total": "40-70 min"
  },
  "complexity": "low | moderate | high"
}
```

## Markdown Rendering

```markdown
# Execution Plan

## Scope
[scope_selection items joined, e.g., "DDL, DML, DQ, Pipeline, Tests (all selected)"]

## Table inventory by layer

| Layer | Count | Tables | Type |
|---|---|---|---|
| [for each layer] | [count] | [tables truncated to 3 + "..."] | [type] |
| **Total** | **[total]** | | |

## Phase plan

| Phase | What happens | Tables | Depends on |
|---|---|---|---|
| [for each phase] | [what] | [estimated_tables] | [depends_on] |

## Dependency wave preview

[for each wave]
- **Wave [N]:** [description] — [table count] tables

## Convention preview (detected from inputs)
- Naming: [naming]
- SCD2 marker: [scd2_marker]
- Audit columns: [audit_columns]
- DQ framework: [dq_framework]
- Load strategies: [load_strategy_mix]

## Known gaps affecting generation

[for each gap]
**[[source]]** [description]
- Impact: [impact]
- Assumption: [assumption]

[or "No significant gaps. All selected artifacts can be generated at full quality."]

## Estimated effort
| Phase | Estimate |
|---|---|
| [for each phase] | [estimate] |
| **Total** | **[total]** |

Complexity: [complexity]
```

## How it fits in the flow

Generated at `/start-build-run` Step 4 alongside the Input Evaluation Report. Both are presented together. The user reviews quality ("are inputs good enough?") and scope ("here's what I'll build") before committing.

Written to `state/run_id_<ID>/discovery/execution_plan.json` and `execution_plan.md`.
