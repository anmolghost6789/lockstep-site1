# INPUT SCHEMA DEFINITIONS

> **Current runtime contract (JSON-as-source, thin index).** /start-design writes exactly TWO standard-input-set files: `input_index.json` (thin pointer index over the ingested sidecars) and `input_set_evaluation_report.md` (readiness report, including the assumptions section). The per-component JSON schemas below (sections 1-2) are retained as **classification vocabulary** — they define what to look for and how to categorize evidence when building the index and the report — but they are NOT written as separate files anymore. Section 3 defines the source-discovery contract (the second half of /start-design). Section 4's canonical design shapes live in `.claude/skills/design-architecture/SKILL.md` (`column_mappings.json` with `layers`/`tables`/`mappings` blocks + `dq_rules_design.json`).

## OVERVIEW: FOUR SCHEMA GROUPS

1. **Ideal Input Set (01 - Start_Run output)** - structured extraction from the run-specific input snapshot.
2. **Standard Input Set (02 - Standardize_Inputs output)** - enriched, validated input components plus evaluation/clarification artifacts. No design artifacts.
3. **Source Discovery (03 - Discover_Sources output)** - selected/rejected/missing source decisions for the current run.
4. **Design Artifacts (04 - Design output)** - architecture design outputs: target model, lineage, column mappings, layer architecture, and DQ rules.

v4.7 uses physically separated context folders: persistent enterprise/domain/project guidance lives under root `context/guidance/{enterprise_context,domain_context,project_context}/`, while run-specific user directives live under `inputs/instructions/` and parse to `user_instructions.json`. Lower tiers may override higher tiers, but every override requires explicit human clarification confirmation. v4.7 also uses a single `additional_documents.json` component for current-run additional documents and keeps governed reusable reference patterns under root `context/reference/`. `gaps_report.md` and `input_set_evaluation_report.md` are evaluation artifacts, not business input categories.

---

## 1. IDEAL INPUT SET (01 - Start_Run output)

Stored in `outputs/00_state/ideal_input_set/`.

### enterprise_context.json
```json
{
  "run_id": "string",
  "enterprise_name": "string | null",
  "enterprise_domain": "string | null",
  "standards": [
    {
      "standard_id": "string",
      "standard_type": "naming | platform | security | privacy | dq | data_modeling | retention | glossary | other",
      "description": "string",
      "applies_to": ["string"],
      "source_evidence": ["file:section/page/sheet"]
    }
  ],
  "governance_rules": [
    {
      "rule_id": "string",
      "rule_type": "string",
      "rule_description": "string",
      "source_evidence": ["string"]
    }
  ],
  "enterprise_glossary": [
    { "term": "string", "definition": "string", "aliases": ["string"], "source_evidence": ["string"] }
  ],
  "data_quality_policies": [
    { "policy_name": "string", "description": "string", "thresholds": "object | null", "source_evidence": ["string"] }
  ],
  "known_conflicts_with_project_context": []
}
```

### domain_context.json
Business domain within the enterprise (e.g., Commercial Sales, Manufacturing, Retail Banking). Distinct from the industry the enterprise operates in. Applies across all projects within that domain.

```json
{
  "run_id": "string",
  "domain_name": "string | null",
  "parent_enterprise": "string | null",
  "sub_domains": ["string"],
  "domain_owner": "string | null",
  "domain_steward": "string | null",
  "domain_description": "string | null",
  "domain_glossary": [
    { "term": "string", "definition": "string", "aliases": ["string"], "source_evidence": ["string"] }
  ],
  "domain_kpis": [
    { "kpi_name": "string", "definition": "string", "formula": "string | null", "grain": "string | null", "source_evidence": ["string"] }
  ],
  "domain_standards": [
    {
      "standard_id": "string",
      "standard_type": "naming | dq | governance | data_modeling | retention | other",
      "description": "string",
      "applies_to": ["string"],
      "source_evidence": ["string"]
    }
  ],
  "domain_data_products": ["string"],
  "domain_dq_rules": [
    { "rule_id": "string", "description": "string", "criticality": "C | NC | null", "source_evidence": ["string"] }
  ],
  "evidence_sources": ["string"],
  "known_conflicts_with_enterprise_context": [],
  "known_conflicts_with_project_context": [],
  "needs_human_clarification": "boolean"
}
```

