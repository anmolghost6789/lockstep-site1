# Requirements Agent

Requirements Agent is the evidence-to-requirements stage of the
data-engineering delivery lifecycle. It reads supplied business evidence,
preserves what the evidence actually says, records gaps and contradictions
instead of guessing past them, and produces only the requirement documents
the user selected: a BRD, FRD, URS, and/or Jira Story Pack.

It is deliberately not a generic document writer. The run folder contains the
evidence snapshot, knowledge concepts, traceability, state, generated
documents, and evaluation results needed to review or resume the work.

## What this package owns

| Use it for | Do not use it for |
|---|---|
| Turning workshops, transcripts, briefs, policies, source descriptions, and existing documents into requirements. | Designing a target data model, producing DDL/DML, deploying a pipeline, or executing data tests. |
| Maintaining traceability from a requirement back to its source evidence. | Filling a gap with an invented rule merely to make a document look complete. |
| Creating review-ready documents and draft Jira stories. | Publishing to Jira without an explicit user decision. |

The typical handoff is Requirements -> Design. Design consumes reviewed
business scope, functional behavior, data requirements, rules, and open
items; it does not need an unreviewed chat summary.

## Where this fits in the lifecycle

```text
Requirements -> Design -> Build -> Deploy -> Test
```

This package is the first of five delivery skill packages in this repository
(`requirements-skill-package`, `design-skill-package`, `build-skill-package`,
`deploy-skill-package`, `test-skill-package`), each with its own owned
outputs and lifecycle stage. `de-discovery` can run before this lifecycle to
establish evidence and readiness for a new or poorly-understood initiative.
`orchestrator-skill-package` coordinates all five delivery packages in the
hosted Guided UI; it does not perform requirements work itself. See
[Overview](docs/getting-started/overview.md) for the full concept model
(evidence, the knowledge layer, RA-BLOCK ownership, traceability).

## Prerequisites

- A current Claude Code installation and an authenticated Claude account.
- Python 3.10+ (for document ingestion, deterministic validation, and
  Markdown-to-DOCX export).
- Optional: Jira credentials, only if this run needs `/publish-to-jira`.

```powershell
Set-Location .\skill-packages\requirements-skill-package
Copy-Item .claude\settings.template.json .claude\settings.json
python -m pip install -r .claude\skills\requirements-agent\scripts\requirements.txt
claude
```

Open **this package root** in Claude Code, not `skill-packages/` and not
`.claude/` — Claude Code discovers `CLAUDE.md` and `.claude/` from the current
project folder, and opening the wrong folder can prevent the right rules,
commands, and hooks from loading.

If your project needs Jira publication, copy
`.claude/settings.local.template.json` to the gitignored
`.claude/settings.local.json` and configure the approved integration there or
through environment variables. Do not put an API token in a source document,
a generated Jira pack, or the committed settings template. You can complete
every requirement phase without Jira access. See
[Prerequisites](docs/getting-started/prerequisites.md) for the full setup
detail and [Jira integration](docs/integrations/jira.md) for credential
handling.

## Prepare the workspace

Place material according to its meaning, not its filename. The first command
ingests supported documents into a manifest before the agent reasons about
them.

| Folder | Add this | Why it matters |
|---|---|---|
| `inputs/scope_and_requirements/` | Charters, prior BRDs/FRDs, scope statements, acceptance criteria. | Primary requirement evidence. |
| `inputs/transcripts/` | Workshops, interviews, discovery calls, meeting notes. | Captures stakeholder intent and unresolved questions. |
| `inputs/data_contracts/` | Schemas, mappings, source-system notes, interface contracts. | Grounds data requirements and feasibility. |
| `inputs/templates/` | Approved BRD, FRD, URS, or Jira Markdown templates. | Controls the shape of the selected document; run-local templates are authoritative over package defaults. |
| `inputs/additional_documents/` | Policies, examples, legacy packs, and supporting evidence. | Adds context without replacing stronger sources. |
| `inputs/instructions/` | Run-specific instructions and file-usage rules. | Governs how other inputs should be used. |
| `context/guidance/` | Enterprise, domain, and project guidance. | Durable rules that apply across runs. |
| `context/branding/` | Branding and export preferences. | Presentation only; it must not change source facts. |
| `context/reference/` | Approved reference material and prior examples. | Secondary context, not a license to copy facts. |

Use UTF-8 text where possible. The ingestion script can read common Office,
PDF, spreadsheet, and text formats; it records unsupported or unreadable
inputs instead of pretending they were used. See
[Inputs and outputs](docs/workflow/inputs-and-outputs.md) for the complete
folder-by-folder model, including priority rules and required source
labeling.

