# How to Prepare Inputs

The Requirements Agent works with whatever inputs you have. More relevant evidence produces stronger outputs.

## Active run inputs

Place current-run files under `inputs/`:

| Folder | What goes here |
|---|---|
| `inputs/instructions/` | Run-specific instructions, selected outputs, file-usage notes, scope focus. |
| `inputs/scope_and_requirements/` | Project charters, existing BRDs/FRDs/URS drafts, requirement specs, scope docs. |
| `inputs/transcripts/` | Meeting transcripts, interview notes, workshop recordings. |
| `inputs/data_contracts/` | Schema definitions, source-system docs, STTMs, APIs, mappings, data dictionaries. |
| `inputs/additional_documents/` | Partial/legacy/mixed-scope docs, examples, prior packs, or documents to use according to instructions. |

## Stable context

Place reusable context under `context/`:

| Folder | What goes here |
|---|---|
| `context/guidance/` | Enterprise, domain, and project context that should apply across runs. |
| `context/branding/` | Logos, branding preferences, DOCX export preferences. |
| `context/reference/` | Prior implementations, approved examples, external standards, reusable frameworks. |

## What improves output quality

| Input | Effect |
|---|---|
| Clear instructions | Correct scope, output selection, and file usage. |
| Project charter / scope | Sharper scope boundaries and fewer assumptions. |
| Existing requirements | Stronger BRD, URS, FRD, traceability, and Jira stories. |
| Transcripts | Richer use cases, KBQs, user needs, and acceptance criteria. |
| Data contracts | Stronger DR, KPI feasibility, FRD data behavior, and data story criteria. |
| Branding preferences | Better final document presentation and DOCX exports. |

## Thin inputs

When evidence is thin, the agent must mark sections with `[INSUFFICIENT INPUT]` or `[ASSUMPTION]` rather than hallucinating.