### project_context.json
```json
{
  "run_id": "string",
  "client_name": "string | null",
  "project_name": "string | null",
  "domain": "string | null",
  "target_platform": "string | null",
  "implementation_scope": { "in_scope": ["string"], "out_of_scope": ["string"] },
  "environment": "string | null",
  "database_schema_context": "object | null",
  "has_layering_instructions": "boolean | null",
  "has_naming_conventions": "boolean | null",
  "naming_conventions_discovered": "object | null",
  "project_specific_overrides": [
    { "overrides_enterprise_item": "string", "override_description": "string", "evidence": ["string"] }
  ],
  "special_instructions": "string | null",
  "evidence_sources": ["string"],
  "collected_at": "IST ISO timestamp"
}
```

### user_instructions.json
Run-specific directives from the individual user invoking the agent. Parsed primarily from `inputs/instructions/user_instructions.*` or other clearly directive files inside `inputs/instructions/`. Format is non-structured / free-form. Multiple matching files are aggregated. The narrowest tier in the context hierarchy.

```json
{
  "run_id": "string",
  "source_files": ["string"],
  "raw_text": "string",
  "instructions": [
    {
      "instruction_id": "UI-NNN",
      "source_excerpt": "string",
      "category": "scope | sources | layering | naming | dq | output | process | design | other",
      "interpretation": "string",
      "applies_to_stages": ["start_design | design_architecture | generate_artifacts | evaluate_design"],
      "priority": "high | medium | low",
      "potential_conflicts_with": [
        { "tier": "enterprise | domain | project", "subject": "string", "severity": "normal | elevated | high" }
      ],
      "evidence": ["string"],
      "status": "pending | applied | deferred_with_confirmation | rejected_with_confirmation",
      "status_recorded_at": "IST ISO timestamp | null",
      "status_reason": "string | null",
      "human_confirmation_id": "string | null"
    }
  ],
  "total_directives": "integer",
  "applied_count": "integer",
  "deferred_count": "integer",
  "rejected_count": "integer",
  "unaddressed_count": "integer",
  "evidence_sources": ["string"],
  "collected_at": "IST ISO timestamp"
}
```

### data_requirements.json
```json
{
  "project_name": "string | null",
  "project_description": "string | null",
  "business_objective": "string | null",
  "scope": { "in_scope": ["string"], "out_of_scope": ["string"] },
  "target_entities": [
    {
      "entity_name": "string",
      "entity_description": "string | null",
      "entity_type": "dimension | fact | reference | cross_reference | bridge | aggregate | unknown",
      "source_objects": [{ "name": "string", "description": "string | null" }],
      "target_layer": "string | null",
      "evidence": ["string"]
    }
  ],
  "assumptions_constraints": ["string"],
  "acceptance_criteria": ["string"]
}
```

### source_inventory.json
This is the full available source universe, not the selected-source list.

```json
{
  "sources": [
    {
      "source_system": "string",
      "database": "string | null",
      "schema": "string | null",
      "tables": [
        {
          "table_name": "string",
          "table_description": "string | null",
          "row_count": "integer | null",
          "source_file": "string | null",
          "columns": [
            {
              "column_name": "string",
              "data_type": "string | null",
              "description": "string | null",
              "is_primary_key": "boolean | null",
              "is_nullable": "boolean | null",
              "sample_values": ["string | null"],
              "evidence": ["string"]
            }
          ]
        }
      ]
    }
  ],
  "source_relationships": [
    {
      "from_table": "string",
      "from_column": "string",
      "to_table": "string",
      "to_column": "string",
      "relationship_type": "FK | inferred_fk | lookup | same_concept | unknown",
      "confidence": "integer 0-100",
      "evidence": ["string"]
    }
  ]
}
```