## End-to-end workflow

```text
Put evidence in inputs/
        |
/start-run -> select BRD, FRD, URS, and/or Jira; ingest and assess readiness
        |
/extract-requirements -> create evidence-backed concepts, links, assumptions, and gaps
        |
/generate-deliverables or one /generate-... command -> write selected documents
        |
/evaluate-run -> check fidelity, coverage, consistency, and traceability
        |
optional /revise-run <specific feedback> -> patch affected concepts and document blocks
        |
optional /publish-to-jira -> explicit external publication
```

Each command is a checkpoint. It writes state, reports what it completed or
could not complete, recommends the next command, and stops. Running a later
command is the user's approval to continue; the package never quietly chains
phases. See [Phases](docs/workflow/phases.md) for the checkpoint model and
review points in full.

## Command reference

| Command | Use it when | What it writes or checks |
|---|---|---|
| `/start-run` | Starting a new run or resuming after inputs changed. | Input manifest, input evaluation, selected output state, and readiness result. |
| `/extract-requirements` | The selected evidence is ready for analysis. | Knowledge concepts, source coverage, contradictions, assumptions, and traceability links. |
| `/generate-deliverables` | You want all selected documents maintained in the preferred order. | Every selected document with current evidence-backed blocks. |
| `/generate-brd` | You need only the Business Requirements Document. | `outputs/02_deliverables/BRD.md`. |
| `/generate-frd` | You need only functional behavior and data requirements. | `outputs/02_deliverables/FRD.md`. |
| `/generate-urs` | You need a User Requirements Specification. | `outputs/02_deliverables/URS.md`. |
| `/generate-jira-stories` | You need a draft story pack, not publication. | `outputs/02_deliverables/JIRA.md`. |
| `/evaluate-run` | Documents are ready for a quality gate. | Evaluation evidence, quality findings, and remediation items. |
| `/revise-run <feedback>` | A reviewer gave concrete feedback. | Targeted updates; unrelated managed blocks are preserved. |
| `/publish-to-jira` | The Jira pack is approved and the user explicitly wants publication. | External Jira updates plus the run's publication evidence. |
| `/status` | You need a short orientation. | Reads compact current phase/artifact state. |
| `/inspect-run` | You are resuming after interruption or need detail. | Reconstructs detailed state from the filesystem. |

Every command above is also reachable through a matching natural-language
request (for example "write the BRD" instead of `/generate-brd`). See
[Command reference](docs/how-to-run/command-reference.md) for exactly what
each command reads, writes, and considers "done."

## Output selection and document order

`/start-run` asks which deliverables matter for the current run. You may
select one, several, or all four. A selection is not a promise that the
evidence is sufficient; documents visibly retain open items when required
facts are missing.

| Output | Contains | Preferred use |
|---|---|---|
| BRD | Business objective, scope, stakeholders, rules, measures, risks, and open items. | Establish business agreement before solution design. |
| FRD | Functional behavior, data needs, interfaces, validations, and open items. | Explain what the solution must do. |
| URS | User-facing requirements, scenarios, controls, and acceptance-oriented needs. | Validate the solution from the user's perspective. |
| Jira Story Pack | Draft stories with traceability and acceptance criteria. | Prepare a reviewable backlog before publishing. |

The preferred generation order is BRD -> FRD -> URS -> Jira, but the package
does not force an unselected upstream document. It uses the selected template
and available evidence proportionally.

## Where the run state lives

```text
inputs/                         supplied run evidence
context/                        durable guidance and references
outputs/
  00_state/                     private state, knowledge index, hashes, evaluation details
  01_input_evaluation/          user-readable readiness information
  02_deliverables/              BRD.md, FRD.md, URS.md, JIRA.md
  03_evaluation/                evaluation_report.md, quality_scores.json, traceability.yaml
  04_publish_handoff/           jira_issue_mapping.json, jira_publish_summary.md
memory/                         approved durable operational learnings
progress.json                   compact current/next phase projection
```

`outputs/00_state/` is private control state. Do not move, rename,
hand-edit, or delete it to clear a problem. Use `/inspect-run`, `/status`, or
a targeted `/revise-run` instead. The run filesystem, not chat history, is the
source of truth. See [Inputs and outputs](docs/workflow/inputs-and-outputs.md)
for the complete folder-by-folder reference.

## Evidence, knowledge, and revisions

