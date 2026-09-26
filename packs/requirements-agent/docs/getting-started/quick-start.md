# Quick start

This is the fastest concrete path from a cloned package to a readiness report.
It assumes you have already completed [Prerequisites](prerequisites.md).

## 1. Open the package root and start Claude Code

```powershell
Set-Location .\skill-packages\requirements-skill-package
claude
```

## 2. Place evidence according to its meaning

Put material where its content belongs, not where its filename happens to
suggest. The first command ingests supported documents into a manifest before
the agent reasons about them, so evidence in the wrong category may be
invisible to the phase that needed it.

| Folder | Add this |
|---|---|
| `inputs/scope_and_requirements/` | Charters, prior BRDs/FRDs, scope statements, acceptance criteria. |
| `inputs/transcripts/` | Workshops, interviews, discovery calls, meeting notes. |
| `inputs/data_contracts/` | Schemas, mappings, source-system notes, interface contracts. |
| `inputs/templates/` | Approved BRD, FRD, URS, or Jira Markdown templates for this run. |
| `inputs/additional_documents/` | Policies, examples, legacy packs, and other supporting evidence. |
| `inputs/instructions/` | Output selection hints, scope focus, file-usage rules for this run. |
| `context/guidance/` | Durable enterprise, domain, and project rules that should apply across runs. |
| `context/branding/` | Branding and DOCX export preferences. Presentation only — must not change source facts. |
| `context/reference/` | Approved reference material and prior examples. Secondary context, not a license to copy facts. |

Use UTF-8 text where possible. Supported binary formats include common Office,
PDF, spreadsheet, and text formats; unreadable or unsupported inputs are
recorded as such rather than silently skipped.

## 3. Start the run

```text
/start-run
```

`/start-run` asks once which outputs you need (BRD, FRD, URS, Jira Story
Pack — any combination), ingests every input into a manifest, and produces an
input-readiness report at `outputs/01_input_evaluation/input_evaluation.md`.

## 4. Read the readiness report

Read the report and resolve blocking gaps — missing primary evidence the
selected outputs cannot be generated without. Non-blocking gaps are fine to
leave; they will remain visible as open items in the generated documents
instead of being silently invented away.

## 5. Run the next recommended command

Every phase ends by recommending exactly one next command. After a clean
`/start-run`, that is:

```text
/extract-requirements
```

From there the workflow continues one checkpoint at a time — see
[Phases](../workflow/phases.md) for the complete sequence, or
[Command reference](../how-to-run/command-reference.md) for what every command
reads and writes. Nothing auto-chains: the package always stops after a
command completes and waits for you to run the next one.
