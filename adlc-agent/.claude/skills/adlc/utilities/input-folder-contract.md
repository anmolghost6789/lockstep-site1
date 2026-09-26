# INPUT FOLDER CONTRACT

## Layout

```text
inputs/
  instructions/   # intent.md (the business goal) and run-specific directives
  requirements/   # BRDs, process documents, acceptance criteria
  sources/        # system descriptions, API specs, schemas, sample data (non-production)
  classification.json   # optional: {"path": "confidential"} per file
```

## Classification

Every input has a data classification from `config/project_config.json > data_classification.levels`. A file is classified by, in order: an entry in `inputs/classification.json`, a first-line marker such as `Classification: confidential`, or the default `internal`.

Inputs above `copy_into_artifacts_max_level` are referenced by path only. Their content never goes into artifacts, prompts, memory or chat.

## Supported inputs

Markdown, text, PDF, Word, spreadsheets, CSV, JSON, YAML, OpenAPI specs and code files. Code in `inputs/` is read as text and never executed.

## Snapshots and staleness

At /discover-define, record a fingerprint (path, size, sha256) of every input in `adlc/.state/index/inputs.json`. On re-entry, compare fingerprints: unchanged inputs are not re-read; changed inputs trigger a targeted update and, if requirements change, the change-impact routing rules.

If the inputs are identical to a previous completed run, say so and ask whether this is a new intent or a re-run before continuing.

## Empty inputs

If there is no intent in `$ARGUMENTS`, `inputs/instructions/intent.md` or a linked ticket, explain where to put one and stop. Don't invent an intent.