### business_rules.json
```json
{
  "rules": [
    {
      "entity_name": "string | null",
      "rule_id": "string",
      "rule_type": "filter | transformation | aggregation | enrichment | standardization | derivation | lookup | deduplication | survivorship | hierarchy | exception | other",
      "rule_description": "string",
      "source_columns_involved": ["string"],
      "target_column_affected": "string | null",
      "source_section": "string | null",
      "priority": "integer | null",
      "evidence": ["string"]
    }
  ],
  "global_rules": [
    { "rule_id": "string", "rule_description": "string", "rule_type": "string", "evidence": ["string"] }
  ]
}
```

### kpi_definitions.json
```json
{
  "kpis": [
    {
      "kpi_name": "string",
      "kpi_description": "string | null",
      "calculation_logic": "string | null",
      "source_columns": ["string"],
      "unit": "string | null",
      "aggregation_level": "string | null",
      "grain": "string | null",
      "priority": "integer | null",
      "evidence": ["string"]
    }
  ]
}
```

### key_business_questions.json
```json
{
  "questions": [
    {
      "question_id": "string",
      "question_text": "string",
      "priority": "high | medium | low",
      "data_domains_involved": ["string"],
      "expected_answer_type": "string | null",
      "required_entities_or_kpis": ["string"],
      "evidence": ["string"]
    }
  ]
}
```

### data_products.json
```json
{
  "products": [
    {
      "product_name": "string",
      "description": "string | null",
      "consumers": ["string"],
      "required_entities": ["string"],
      "required_kpis": ["string"],
      "refresh_frequency": "string | null",
      "delivery_format": "string | null",
      "evidence": ["string"]
    }
  ]
}
```

### layering_instructions.json
```json
{
  "source": "client_provided | enterprise_standard | project_context | default_fallback",
  "instructions": "string | null",
  "layer_definitions": [
    {
      "layer_id": "string",
      "layer_name": "string",
      "description": "string",
      "schema_prefix": "string | null",
      "table_prefix": "string | null",
      "loading_strategy": "string | null"
    }
  ],
  "same_layer_dependency_policy": "string | null",
  "evidence": ["string"]
}
```

### dq_requirements.json
```json
{
  "dq_policies": [
    {
      "policy_id": "string",
      "policy_name": "string",
      "description": "string",
      "applies_to": ["table | column | entity | KPI | layer | all"],
      "criticality": "C | NC | null",
      "threshold_value": "integer | string | null",
      "evidence": ["string"]
    }
  ],
  "dq_waivers": [
    { "waiver_id": "string", "description": "string", "applies_to": ["string"], "evidence": ["string"] }
  ],
  "reconciliation_requirements": [
    { "requirement_id": "string", "description": "string", "evidence": ["string"] }
  ]
}
```

### additional_documents.json
Current-run additional documents that do not fit a primary category, including prior STTMs, prior data models, DQ examples, sample outputs, comparison documents, known-good examples, meeting notes, appendices, validation references, or miscellaneous useful facts. These are different from reusable `context/reference/` patterns.

```json
{
  "documents": [
    {
      "filename": "string",
      "input_category": "additional_documents",
      "document_purpose": "requirements_context | source_context | design_example | mapping_example | dq_example | validation_reference | sample_output | comparison_document | known_good_example | meeting_note | appendix | miscellaneous_context | unclear | not_useful",
      "description": "string",
      "content_summary": "string",
      "usefulness": "high | medium | low | not_useful",
      "how_used": "input_enrichment | design_reference | validation_reference | caution_only | not_used",
      "authority_level": "advisory | authoritative_if_confirmed | authoritative | unknown",
      "requires_human_confirmation": "boolean",
      "must_not_override_current_inputs": true,
      "mapped_components": ["data_requirements.json | business_rules.json | kpi_definitions.json | source_inventory.json | other"],
      "conflicts": ["string"],
      "evidence": ["string"]
    }
  ]
}
```

