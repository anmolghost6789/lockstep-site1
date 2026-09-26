# Prerequisites

## Claude Code

You need a current Claude Code installation and an authenticated Claude account. Claude
Code discovers `CLAUDE.md`, `.claude/skills/`, `.claude/agents/`, and `.claude/hooks/` from
the **current project folder**, so you must open `design-skill-package/` itself as the
project root — not `skill-packages/` and not a subfolder such as `.claude/`. Opening the
wrong folder is the most common cause of an "incomplete workflow" symptom (missing slash
commands, missing rules).

Git is required if you will clone or contribute changes to the package.

## Python

Python 3.10+ is required. The package's deterministic scripts depend on:

| Package | Used by | Why |
|---|---|---|
| `openpyxl` (`>=3.1.2,<4.0.0`) | `generate_workbooks.py`, `verify_workbook_headers.py`, `verify_artifact_semantics.py`, `generate_column_mappings.py` | Template-based workbook generation and header verification. |
| `sqlglot` (`>=23.0.0`) | `verify_artifact_semantics.py` | Parses every `dq_rule_expression` as SQL (wrapped as `SELECT 1 FROM t WHERE (...)`) to catch invalid DQ predicates before evaluation. |

Install both from the package root before your first run:

```powershell
python -m pip install -r .claude\skills\design-agent\scripts\requirements.txt
```

`render_design_md.py`, `build_plan.py`, and `seed_progress.py` are stdlib-only and need no
extra dependency.

## Local settings

The package ships one versioned settings template:

```text
.claude/settings.template.json
```

Copy it to the ignored local settings file before your first run:

```powershell
Copy-Item .claude\settings.template.json .claude\settings.json
```

`.claude/settings.template.json` sets runtime env vars (`CLAUDE_STREAM_IDLE_TIMEOUT_MS`,
`BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS`, `MAX_THINKING_TOKENS`,
`CLAUDE_AUTO_COMPACT_THRESHOLD_PERCENT`) and a permission allow-list for the Bash
subcommands the phase skills use (`python3`, `mkdir`, `cp`, `cat`, `ls`, `find`, `wc`,
`head`, `tail`, `grep`, `sort`, `unzip`, `zip`, `mv`, `rm`). It contains no client
credential, so `.claude/settings.json` is safe to create from it directly.

Unlike some sibling packages, this package does not ship a
`.claude/settings.local.template.json`. If your organization later adds an integration
that needs local secrets, keep those values only in an ignored local settings file or
environment variables — never in a committed file, `inputs/`, or a generated deliverable.

The package root also ships `.mcp.json`, declaring `jira` and `github` MCP server
endpoints. No phase skill in this package currently invokes either — design does not
publish to Jira (that is `requirements-skill-package`'s job) or open pull requests (that is
`deploy-skill-package`'s job). Treat these entries as inherited scaffolding rather than an
active integration until a skill in this package actually references them.

## Next

Continue to [Quick start](quick-start.md) to run your first design.
