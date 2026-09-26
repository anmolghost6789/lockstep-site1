# Inputs and outputs

## Principle

The package separates active run evidence from durable, reusable context:

- `inputs/` is the active evidence drop-zone for the *current* run.
- `context/` is stable guidance/reference/branding that may apply *across*
  runs.
- `.claude/skills/requirements-agent/assets/` contains agent-owned templates
  and bundled resources — not user evidence.
- `outputs/` is everything the package generates: private state plus every
  reviewable artifact.
- `memory/` is durable operational learning that persists across runs.
- `progress.json` is the run-root compact current/next projection.

These are **default semantic hints, not required filenames.** Content
classification decides a file's role, not its name or extension — you may add
custom subfolders (for example `inputs/jira_guidelines/`,
`context/guidance/compliance/`) and the agent scans them too. Files may be
`.md`, `.docx`, `.pdf`, `.txt`, `.csv`, `.xlsx`, `.json`, or `.yaml`.

## `inputs/`

| Folder | Meaning | Default evidence role |
|---|---|---|
| `inputs/instructions/` | Run-specific instructions and file-usage rules. | Governing run instruction. |
| `inputs/scope_and_requirements/` | Approved or draft scope/requirements material — charters, prior BRDs/FRDs, acceptance criteria. | Primary evidence. |
| `inputs/transcripts/` | Stakeholder conversations, workshops, interviews, discovery calls. | Primary evidence, but may need confirmation. |
| `inputs/data_contracts/` | Schemas, STTMs, data dictionaries, interfaces, mappings. | Primary data evidence. |
| `inputs/templates/` | Approved BRD, FRD, URS, or Jira Markdown templates for this run. | Controls the shape of the selected document — run-local templates are authoritative over package defaults. |
| `inputs/additional_documents/` | Mixed run-specific additional material, legacy packs, partial BRDs, examples. | Supporting unless instructions promote it; without instructions it supports terminology/style/comparison but should not create high-confidence requirements by itself. |
| `inputs/<custom-subfolder>/` | Anything you create under `inputs/`. | Classified from content; treated as `additional_document` if no other role fits. |

### Priority rules

1. Explicit `inputs/instructions/` directions govern how other files should be
   used.
2. Active primary evidence (`scope_and_requirements`, `transcripts`,
   `data_contracts`) drives generated requirements.
3. `inputs/additional_documents/` follows instructions when present; otherwise
   it supports terminology/style/comparison only.
4. `context/guidance/` constrains interpretation and terminology; it does not
   override active input evidence unless it states a compliance/enterprise
   rule.
5. `context/reference/` and `context/branding/` do not create requirements by
   default.

### Required source labeling

Every extracted fact carries a `source_role`: `primary_scope`,
`primary_transcript`, `primary_data_contract`, `run_instruction`,
`additional_document`, `enterprise_guidance`, `domain_guidance`,
`project_guidance`, `branding_context`, `reference_context`, or
`agent_inference`. Anything tagged `agent_inference` must be surfaced as an
assumption unless it is purely structural.

## `context/`

| Folder | Meaning |
|---|---|
| `context/guidance/` | Durable enterprise, domain, and project guidance — e.g. `enterprise.md` (org-wide standards/compliance), `domain.md` (domain concepts, metrics, regulatory context), `project.md` (scope, systems, stakeholders, accepted decisions). Sub-classification is by content scan, not filename. |
| `context/branding/` | Branding and DOCX export preferences — logos, color/style guidance, footer/confidentiality text. Normalized natural-language instructions are persisted to `context/branding/docx_export_preferences.json`. Affects presentation only; must not create requirements unless a user explicitly says a branding file is itself a source requirement. |
| `context/reference/` | Reusable reference material — prior implementations, legacy BRDs, approved examples, industry references. Can influence structure, terminology, and comparison; does not override active inputs by default. |

## `outputs/`

```text
outputs/
  00_state/                     private control state — never hand-edit
    state.json                  machine-owned hashes, status, impact, ownership
    knowledge/
      index.md                  OKF root and progressive-disclosure entry point
      log.md                   human-readable semantic change history
      sources/index.md          descriptive provenance routes
      sources/*.md              generated provenance plus projected coverage
      coverage/index.md         generated coverage navigation
      coverage/*.md             non-captured exceptions by exact input category
      <semantic route>/index.md generated input-shaped navigation
      <semantic route>/*.md     dynamic standalone concepts or cohesive collections
  01_input_evaluation/
    input_evaluation.md         updated in place by /start-run
  02_deliverables/
    BRD.md FRD.md URS.md JIRA.md  selected final deliverables
    .BRD.pending                  exists only while BRD generation is in flight (hidden)
  03_evaluation/
    evaluation_report.md
    quality_scores.json
    traceability.yaml
  04_publish_handoff/
    jira_issue_mapping.json
    jira_publish_summary.md
```

Only these declared paths are ever created. The package never persists source
scans, fragments, evidence catalogs, extraction packets, generation packets,
routes, contracts, chunks, batches, shards, or evaluation packets — there is
no scratch tree and no promotion folder. Each in-flight deliverable uses
exactly one dot-prefixed hidden sibling `.pending` file, which is validated in
place and atomically replaces the final file only after it passes every
check.

**`outputs/00_state/` is private control state.** Do not move, rename,
hand-edit, or delete it to clear a problem — use `/inspect-run`, `/status`, or
a targeted `/revise-run` instead. See
[Revisions and recovery](revisions-and-recovery.md) for why this matters.

## `memory/`

Durable knowledge that persists **across** runs, read once at the start of a
run and written back only at phase boundaries when a durable, reusable
learning is confirmed:

| File | Contents |
|---|---|
| `MEMORY.md` | Reusable facts, project-agnostic conventions, durable learnings. |
| `CONVENTIONS.md` | Writing, naming, formatting, and delivery conventions. |
| `DECISIONS.md` | Decisions that should persist across runs unless superseded. |
| `PATTERN_LIBRARY.md` | High-value reusable section or artifact patterns. |

Promote only information that is reusable, safe, concise, and validated by a
run or user feedback. Never promote raw notes, transcripts, secrets, copied
client content, PII/PHI, one-off assumptions, temporary observations, large
dumps, or unverified guesses.

## `progress.json`

The run-root, UI-facing projection of "what's done, what's current, what's
next." It is derived — never hand-written — from
`outputs/00_state/state.json` and the static workflow manifest by
`seed_progress.py`. See
[Configuration](../reference/configuration.md#progress-and-workflow-manifest)
for the script's exact invocation contract and
[Revisions and recovery](revisions-and-recovery.md) for how it is reconciled
after an interruption.
