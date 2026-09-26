# INPUT FOLDER CONTRACT

## Purpose

`inputs/` is a stable, category-based run-intake area. The agent must not create run folders inside `inputs/`. For each run, 01 - Start_Run snapshots current run input contents into `outputs/00_state/input_snapshot/` and snapshots persistent guidance from root `context/guidance/` into `outputs/00_state/context_snapshot/guidance/`. Parsing/design works from those snapshots.

Persistent enterprise/domain/project context is intentionally outside `inputs/` under root `context/guidance/`. Governed reusable reference knowledge is under root `context/reference/`. Run-specific user directives are under `inputs/instructions/`.

## Canonical Input Scaffold

01 - Start_Run must ensure these input folders exist and each contains a `README.md` file:

```text
inputs/
  README.md
  instructions/README.md
  requirements/README.md
  source_inventory/README.md
  additional_documents/README.md
```

01 - Start_Run must also ensure these persistent context folders exist, with README guidance where appropriate:

```text
context/
  README.md
  branding/README.md
  guidance/README.md
  guidance/enterprise_context/README.md
  guidance/domain_context/README.md
  guidance/project_context/README.md
  reference/raw/
  reference/processed/
  reference/_metadata.json
```

`README.md` files define what each folder expects. They are package guidance files and are never counted as run input evidence. If a user wants to provide project notes, they must create a separate file such as `project_notes.md` in the appropriate folder.

## Supported Formats

The user may put files in any input or guidance folder using these formats:

```text
DOCX, TXT, XLSX, XLS, ZIP, PPTX, PPT, PDF, CSV, TSV, MD, PY, JSON, XML, YAML, YML
```

User-provided `.py` files are parsed as text only and must never be executed.

## Category Definitions

| Folder | Expected content | Parsed components |
|---|---|---|
| `inputs/instructions/` | Run-specific user directives only. Recommended filename stem: `user_instructions`. | `user_instructions.json` |
| `inputs/requirements/` | BRDs, requirements, scope, entities, use cases, acceptance criteria. | `data_requirements.json`; may also enrich related components when content includes rules, KPIs, KBQs, data products, DQ, or layering guidance. |
| `inputs/source_inventory/` | Source systems, schemas, tables, columns, metadata, sample extracts, source catalog exports. May include all available sources, not only used sources. | `source_inventory.json` |
| `inputs/additional_documents/` | Business rules, KPI definitions, key business questions, data product notes, layering instructions, DQ expectations, examples, comparison artifacts, meeting notes, appendices, validation references, and anything useful that does not fit another primary category. | `business_rules.json`, `kpi_definitions.json`, `key_business_questions.json`, `data_products.json`, `layering_instructions.json`, `dq_requirements.json`, `additional_documents.json`, or best-fit components by content. |
| `context/guidance/enterprise_context/` | Organization-wide standards/rules that apply across many projects for the enterprise client. | `enterprise_context.json` |
| `context/guidance/domain_context/` | Business-domain standards/rules inside the enterprise. Domain means a sub-area such as Commercial Sales, Manufacturing, Retail Banking, Claims, Wealth Management, Finance, or Supply Chain. | `domain_context.json` |
| `context/guidance/project_context/` | Current initiative implementation context. | `project_context.json` |
| `context/branding/` | Persistent branding/presentation assets or client presentation guidance. | branding/context metadata when needed; not part of core Standard Input Set unless referenced |
| `context/reference/` | Governed reusable historical/reference patterns. | advisory reference-store patterns only |

## Runtime-Created Midrun Uploads Folder

`inputs/midrun_uploads/` is intentionally absent from the initial package scaffold because it confuses users before the run starts. 02 - Standardize_Inputs creates it only after `outputs/00_state/standard_input_set/input_set_evaluation_report.md` exists and the agent is entering the clarification/Q&A phase.

When 02 - Standardize_Inputs creates it, include a short `README.md` explaining:

```text
Place only files requested or accepted during the current 02 - Standardize_Inputs clarification phase here.
Tell the agent which question or gap each file addresses.
The agent copies files from inputs/midrun_uploads/ to outputs/00_state/midrun_uploads/ and records them in midrun_uploads_manifest.json.
```

01 - Start_Run must ignore `inputs/midrun_uploads/` even if the folder exists from a prior/manual run.

## Context Folder Classification