### gaps_report.md
Sections: Critical Gaps, Important Gaps, Minor Gaps, Context Hierarchy Conflicts, File/Parsing Issues, Assumptions/Defaults, Questions To Carry Into 02 - Standardize_Inputs.

### input_set_evaluation_report.md
Created in 02 - Standardize_Inputs, not 01 - Start_Run. It evaluates the input set and then asks questions.

---

## 2. STANDARD INPUT SET (02 - Standardize_Inputs output - INPUT QUALITY ONLY)

Stored in `outputs/00_state/standard_input_set/`.

Contains enriched versions of all structured input components plus:

### human_clarifications.json
```json
{
  "clarifications": [
    {
      "id": "HC-NNN",
      "stage": "02 - Standardize_Inputs | 03 - Discover_Sources | 04 - Design | 07 - Review",
      "question_id": "string | null",
      "question": "string",
      "context": "string",
      "human_response": "string",
      "timestamp": "IST ISO",
      "applied_to": ["string"],
      "learning_value": "high | medium | low"
    }
  ]
}
```

### input_set_evaluation_report.md
Detailed report that first evaluates input quality and then asks the human all required questions. See `.claude/skills/start-design/SKILL.md`.

### validation_report.md
Overall confidence, per-component scores, resolved issues, remaining assumptions, enterprise/project conflict handling, file parsing quality, and midrun upload handling.

### confidence_assessment.json
```json
{
  "overall_confidence": "integer 0-100",
  "per_component": {
    "enterprise_context": { "confidence": "integer", "note": "string" },
    "domain_context": { "confidence": "integer", "note": "string" },
    "project_context": { "confidence": "integer", "note": "string" },
    "user_instructions": { "confidence": "integer", "note": "string" },
    "additional_documents": { "confidence": "integer", "note": "string" },
    "source_inventory": { "confidence": "integer", "note": "string" },
    "business_rules": { "confidence": "integer", "note": "string" }
  },
  "critical_elements": [
    { "element": "string", "item": "string", "confidence": "integer", "blocks_normal_gate": "boolean" }
  ],
  "unresolved_gaps": [{ "id": "string", "description": "string", "severity": "string", "impact": "string" }],
  "critical_blockers": [{ "id": "string", "element": "string", "confidence": "integer", "blocks_normal_gate": "boolean" }],
  "total_unresolved": "integer"
}
```

### midrun_uploads_manifest.json
```json
{
  "run_id": "string",
  "uploads": [
    {
      "upload_id": "MRU-001",
      "original_path": "inputs/midrun_uploads/file.xlsx",
      "run_path": "outputs/00_state/midrun_uploads/{IST_timestamp_slug}/file.xlsx",
      "requested_by_question_id": "string | null",
      "parsed": "boolean",
      "applied_to_components": ["source_inventory.json"],
      "notes": "string"
    }
  ]
}
```

02 - Standardize_Inputs does not contain `column_mappings.json`, `layer_architecture.json`, `dq_rules.json`, `lineage_traces.json`, or target model design artifacts. Those belong to 04 - Design.

---

## 3. SOURCE DISCOVERY (/start-design source-discovery output)

Stored in `outputs/00_state/source_discovery/`. This is the only selected-source run folder for the current run. Exactly TWO files are written — every candidate is stated exactly once in `source_decisions.json`; the concept list, matches, selected/rejected splits, and evidence map are all views of it and are NOT written as separate files.

### source_decisions.json
```json
{
  "run_id": "string",
  "required_concepts": { "SC-001": "one-line business concept" },
  "decisions": [
    {
      "id": "SD-001",
      "entity": "string — business entity/concept this source serves",
      "source_system": "string",
      "source_table": "string",
      "status": "selected | rejected | missing",
      "rationale": "string — why selected/rejected, or what is missing",
      "evidence": ["input_index id or sidecar pointer"],
      "gaps": ["string — unresolved columns, grain doubts, delivery risks"],
      "confidence": "integer 0-100"
    }
  ],
  "reference_store_audit": {
    "store_present": "boolean",
    "patterns_consulted": ["string"],
    "influence": "advisory only — current-run evidence wins"
  },
  "waivers": []
}
```

