# Configuration

## `workspace_layout.yaml`

`workspace_layout.yaml` at the package root is the playground UI + run
scaffold contract. It declares:

- **`progress`** — the script (`seed_progress.py`) and file (`progress.json`)
  used for the next-step recommendation, and its reconcile arguments
  (`--recover`). `progress.json` lives at the run root and is the single
  source of truth for done/current/next.
- **`input_change`** — the ingestion script (`ingest_inputs.py`) and state
  script (`knowledge_layer.py`) run after an input upload or deletion. These
  are load-bearing and agent-owned: ingestion updates the current content
  manifest, and the knowledge layer preserves stable source IDs while
  invalidating only the phases whose source or entity hashes actually
  differ.
- **`inputs`** — the declared input categories (`instructions`, `templates`,
  `scope_and_requirements`, `transcripts`, `data_contracts`,
  `additional_documents`) with a label, description, and icon each, used by
  the UI's upload panel.
- **`context_scaffold` / `context`** — the `context/guidance`,
  `context/branding`, `context/reference` folders, with `guidance` further
  split into `enterprise_context`, `domain_context`, and `project_context`
  children by content match.
- **`project_context`** — the same four context slots (enterprise, domain,
  project, branding) plus `reference`, described for project-level reuse
  across runs.

Edit this file (or add folders under `inputs/`/`context/`) only with an
understanding of the UI contract it drives; the comment at its top notes that
the backend must be restarted and the UI hard-refreshed to pick up changes.
Read it before rearranging folders — the packages use their filesystem as the
source of truth, and an input in the wrong category may be invisible to the
phase that needed it.

## `settings.template.json` / `settings.local.template.json`

See [Prerequisites](../getting-started/prerequisites.md) and
[Running in Claude Code](../how-to-run/running-in-claude-code.md) for the copy
steps. In summary:

| File | Committed? | Purpose |
|---|---|---|
| `.claude/settings.template.json` | Yes | Base session config: env timeouts, hook wiring (`SessionStart` -> `load-run-state.sh`, `PostToolUse` on `Write\|Edit` -> `lint-output.py`), the allowed Bash command list, and a `deny` list blocking `.env`/`secrets/**`/`credentials/**`/key files. Copy to `settings.json` (gitignored) before first use. |
| `.claude/settings.local.template.json` | Yes (template only) | Shape for local secrets: `GITHUB_PAT`, `JIRA_PROJECT_KEY`, `JIRA_EMAIL`, `JIRA_API_TOKEN`. Copy to `settings.local.json` (gitignored) and fill in real values only if this run needs Jira publication. |

Never place a live credential in either `.template.json` file — those are
versioned. Keep secrets in `settings.local.json`, environment variables, or
your organization's approved secret mechanism.

## Templates in `inputs/templates/`

Any BRD, FRD, URS, or Jira Markdown template you place under
`inputs/templates/` is **run-local and authoritative** — it overrides the
package's default template for that output for this run only.
`workflow_manifest.json` records each output's package-default path (for
example `.claude/skills/requirements-agent/assets/templates/deliverables/BRD.template.md`)
purely as a fallback; the actual document shape (headings, order, tables,
fields, terminology) always comes from whichever template — run-local or
default — is resolved for that generation. If more than one candidate
template is found for an output, the phase inspects their content and asks
you to disambiguate with `--template <path>` rather than silently picking
one.

Package templates set generation defaults recorded in
`workflow_manifest.json`:

| Output | Default template | Open Items section |
|---|---|---|
| BRD | `BRD.template.md` | 11. Open Items |
| FRD | `FRD.template.md` | 11. Open Items |
| URS | `URS.template.md` | 18. Open Items |
| JIRA | `JIRA_STORY_PACK.template.md` | 8. Open Items |

The preferred generation order across outputs is BRD -> FRD -> URS -> JIRA
(`generationOrder` / `outputOrder`), applied as a soft dependency —
`generationPolicy.mode: soft_dependency_order` — never a hard requirement to
generate an unselected upstream document.

## Output selection persistence

`/start-run` resolves the complete selected-output set (from your input or
from existing state) and commits it with
`knowledge_layer.py commit-start --selected <ID> [--selected <ID> ...]`. The
result is stored as the `selected_outputs` array inside
`outputs/00_state/state.json` — the package's private, machine-owned state
file — and every downstream phase (`/extract-requirements`, every
`/generate-*`, `/evaluate-run`) reads that same field before doing any work,
so an unselected output is never silently generated. `progress.json` and the
`load-run-state.sh` session-start hook both surface the current
`selected_outputs` value for quick orientation, but neither is the source of
truth — `state.json` is.

## Branding / DOCX export configuration

`context/branding/branding_preferences.json` and
`context/branding/docx_export_preferences.json` (the second overrides the
first when both are present) hold normalized branding settings — client/
project name, logo path, colors, font, footer/confidentiality text, and
DOCX-specific fields (`docx.heading_color`, `docx.table_header_color`,
`docx.include_cover_page`, `docx.toc_max_level`, `docx.margins_inches`, and
more). Use
`.claude/skills/requirements-agent/assets/templates/inputs/docx_export_preferences.example.json`
as the shape guide. Markdown remains the source of truth for every
deliverable; DOCX is only ever an on-demand export via `md_to_docx.py` (or the
hosted UI's export action), never something the agent writes as a primary
artifact.
