# Inputs and Context Model

## Principle

Separate active run evidence from durable context.

- `inputs/` is the active evidence drop-zone for the current run.
- `context/` is stable guidance/reference/branding that may apply across runs.
- `.claude/skills/requirements-agent/assets/` contains agent-owned templates and bundled resources, not user evidence.

## Folder semantics

These are **default semantic hints**, not required filenames. Users may add custom subfolders under `inputs/` or `context/` (e.g. `inputs/jira_guidelines/`, `inputs/interviews/`, `context/guidance/compliance/`, `context/branding/client-acme/`); the agent scans them too. Files may be `.md`, `.docx`, `.pdf`, `.txt`, `.csv`, `.xlsx`, `.json`, or `.yaml` — content classification, not extension, decides the role.

| Location | Meaning | Default evidence role |
|---|---|---|
| `inputs/instructions/**` | Run-specific instructions and file-usage rules. Any filename, any extension. | Governing run instruction. |
| `inputs/scope_and_requirements/**` | Approved or draft scope/requirements material. Any filename. | Primary evidence. |
| `inputs/transcripts/**` | Stakeholder conversations and workshops. Any filename. | Primary evidence, but may need confirmation. |
| `inputs/data_contracts/**` | Schemas, STTMs, data dictionaries, interfaces, mappings. Any filename. | Primary data evidence. |
| `inputs/additional_documents/**` | Mixed run-specific additional documents, legacy packs, partial BRDs, examples. Any filename. | Supporting unless instructions promote it. |
| `inputs/<user-custom-subfolder>/**` | Any subfolder the user creates under `inputs/` (e.g. `inputs/jira_guidelines/`). Classify by content; treat as `additional_document` if no other role fits. | Inferred from content. |
| `context/guidance/**` | Enterprise/client standards, domain concepts, durable project context, and any custom guidance the user files here. Any filename — `enterprise.md`, `enterprise_standards.docx`, `domain_context.pdf`, `project_history.txt`, `all_context.md`, or nested subfolders like `context/guidance/compliance/`. Sub-classification (enterprise vs domain vs project) is by content scan, not filename. | Standing guidance. |
| `context/branding/**` | Branding, export preferences, logos, style. Any filename matching `*branding*`, `*preferences*`, `docx*`, or anything the user drops in this folder. | Presentation guidance. |
| `context/reference/**` | Reusable reference docs or prior implementations. Any filename. | Reference only. |

**No filename in this table is required.** Discover roles, governance, branding,
and requirements by content and location. Template filenames are conveniences,
not routing keys or evidence of meaning.

## Priority rules

1. Explicit `inputs/instructions/` directions govern how files should be used.
2. Active primary evidence in `inputs/scope_and_requirements/`, `inputs/transcripts/`, and `inputs/data_contracts/` drives generated requirements.
3. `inputs/additional_documents/` is used according to instructions. Without instructions, it supports terminology/style/comparison but should not create high-confidence requirements by itself.
4. `context/guidance/` constrains interpretation and terminology. It does not override active input evidence unless it is a compliance/enterprise rule.
5. `context/reference/` and `context/branding/` do not create requirements by default.

## Required source labeling

Every extracted fact must include `source_role`:

- `primary_scope`
- `primary_transcript`
- `primary_data_contract`
- `run_instruction`
- `additional_document`
- `enterprise_guidance`
- `domain_guidance`
- `project_guidance`
- `branding_context`
- `reference_context`
- `agent_inference`

Generated content with `agent_inference` must be marked as an assumption unless it is purely structural.