The context hierarchy is physically separated by authority tier:

```text
context/guidance/enterprise_context/ -> enterprise_context.json
context/guidance/domain_context/     -> domain_context.json
context/guidance/project_context/    -> project_context.json
inputs/instructions/                 -> user_instructions.json
```

Classification guidance:

| Logical component | Scope | Classification signals |
|---|---|---|
| `enterprise_context.json` | Organization-wide standards/rules that apply across many projects for the enterprise client. | enterprise governance, global naming standards, data security/privacy policies, enterprise glossary, approved tech stack, retention rules. |
| `domain_context.json` | Business-domain standards/rules inside the enterprise. | domain glossary, domain KPIs, domain stewardship, domain DQ/modeling conventions, domain-level product standards. |
| `project_context.json` | Current initiative implementation context. | project charter, scope, target platform, environment, project naming guide, project-specific layer rules, architecture notes. |
| `user_instructions.json` | Run-specific directives from the user invoking the agent. | files under `inputs/instructions/`, filename stem `user_instructions`, or clear run-specific directives such as "for this run use...", "skip...", "only generate...". |

Ambiguous enterprise/domain/project context defaults to project context and must be flagged for clarification in 02 - Standardize_Inputs. Ambiguous user directives must be flagged for confirmation.

## Context Override Hierarchy

Guidance precedence, highest first:

1. Confirmed clarification answers.
2. User instructions for this run.
3. Project context.
4. Domain context.
5. Enterprise context.
6. Governed reference-store patterns.
7. Built-in package defaults.

Every lower-tier override of a higher tier requires explicit human confirmation before it is applied. The agent must never silently override higher-tier governance.

## User Instructions

A user-instructions file is optional. Recommended filename stem:

```text
user_instructions
```

Any supported extension is valid, for example:

```text
user_instructions.md
user_instructions.txt
User_Instructions.pdf
user_instructions.xlsx
```

If multiple user-instruction files are present, aggregate them. 01 - Start_Run parses free-form text into discrete directives with category, interpretation, affected stages, priority, potential conflicts, evidence, and status.

## Additional Documents

`inputs/additional_documents/` contains current-run material only. It is a single intake folder for useful files that do not belong to another primary category.

Each additional document should be classified inside `additional_documents.json` with fields such as:

```json
{
  "document_purpose": "requirements_context | source_context | design_example | mapping_example | dq_example | validation_reference | sample_output | comparison_document | known_good_example | meeting_note | appendix | miscellaneous_context | unclear | not_useful",
  "usefulness": "high | medium | low | not_useful",
  "how_used": "input_enrichment | design_context | validation_context | caution_only | not_used",
  "authority_level": "advisory | authoritative_if_confirmed | authoritative",
  "requires_human_confirmation": true
}
```

Additional documents are advisory by default. They must not override BRD/source/business-rule/context/human evidence unless the human explicitly confirms that an additional document is authoritative for a specific decision.

## Difference From Context/Reference

`inputs/additional_documents/` and `context/guidance/` are current-run/current-project evidence areas.

`context/reference/` is a reusable, governed knowledge base across runs. Current-run documents do not become reference-store patterns unless the evaluate-design closure tail asks and the human approves with governance metadata.

## Snapshot Rules

01 - Start_Run copies files from canonical input categories into:

```text
outputs/00_state/input_snapshot/
  instructions/
  requirements/
  source_inventory/
  additional_documents/
```

01 - Start_Run also copies persistent guidance files into:

```text
outputs/00_state/context_snapshot/guidance/
  enterprise_context/
  domain_context/
  project_context/
```

Initial 01 - Start_Run must not create or consume `inputs/midrun_uploads/`; 02 - Standardize_Inputs creates and consumes it only during the clarification phase.

Do not copy package `README.md` guidance files as user inputs. Folder README files are guidance only and must not become evidence. If project-specific content is found inside a README, flag it as misplaced guidance and ask the user to provide it as a separate file.

## No Terminal Input Cleanup

Input files are NEVER cleared by the agent. At every terminal run outcome (`completed`, `cancelled`, or unrecoverable `error`), `inputs/`, `outputs/00_state/`, and `outputs/` are all preserved as-is (owner decision, consistent with the other agents). The stale-input warning in /start-design protects the next run from accidentally re-running identical inputs; replacing input files for the next run is the user's action, not the agent's.
