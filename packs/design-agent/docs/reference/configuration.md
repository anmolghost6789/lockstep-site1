# Configuration

## `workspace_layout.yaml`

The playground UI and run-scaffold contract for the package. It declares:

- the progress-seeding script (`.claude/skills/design-agent/scripts/seed_progress.py`) and
  the projection file (`progress.json`) at the run root;
- the four `inputs/` categories the UI renders (`instructions`, `requirements`,
  `source_inventory`, `additional_documents`) with labels, descriptions, and icons;
- the `context/` scaffold (`context/guidance`, `context/branding`, `context/reference`) and
  its three guidance children (`enterprise_context`, `domain_context`, `project_context`).

`outputs/` is documented there as the single working tree — numbered folders `01_inputs`
through `06_evaluation` plus `00_state`, with no per-run folder and no separate publish
step.

## `config/project_config.json`

The package's central defaults file (`version: "4.8-phase-split"`). Key sections:

| Section | Contents |
|---|---|
| `defaults.database_name_pattern`, `schema_name_patterns` | `{client}_db_{env}`; per-layer schema patterns for L0/L1/L2/L3+. |
| `defaults.layer_prefixes` | `rw_` (L0 tables), no L1 table prefix, `d_`/`f_`/`ref_`/`xref_` for L2 dimension/fact/reference/cross-reference tables. |
| `defaults.audit_columns` | Standard audit columns every table carries: `INRT_DT`, `INRT_BY`, `CYCL_TIME_ID`, `UPDT_DT`, `UPDT_BY`. |
| `defaults.surrogate_key` | Naming pattern `{TABLE_SHORT}_SK`, auto-increment transformation logic. |
| `defaults.standard_dq_checks` | Default check/criticality/threshold for business-key not-null, surrogate-key uniqueness, audit not-null, date-format, and year-month checks. |
| `reference_store` | `raw_path`/`processed_path` under `context/reference/`, governance defaults and built-in-pattern defaults (see below). |
| `run_settings` | Confidence thresholds, critical-confidence elements, empty-input guard behavior, IST timezone/timestamp format, terminal-cleanup behavior. |
| `context_hierarchy` | The four guidance tiers, their folder paths, and override rules. |
| `template_paths` | Paths to the four canonical `.xlsx` templates. |
| `supported_input_formats` | DOCX, TXT, XLSX, XLS, ZIP, PPTX, PPT, PDF, CSV, TSV, MD, PY, JSON, XML, YAML, YML. |
| `output_strategy` | `outputs/` layout paths; `archive_policy: disabled` — no `archive/` folders are ever created. |
| `runtime_code_policy` | Where generated runtime code may and may not live (see below). |
| `orchestration` | The four subagents, their spawn thresholds, and delegation rules. |
| `machine_readable_specs` | Paths to the five YAML contracts under `.claude/skills/design-agent/specs/`. |
| `traceability` | Allowed `References` prefixes: `INPUT`, `SRC`, `BRD`, `RULE`, `KPI`, `KBQ`, `PRODUCT`, `DQREQ`, `CTX`, `SUPPORT`, `HUMAN`, `CONFIG`, `REFSTORE`, `PKG`, `INFERRED`, `RISK`. |
| `agent_memory` | The five `memory/` files and what must never be stored in them. |

## Local Claude Code settings

| File | Status | Purpose |
|---|---|---|
| `.claude/settings.template.json` | Versioned. | Runtime env vars and Bash permission allow-list. Copy to `.claude/settings.json` before running. |
| `.claude/settings.json` | Gitignored. | Your local copy of the template above. |
| `.mcp.json` | Versioned, package root. | Declares `jira` and `github` MCP server endpoints. No skill in this package currently invokes either. |

There is no `.claude/settings.local.template.json` in this package (unlike some sibling
packages) — no phase skill here needs a locally-supplied credential today.

## Machine-readable specs (`.claude/skills/design-agent/specs/`)

These YAML files are contracts Claude reads as a machine-readable checklist; they are not
executable scripts. The phase `SKILL.md` files and the `.claude/skills/design-agent/utilities/`
files remain the human-readable source of detailed procedure.

| File | Purpose |
|---|---|
| `artifact_contract.yaml` | Expected output inventory and naming rules. |
| `template_contracts.yaml` | Workbook/sheet/header/summary layout rules for STTM, Data Model, DQ, and ER Diagram. |
| `validation_contracts.yaml` | Deterministic validation checks and severities. |
| `traceability_contract.yaml` | Mandatory row-level `References` rules and evidence prefixes. |
| `run_state_contract.yaml` | `run_state.json` schema and status values. |

