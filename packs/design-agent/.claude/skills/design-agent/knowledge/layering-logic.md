# LAYERING LOGIC

## L0: ALWAYS-ON RAW LAYER

L0 is ALWAYS present for every run, regardless of client instructions.

### L0 Rules

1. One L0 table for each 03 - Discover_Sources selected source table needed for downstream layers. Not every source table in the 02 - Standardize_Inputs source inventory needs an L0 table.
2. L0 tables are 1:1 column mirrors of their external source tables, plus audit columns.
3. No business logic at L0 - pure ingestion/mirroring.
4. Transformation for all source columns: `Direct mapping.`
5. Data types: preserve source data types unless the client explicitly requires normalization at L0.
6. Naming: client convention if provided; otherwise use configured defaults.
7. L0 replaces the external source for all subsequent layers. L1+ should normally reference L0 tables, not original external source tables.
8. If client inputs define their own L0 logic, use it only after verifying it does not break traceability.

### Determining Which Source Tables Need L0 Entries

Use 03 - Discover_Sources output, not the full source universe:

```text
For each table in source_discovery/selected_sources.json:
  create one L0 raw mirror table unless an explicit client instruction says otherwise.
```

02 - Standardize_Inputs `source_inventory.json` is the full verified source universe. It is not a selected-source list.

---

## DEFAULT LAYERING FALLBACK

When the client does not provide layering instructions, apply this algorithm.

### Step 1: Classify candidate tables

| Classification | Criteria | Typical Layer |
|---|---|---|
| Raw mirror | 1:1 copy of selected external source | L0 |
| Staged/cleansed | Renamed, cast, standardized, deduped version of source | L1 |
| Simple dimension | Single upstream table with SK and attributes | L2 |
| Complex dimension | Multiple upstream tables, conformance, survivorship, hierarchy | L2 or L3 |
| Reference table | Small lookup/classification table | L2 |
| Cross-reference / bridge | Many-to-many, mapping, or bridge logic | L2 or L3 |
| Simple fact | Measures from source plus semantic FK relationships | L2 or L3 |
| Complex fact | Multi-source joins, aggregations, calculations, or physical lookups | L3 or L4 |
| Aggregated/KPI | Summary, KPI, or mart table | L4+ |

### Step 2: Assign layers by dependency depth

```text
L0: all selected source raw mirrors
L1: staged/standardized versions of L0 tables that have downstream consumers
L2+: determined by physical transformation dependency depth
```

Depth definition:

```text
depth(table) = max(depth(physical_source_table) for physical_source_table in table.physical_sources) + 1
where depth(L0 table) = 0 and depth(L1 table) = 1
```

Group tables by depth:

```text
depth 2 -> L2
depth 3 -> L3
depth 4 -> L4
...
```

Sparse layer participation is allowed. Do not create fake pass-through tables just to make every entity appear in every layer. Create a table only when it serves a real modeling, transformation, conformance, DQ, or lineage purpose.

### Step 3: Same-height validation

A layer should contain tables at the same horizontal transformation depth.

```python
for layer in layers:
    depths = [compute_physical_depth(table) for table in layer.tables]
    assert max(depths) - min(depths) <= 1, f"Layer {layer} violates same-height rule"
```

If a layer contains tables at significantly different depths, split the layer or introduce sub-layers.

### Step 4: No same-layer physical transformation dependencies by default

This is the default policy:

```text
Same-layer logical/semantic relationships are allowed.
Same-layer physical transformation dependencies are not allowed by default.
```

Allowed same-layer semantic relationship:

```text
L2.f_sales has an FK relationship to L2.d_customer in the Data Model or ER Diagram.
```

Not silently allowed:

```text
L2.f_sales transformation reads generated L2.d_customer to derive customer_sk.
```

If a physical same-layer dependency is genuinely required, the agent must choose one of these before Gate 3:

1. Move the upstream table to an earlier layer.
2. Introduce explicit sub-layers such as L2A and L2B.
3. Ask for explicit Gate 3 approval as a documented exception.

Document any approved exception in:

```text
outputs/00_state/design/layer_architecture.json
outputs/00_state/design/design_validation_report.md
outputs/00_state/execution_plan/generation_order.json
```

### Step 5: DAG validation

The physical lineage graph must be a Directed Acyclic Graph:

```python
# No cycles allowed.
# Every table must be reachable from at least one selected source.
# No orphan tables unless they are explicit final outputs or approved reference tables.
# No unapproved same-layer physical dependencies.
```

Semantic relationships may form model references, but physical transformation dependencies must remain acyclic and layer-safe.

---

## WHEN CLIENT PROVIDES LAYERING INSTRUCTIONS

If the client specifies layers:

1. Use the client layer names and purposes where possible.
2. Still validate L0, same-height, DAG, and same-layer dependency rules.
3. If client instructions require a same-layer physical dependency, present it at Gate 3 as an explicit exception.
4. Do not silently override client layering; ask or document the exception.
5. Always include L0 unless the client explicitly says not to and the human approves the risk.

---

## LAYER NAMING CONVENTIONS (DEFAULTS)

| Layer | Schema Prefix | Table Prefix | Example |
|---|---|---|---|
| L0 | `{client}_rw` | `rw_` | `rw_jpm_trn` |
| L1 | `{client}_wk` | `wk_` or `stg_` | `az_wk_jpm_trn` |
| L2 | `{client}_dw` | `d_`, `f_`, `ref_`, `xref_` | `d_atc`, `f_trn` |
| L3+ | `{client}_dm` | entity-specific | per requirements |
| Sub-layer | same as parent unless client defines otherwise | layer suffix in metadata | L2A, L2B |

These are defaults. Client conventions override them when they do not break lineage clarity.