The agent ingests inputs before semantic extraction. It builds a bounded
knowledge layer with stable IDs, source evidence, relationships, hashes, and
impact analysis. Generated document blocks carry managed ownership
(`RA-BLOCK` markers) so a focused revision can change the relevant
requirement without rewriting unrelated reviewed content.

This means the package can surface a contradiction rather than choosing sides
silently. It can carry an assumption as an assumption. It can mark
information as insufficient. Those are useful outputs: a reviewer can resolve
them before Design turns them into a technical decision. See
[Revisions and recovery](docs/workflow/revisions-and-recovery.md) for how
`/revise-run` applies feedback and how to resume safely after an
interruption.

## Configuration

| Concern | File |
|---|---|
| Playground UI + run scaffold contract (input categories, context slots, progress script) | `workspace_layout.yaml` |
| Base session config (hooks, timeouts, allowed commands, deny rules) | `.claude/settings.template.json` -> `.claude/settings.json` |
| Local secrets shape (Jira, GitHub) | `.claude/settings.local.template.json` -> `.claude/settings.local.json` (gitignored) |
| Command routing, template defaults, generation order | `.claude/skills/requirements-agent/workflow_manifest.json` |
| Run-local document templates (override package defaults) | `inputs/templates/` |
| Output selection persistence | `outputs/00_state/state.json`'s `selected_outputs` field |

See [Configuration](docs/reference/configuration.md) for the full detail on
each of these.

## Review and handoff checklist

Before handing a result to Design or publishing stories:

1. Confirm each material requirement still matches the evidence and
   stakeholder intent.
2. Resolve or explicitly accept contradictions, assumptions, and open items.
3. Review scope boundaries, acceptance criteria, data requirements, and
   business rules.
4. Run `/evaluate-run` and address evidence, coverage, consistency, or
   traceability findings.
5. Hand off the reviewed document files, not private state or a copied chat
   transcript.

## Troubleshooting and safe recovery

| Situation | What to do |
|---|---|
| The agent says inputs are insufficient. | Add the missing evidence to the correct input category, then re-run `/start-run` or the recommended phase. |
| A document has an open item. | Resolve it with evidence or leave it visible for a human owner; do not replace it with a guess. |
| A reviewer wants a change. | Use `/revise-run` with specific feedback and inspect the targeted result. |
| The session was interrupted. | Run `/inspect-run`; do not recreate the output folders manually. |
| Jira is unavailable. | Continue locally. Publication is optional and must not block document generation. |
| A template changed during the run. | Review its effect before regeneration; templates shape documents but do not override evidence. |

See [Troubleshooting and FAQ](docs/reference/troubleshooting-faq.md) for an
expanded FAQ covering each of these in more depth.

## Full documentation

### Getting started

- [Overview](docs/getting-started/overview.md) — what the agent owns, where it sits in the lifecycle, and its key concepts (evidence, knowledge layer, RA-BLOCK ownership, traceability).
- [Prerequisites](docs/getting-started/prerequisites.md) — Claude Code and Python setup, dependency install, safe local settings, optional Jira credentials.
- [Quick start](docs/getting-started/quick-start.md) — the fastest concrete path from a clone to a readiness report.

### How to run

- [Running in Claude Code](docs/how-to-run/running-in-claude-code.md) — opening the package root, settings setup, the daily operating loop, resuming.
- [Running in the marketplace / Guided UI](docs/how-to-run/running-in-marketplace.md) — how the hosted UI runs this same package without changing the workflow.
- [Command reference](docs/how-to-run/command-reference.md) — every command's purpose, reads, writes, and definition of done.

### Workflow

- [Phases](docs/workflow/phases.md) — the end-to-end phase-by-phase workflow, checkpoint model, and review points.
- [Inputs and outputs](docs/workflow/inputs-and-outputs.md) — the complete folder-by-folder reference for `inputs/`, `context/`, `outputs/`, `memory/`, and `progress.json`.
- [Revisions and recovery](docs/workflow/revisions-and-recovery.md) — how `/revise-run` and RA-BLOCK ownership work, and how to resume safely.

### Integrations

- [Jira integration](docs/integrations/jira.md) — the optional Jira flow, credential handling, and the publication gate.

### Reference

- [Configuration](docs/reference/configuration.md) — `workspace_layout.yaml`, settings templates, run-local templates, and output selection persistence.
- [Troubleshooting and FAQ](docs/reference/troubleshooting-faq.md) — insufficient inputs, open items, contradictions, interrupted sessions, Jira unavailability, and mid-run template changes.
