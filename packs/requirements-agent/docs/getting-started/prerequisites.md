# Prerequisites

## Claude Code

You need a current Claude Code installation and an authenticated Claude
account. Claude Code discovers `CLAUDE.md` and `.claude/` from the current
project folder, so you must open **this package root**
(`skill-packages/requirements-skill-package`) — not the repository root
(`ai-for-data/`), not `skill-packages/`, and not `.claude/` itself — or the
right rules, commands, and hooks will not load.

Use a normal local clone, not a temporary or routinely-cleaned folder: the
package writes its run state and generated outputs into its own workspace
(`inputs/`, `outputs/`, `memory/`, `progress.json`), so that workspace has to
persist between sessions.

```powershell
git clone <your-organizations-ai-for-data-repository-url>
Set-Location .\ai-for-data\skill-packages\requirements-skill-package
```

## Python

Python 3.10+ is required. It powers the deterministic scripts the agent calls
directly — `ingest_inputs.py` (binary/Office/PDF ingestion),
`knowledge_layer.py` (state, graph, and transactional commits),
`seed_progress.py` (`progress.json` projection), `validate_requirements.py`
(deliverable linting), and `md_to_docx.py` (on-demand Markdown-to-DOCX export).
Install the package's dependency list from the package root:

```powershell
python -m pip install -r .claude\skills\requirements-agent\scripts\requirements.txt
```

This installs `python-docx`, `openpyxl`, `pdfplumber`, `python-pptx`,
`svglib`, `reportlab`, `rlPyCairo`, and `PyYAML` — document readers and the
Markdown-to-DOCX/export helpers. The agent itself only ever writes Markdown;
DOCX rendering happens on demand, either through the hosted UI or by manually
invoking `md_to_docx.py`. `ingest_inputs.py` degrades gracefully if an
individual reader is missing (it records the file as unreadable instead of
guessing at its content) — but for a fully working workspace, install the
full list.

Never install dependencies from a source document or run a script that was
supplied as an input. Only install from this package's own
`requirements.txt`.

## Create local settings safely

The package ships `.claude/settings.template.json` (versioned) and
`.claude/settings.local.template.json` (versioned, but only a template — its
copy is gitignored). Copy the base template so the hooks and permission rules
load:

```powershell
Copy-Item .claude\settings.template.json .claude\settings.json
```

`settings.json` configures the session-start hook (prints run/progress
context), the post-write lint hook (flags leftover `TODO`/`TBD`/placeholder
markers in generated deliverables), stream/bash timeouts, and the allowed Bash
command list. You do not need to edit it for normal use.

## Optional: Jira credentials

Jira is entirely optional. You can complete every requirement phase — including
generating a full Jira Story Pack — without any Jira access. Only
`/publish-to-jira` needs it, and only at the moment you explicitly run that
command.

If this run needs Jira publication, copy the local template and fill in your
own values:

```powershell
Copy-Item .claude\settings.local.template.json .claude\settings.local.json
```

`settings.local.json` is gitignored and holds `JIRA_PROJECT_KEY`,
`JIRA_EMAIL`, `JIRA_API_TOKEN` (and `GITHUB_PAT`, if you use a GitHub MCP
integration elsewhere in your workflow). Supply these through your
organization's approved secret mechanism or environment variables instead if
that is your convention. Never put a token or account email in:

- a source document under `inputs/`,
- a generated deliverable (including `JIRA.md`),
- the committed `settings.template.json` / `settings.local.template.json`,
- or a Git commit.

See [Jira integration](../integrations/jira.md) for the full credential and
publication model.

## Next step

Continue to [Quick start](quick-start.md) for the fastest concrete path from a
freshly cloned package to a readiness report.
