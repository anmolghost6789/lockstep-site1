# Inputs

`inputs/` contains active source material for the current run. The agent scans this folder recursively during `/start-run`.

| Folder | Put here | How the agent treats it |
|---|---|---|
| `instructions/` | Run-specific user instructions, output selection notes, scope constraints, and file-usage directions. | Highest-priority run guidance. Instructions can tell the agent which documents to use or ignore, but they cannot create unsupported facts. |
| `templates/` | User-supplied BRD, FRD, URS, or Jira markdown templates. | Dynamically interpreted during generation. A template can change document structure; it is never compiled into a fixed schema. |
| `scope_and_requirements/` | Project charter, scope docs, existing BRD/FRD/URS fragments, partial requirements, business rules. | Primary evidence for business/user/functional requirements. |
| `transcripts/` | Meeting transcripts, stakeholder interviews, workshops, notes. | Primary evidence, but lower authority than approved scope/requirements unless instructions say otherwise. |
| `data_contracts/` | Source-system docs, schemas, STTMs, data dictionaries, interface/API contracts, DDL, sample mappings. | Primary evidence for data requirements, KPIs, feasibility, lineage, and data-quality rules. |
| `additional_documents/` | Anything else the user wants considered for this run: partial BRDs, legacy docs, use-case subsets, examples, decision logs, old packs. | Used according to `instructions/`. If not explicitly promoted to source evidence, it is treated as additional/reference evidence. |

Document branding and reusable style preferences now live in `context/branding/`. Durable enterprise/domain/project context lives in `context/guidance/`.

Recommended instruction file (any name and extension work - this is just a convenient default):

```text
inputs/instructions/user_instructions.md
```

You can equally use `inputs/instructions/instructions.docx`, `inputs/instructions/runbook.pdf`, or split content across a custom subfolder like `inputs/jira_guidelines/`. The agent classifies by content, not by filename, so use the layout that fits your workflow.

In whatever instruction file(s) you provide, explain which documents are authoritative, which are partial/reference-only, any use-case subset to focus on, and which outputs to generate. Also include any cross-cutting preferences (team roles for Jira subtasks, AC syntax preference, story-point scheme, story format template, naming conventions, etc.) - these can also live in any additional document you point the agent at.