### source_gap_report.md
Human-facing view: selected-sources table, gaps table (missing source concepts, ambiguous candidates, unresolved source columns) with design impact and mitigation, verdict.

### source_catalog_delta.json (optional)
Only created if the source-discovery step finds source metadata not already indexed earlier in /start-design.

/design-architecture must design only from `source_decisions.json` entries with `status: "selected"` plus explicit human-approved waivers. It must not use a table only because it appears in the input index.

## 4. DESIGN ARTIFACTS (/design-architecture output — THE HEART)

Stored in `outputs/00_state/design/`. JSON-as-source: the model states each design fact exactly once in the two canonical JSONs; every human-readable view is script-rendered.

### column_mappings.json (canonical)
Shape defined in `.claude/skills/design-architecture/SKILL.md`: a `layers` array (per-layer id/title/schema/database), a `tables` array (per-table purpose, grain, key_strategy, table_type, load_strategy, frequency, schema/database overrides), and a `mappings` array (one entry per target column with source, transformation, filter_conditions, join_conditions, source_reference).

### dq_rules_design.json (canonical)
Shape defined in `.claude/skills/design-architecture/SKILL.md`: a `rules` array with rule_id, rule_type, severity, bare-predicate dq_rule_expression (R8), threshold_value (R7), and source_reference. Every table has at least one rule (R6).

### target_model_design.md (rendered view)
Produced only by `scripts/render_design_md.py` from the two JSONs — per-layer sections, per-table metadata lines, column tables, DQ rule tables. Used for human review. Never hand-written or hand-edited.

### design_brief.md (hand-written judgment)
Short prose: business framing, layers, table counts per layer, key decisions, open questions. No restated per-column facts.

## 5. REFERENCE STORE SCHEMAS

Stored in `context/reference/processed/`. Every processed pattern must follow `.claude/skills/design-agent/utilities/reference-store-governance.md`. Missing metadata must use conservative defaults: `reuse_scope=client`, `approved_for_reuse=false`, `approval_status=provisional`, `sensitivity=client_specific`, and `approved_for_cross_client_reuse=false`.

### source_usage_patterns.json
```json
{ "patterns": [{ "domain": "pharma", "entity_type": "dimension", "entity_name": "d_atc", "sources_used": ["JPM_MST_ATC"], "frequency": 5, "clients": ["AZ", "Pfizer"] }] }
```

### column_mapping_patterns.json
```json
{ "patterns": [{ "column_pattern": "*_SK", "role": "surrogate_key", "transformation": "Auto Generated...", "frequency": 100 }, { "column_pattern": "CMPNY_CD", "typical_source": "company_master", "typical_role": "business_key", "frequency": 8 }] }
```

### transformation_catalog.json
```json
{ "transformations": [{ "pattern": "SK_LOOKUP", "description": "Lookup business key in dimension to get SK", "template": "Lookup {bk} in {dim} to get {sk}.", "frequency": 45 }] }
```

### entity_design_patterns.json
```json
{ "patterns": [{ "entity_type": "dimension", "domain": "pharma", "typical_columns": ["*_SK", "*_CD", "*_NM", "audit_cols"], "typical_grain": "one code per row", "example_entities": ["d_atc", "d_cmpny"] }] }
```

### dq_patterns_history.json
```json
{ "patterns": [{ "column_role": "business_key", "checks_applied": ["Not NULL"], "criticality": "C", "threshold": 10, "success_rate": 98 }] }
```

### domain_knowledge.json
```json
{ "domains": [{ "domain": "pharma", "key_concepts": ["ATC classification", "pack codes", "company hierarchies"], "common_sources": ["JPM", "Intage", "Encise"], "notes": "string" }] }
```