## Knowledge base (`.claude/skills/design-agent/knowledge/`)

Domain knowledge the design phases apply, read on demand:

| File | Covers |
|---|---|
| `dq-patterns.md` | The standard DQ check catalog (Not NULL, Uniqueness, FK integrity, range, regex, etc.) and when to apply each. |
| `etl-domain.md` | Core dimensional-modeling concepts (dimension/fact tables, loading strategies). |
| `layering-logic.md` | Layer rules — L0 (always-on raw layer) and beyond. |
| `naming-conventions.md` | Naming priority order: client-specific > observed-in-source > package defaults. |
| `transformation-patterns.md` | The transformation-logic pattern catalog (direct mapping, and others). |

`/evaluate-design`'s standards-conformance check scores every generated artifact against
`naming-conventions.md`, `layering-logic.md`, and `dq-patterns.md` directly — a violation of
any of these caps that category's score at 6/10.

## Scripts (`.claude/skills/design-agent/scripts/`)

| Script | Invoked by | Purpose |
|---|---|---|
| `ingest_inputs.py` | `/start-design-run` | Converts snapshot files to UTF-8 sidecars plus `inputs_manifest.json`. |
| `render_design_md.py` | `/design-architecture` | Renders `target_model_design.md` deterministically from the canonical design JSONs. |
| `build_plan.py` | `/design-architecture` | Computes `plan.json` — generation waves via topological sort of FK/semantic relationships. |
| `generate_column_mappings.py` | Recovery only | Reconstructs `column_mappings.json` from a previously rendered `target_model_design.md`, if the JSON is damaged mid-run. |
| `generate_workbooks.py` | `/generate-artifacts` | The canonical, only workbook writer — loads templates, clones the `_template_reference` sheet per table, and writes STTM/Data Model/DQ/ER outputs. |
| `verify_workbook_headers.py` | `/generate-artifacts`, `/evaluate-design` | Compares every generated sheet's header row against its canonical template; any mismatch is fatal. |
| `verify_artifact_semantics.py` | `/evaluate-design` | Parses every DQ rule expression as SQL (via `sqlglot`), diffs ER Mermaid columns against the design JSON, and checks for encoding corruption. |
| `seed_progress.py` | Standalone/first run | Seeds the baseline `progress.json` at the workspace root. |

Dependencies (`.claude/skills/design-agent/scripts/requirements.txt`): `openpyxl>=3.1.2,<4.0.0`
and `sqlglot>=23.0.0`. `render_design_md.py`, `build_plan.py`, and `seed_progress.py` are
stdlib-only.

## Templates (`.claude/skills/design-agent/templates/`)

| Path | Contents |
|---|---|
| `templates/workbooks/STTM_TEMPLATE.xlsx`, `DATA_MODEL_TEMPLATE.xlsx`, `DQ_TEMPLATE.xlsx` | Each ships exactly two sheets: `table_tracker` (index) and `_template_reference` (structural blueprint, cloned per table and deleted before save). |
| `templates/workbooks/ER_DIAGRAM_TEMPLATE.xlsx` | Ships `table_tracker` plus role-named structural sheets `lineage_overview`, `table_relationships`, `layer_diagram_data` — these are used as-is and never deleted. |
| `templates/specs/*.md` | `data-model-spec.md`, `dq-spec.md`, `er-diagram-spec.md`, `sttm-spec.md` — the authored specification each workbook template implements. |
| `templates/memory/*.md` | Seed copies of the five `memory/` files, used as the expected format when a fresh package's `memory/` files are still empty. |

Formatting (the default single-blue `#5B9BD5` header theme) always comes from the template
file itself — the generator hardcodes no palette. If `context/branding/branding_preferences.json`
exists and a different theme is required, that is a template-swap decision made by a human
(replacing the `templates/workbooks/*.xlsx` set), not a reason to write a custom generator.

## Runtime code policy

Generated runtime code may exist only under `outputs/00_state/runtime_scratch/`, is logged
in `outputs/00_state/logs/runtime_code_manifest.json`, and is never left in
`.claude/skills/design-agent/`, `.claude/`, `config/`, `context/reference/`, `memory/`, the
project root, `inputs/`, or anywhere under `outputs/` except `00_state/runtime_scratch/`.
`/evaluate-design`'s hygiene check verifies containment; the closure tail deletes
`runtime_scratch/` on approval.

## Next

See [Command reference](../how-to-run/command-reference.md) for how each script is invoked
in context, or [Troubleshooting FAQ](troubleshooting-faq.md) for common configuration
issues.
