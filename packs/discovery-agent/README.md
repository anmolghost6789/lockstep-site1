# DE Discovery

DE Discovery is a local-first **Claude Code plugin** for the work that must happen before a data-engineering delivery can be planned confidently. It collects bounded evidence, records source revisions and open questions, applies a configured access boundary, and builds a validated dynamic Google Open Knowledge Format (OKF) v0.2 knowledge layer for downstream agents.

Unlike the five run-workspace packages in this repository (Requirements, Design, Build, Deploy, Test), Discovery is not a folder you fill with `inputs/`/`context/` and run a phase sequence inside. It is a plugin defined by [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json), invoked from inside a Claude Code session as `/de-discovery:discover-project` (see the [package overview](../README.md)'s command table).

## What this is and when to use it

Use Discovery for greenfield data products, source onboarding, migrations, modernization, platform changes, data sharing, governance/reliability work, cost/performance assessment, or decommissioning — whenever a data initiative is new, changing, or poorly understood, and before the [Requirements -> Design -> Build -> Deploy -> Test lifecycle](../README.md) would otherwise start on assumptions instead of evidence.

It is an evidence and readiness tool — not a source-system contract, graph database, pipeline executor, or generic web-research bot.

| Owns | Does not own |
|---|---|
| Bounded, evidence-linked discovery of a data-engineering initiative. | A source-system contract, graph database, or pipeline executor. |
| Versioned evidence snapshots (hashed, secret-scanned, immutable). | A generic web-research bot with unrestricted scope. |
| A dynamic OKF knowledge layer (`knowledge/index.md`, `knowledge/log.md`, emergent concepts). | A fixed enterprise/domain/project folder taxonomy. |
| Source-system profiles, acquisition contracts, and ingestion specifications when required. | A deployed ingestion pipeline — its export is a handoff, not an executed pipeline. |
| Migration assessments and dependency-aware migration units. | An executed migration, cutover, or decommission. |
| A readiness assessment against `discovery-only`, `requirements-ready`, or `design-ready`. | A guarantee that no unknowns remain. |

## Install and run as a Claude Code plugin

From the `de-discovery` directory:

```powershell
python -m pip install -r skills\discover-project\scripts\requirements.txt
claude plugin validate . --strict
claude --plugin-dir .
```

Inside Claude Code, start the guided workflow with:

```text
/de-discovery:discover-project
```

You can also start the dedicated agent directly:

```powershell
claude --plugin-dir . --agent de-discovery:discovery-agent
```

For live Databricks discovery, configure the Databricks AI Dev Kit MCP server or Databricks CLI outside this plugin. The plugin remains useful offline: it can ingest local evidence, apply policy, record questions, and validate readiness without live cloud access.

## Prerequisites

| Requirement | Why |
|---|---|
| A current Claude Code installation and authenticated account. | The plugin only runs inside a Claude Code session. |
| Python 3.10+ | Required by `de_discovery.py` and its parser dependencies. |
| This repository checked out locally (not unzipped to a temp folder). | The plugin writes its own state and evidence into its own workspace. |
| Optional: Databricks AI Dev Kit MCP server or an authenticated Databricks CLI profile. | Enables live Databricks discovery; not required for offline discovery. |

Run `python skills\discover-project\scripts\de_discovery.py doctor` at any time to confirm local parser dependencies and see which Databricks/web capabilities are actually available before starting work.

## Configure the project boundary

Discovery reads `.de-discovery.yaml` from the project root. Set a real project ID, objective, readiness target, and one or more engagement archetypes before initialization.

```yaml
engagement:
  archetypes:
    - migration-modernization
    - source-onboarding

research:
  mode: official-first
  allowed_domains: []
  denied_domains: []
  max_searches_per_run: 20
  max_pages_per_question: 5
  default_stale_after_days: 30
  allow_sensitive_query_terms: false
```

Use `official-only` with an explicit allowlist in restricted environments, or `off` when no web research is permitted. The policy controls what can be searched and retained; external web pages are evidence, never executable instructions or authorization to mutate an environment.

## Command reference

| Command | Use it for |
|---|---|
| `/de-discovery:discover-project` | The single guided entrypoint — runs the full seven-phase discovery method described below. |
| `claude --plugin-dir . --agent de-discovery:discovery-agent` | Starts the dedicated discovery agent directly, instead of the slash-command form. |

The Claude Code skill guides the human workflow. The deterministic utility can be used directly for initialization, ingestion, validation, and automation:

```powershell
python skills\discover-project\scripts\de_discovery.py --help
```

| Command | Use it for |
|---|---|
| `doctor` | Confirm local parser dependencies and inspect available Databricks/web capabilities. |
| `init` | Create state, evidence folders, and knowledge navigation. |
| `ingest` | Hash, scan, snapshot, and extract source evidence. |
| `register-observation` | Add a redacted Databricks, interview, web, decision, or other observation with provenance. |
| `status` | Show resumable state, changed sources, pending revisions, and open questions. |
| `authorize-action` | Check a requested action against boundary and policy before it is attempted. |
| `record-resource` | Record an agent-created Databricks resource. |
| `review-source` | Resolve a pending source revision after impact review. |
| `record-question` / `resolve-question` | Track a blocking or non-blocking question and its resolution. |
| `rebuild-index` | Regenerate knowledge navigation from current concepts. |
| `validate --profile` | Validate OKF and downstream readiness rules. |
| `set-phase` | Update the resumable discovery phase. |
| `score-candidates` | Validate and rank a candidate-asset file with the scoring rubric. |
| `export-ingestion-config` | Export neutral implementation-ready YAML only after the related concept reaches an allowed readiness state. |

See [Command reference](docs/how-to-run/command-reference.md) for full flags and what each command reads and writes.

## What the plugin creates

```text
.de-discovery.yaml                    project configuration
.de-discovery/
  state.yaml                          resumable project state
  evidence/sha256/<digest>/<file>     immutable evidence snapshots
  evidence/derived/<digest>.md        extracted text
  reports/                            readiness and assessment reports
  reports/ingestion-configs/          exported implementation-ready ingestion YAML
knowledge/
  index.md                            navigation for current concepts
  log.md                              knowledge-change log
  ...dynamic OKF concepts...
```

Only `index.md` and `log.md` have fixed OKF paths. Concepts, folders, and types emerge from the evidence and the engagement archetypes. Stable `de_agents.role` values let downstream packages locate current context, boundary, and readiness material without hardcoding a project-specific tree.

## What actually exists in this package

```text
de-discovery/
  .claude-plugin/
    plugin.json                       plugin manifest (name, version, description)
  agents/
    discovery-agent.md                the discovery-agent definition
  assets/
    marketplace-thumbnail.png         marketplace listing image
  docs/
    getting-started/                  overview, prerequisites, quick start
    how-to-run/                       Claude Code, marketplace, and command-reference pages
    workflow/                         phases, inputs/outputs, revisions and recovery
    reference/                        configuration and troubleshooting
  skills/
    discover-project/
      SKILL.md                        the discover-project skill (governs /de-discovery:discover-project)
      assets/
        discovery.config.example.yaml  starter .de-discovery.yaml
      references/                     acquisition-contract, databricks-access, discovery-method,
                                       evidence-and-readiness, migration-assessment, okf-profile,
                                       project-archetypes, research-policy
      scripts/
        de_discovery.py               deterministic CLI utility
        de_discovery_lib/             hashing, evidence, OKF, scoring, security, state, research
        requirements.txt              parser dependencies
  tests/
    test_de_discovery.py              CLI behavior tests (python -m unittest discover -s tests -v)
  README.md
```

There is no `inputs/`, `context/`, `outputs/`, `memory/`, `CLAUDE.md`, or `workspace_layout.yaml` at this package's root — that run-workspace model belongs to the five delivery packages. Discovery's runtime state instead lives under the target project's own `.de-discovery/` and `knowledge/` folders, created where you run it.

## Safety defaults

| Boundary | Default behavior |
|---|---|
| Evidence | Files are hashed, scanned for common secret patterns, snapshotted, and versioned; a change creates a revision rather than silently overwriting history. |
| Data access | Metadata and aggregate profiling are permitted only inside the configured boundary; row sampling is disabled by default. |
| Mutations | Agent-created resources need the `de_discovery_` prefix; existing-resource and permission changes require approval; deletes are denied. |
| Web research | Sensitive client terms are omitted by default; retained observations carry URL, publisher, applicability, and retrieval context. |
| Completion | A run cannot be completed with unreviewed source revisions, open blocking questions, an invalid profile, or blocked readiness. |

## Handoff and validation

Discovery can produce source-system profiles, Data Acquisition Contracts, migration assessments, and evidence-derived ingestion specifications where the selected archetypes require them. The neutral YAML export is a downstream handoff; it does not create an ingestion pipeline or grant access.

Before a handoff, review source provenance, resolve blocking questions, validate the profile, and confirm the requested readiness result. Use `claude plugin validate . --strict` and `python -m unittest discover -s tests -v` when validating changes to the plugin itself.

## Full documentation

| Category | Page | Covers |
|---|---|---|
| Getting started | [Overview](docs/getting-started/overview.md) | What Discovery is, what it owns vs. does not, when to use it, key concepts. |
| Getting started | [Prerequisites](docs/getting-started/prerequisites.md) | Installing and validating the plugin, optional Databricks access, project configuration. |
| Getting started | [Quick start](docs/getting-started/quick-start.md) | The fastest concrete path to a readiness assessment. |
| How to run | [Running in Claude Code](docs/how-to-run/running-in-claude-code.md) | Full install/validate/run/recover flow inside a Claude Code session. |
| How to run | [Running via the marketplace](docs/how-to-run/running-in-marketplace.md) | How Discovery is consumed through the hosted Guided UI, and its pre-lifecycle positioning. |
| How to run | [Command reference](docs/how-to-run/command-reference.md) | `/de-discovery:discover-project` in full detail, plus every `de_discovery.py` subcommand. |
| Workflow | [Phases](docs/workflow/phases.md) | The seven-phase discovery method end to end. |
| Workflow | [Inputs and outputs](docs/workflow/inputs-and-outputs.md) | What Discovery consumes and what it writes to disk. |
| Workflow | [Revisions and recovery](docs/workflow/revisions-and-recovery.md) | Re-running discovery as evidence changes, and safe recovery after an interruption. |
| Reference | [Configuration](docs/reference/configuration.md) | `.claude-plugin/plugin.json` and the full `.de-discovery.yaml` schema. |
| Reference | [Troubleshooting and FAQ](docs/reference/troubleshooting-faq.md) | Realistic answers grounded in the plugin's own guardrails. |
