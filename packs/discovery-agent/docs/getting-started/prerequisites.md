# Prerequisites

DE Discovery is a Claude Code **plugin** (see [`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json)), not a standalone application. Everything below is what the repository actually documents for enabling and running it — there is no separate marketplace-install flow for this package beyond loading it as a local plugin directory.

## Required

| Requirement | Why |
|---|---|
| A current Claude Code installation and authenticated account. | The plugin runs inside a Claude Code session; there is no other entry point. |
| Python 3.10+ | The deterministic `de_discovery.py` utility and its parser dependencies (DOCX/PDF/XLSX evidence readers) require it. |
| This repository checked out locally. | The plugin loads from its own directory; do not unzip it into a temporary folder that gets cleaned, since it writes state and evidence into its own workspace. |

## Install plugin dependencies

From the `de-discovery` directory:

```powershell
Set-Location .\skill-packages\de-discovery
python -m pip install -r skills\discover-project\scripts\requirements.txt
```

This installs the local parser dependencies the `de_discovery.py` utility needs to hash, scan, and extract text from supplied evidence files (Office, PDF, tabular formats). It does not install credentials, create cloud resources, or start any external service.

## Validate and load the plugin

```powershell
claude plugin validate . --strict
claude --plugin-dir .
```

`claude plugin validate . --strict` checks the plugin manifest and package structure before you load it. `claude --plugin-dir .` starts a Claude Code session with this plugin directory loaded, making the `discovery-agent` agent and the `discover-project` skill (and its `/de-discovery:discover-project` command) available in that session.

## Optional: Databricks access

Live Databricks discovery is optional, not required. If you want it:

- Configure the Databricks AI Dev Kit MCP server, or
- Ensure the Databricks CLI is installed and an authenticated profile is configured.

See [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md) for the provider order (MCP tools, then CLI, then offline) and the default action policy. Without either, Discovery still runs: it ingests local evidence, applies policy, records questions, and validates readiness entirely offline — live system descriptions are then labeled `reported` or `inferred` from supplied artifacts instead of `observed`.

## Project configuration

Before running discovery on a real project, create or review `.de-discovery.yaml` in the project root. At minimum it needs a real `project_id`, a stated `objective`, a `readiness_target`, and one or more `engagement.archetypes`. See [Configuration](../reference/configuration.md) for the full schema and [`discovery.config.example.yaml`](../../skills/discover-project/assets/discovery.config.example.yaml) for a ready-to-copy template.

Do not place client secrets or credentials in this configuration file, in evidence files, or in any research query — see [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md) and [research policy](../../skills/discover-project/references/research-policy.md) for the full guardrails.

## Next step

Continue to [Quick start](quick-start.md).
