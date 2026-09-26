# Command reference

## `/de-discovery:discover-project`

The single guided entrypoint this plugin exposes. It is defined by [`skills/discover-project/SKILL.md`](../../skills/discover-project/SKILL.md) and run by the [`discovery-agent`](../../agents/discovery-agent.md).

**Description (from the skill manifest):** discover and assess any bounded data-engineering initiative — greenfield data products, source onboarding/ingestion, brownfield changes, legacy migration and modernization, platform change, data sharing, quality or governance remediation, optimization, and decommissioning. Use it when a DE Agent needs trustworthy semantic, acquisition, migration, operational, and current-practice context from project evidence, controlled internet research, and a bounded Databricks environment before Requirements, Design, Build, Test, or Deploy work.

You can also start the dedicated agent directly instead of the skill's slash form:

```powershell
claude --plugin-dir . --agent de-discovery:discovery-agent
```

### When to use it

- A data initiative is new, changing, or not well understood, and the next stage (Requirements, Design, or Build) would otherwise start on assumptions.
- You need a machine-readable, evidence-linked knowledge bundle another DE Agent can navigate without inheriting this chat.
- You need a source-system profile, acquisition contract, or ingestion specification before Design/Build can work with a source.
- You need a migration assessment and dependency-aware migration units before planning a legacy migration.
- You are resuming a prior discovery run after evidence changed — the skill resumes safely from local state (`.de-discovery/state.yaml`) rather than starting over.

### What it produces

Per the [discovery-agent](../../agents/discovery-agent.md) definition, the product is "not a prose report: it is a validated, source-linked OKF v0.2 knowledge bundle that another DE Agent can navigate without inheriting this conversation." Concretely:

- an initialized or updated `.de-discovery/` state and evidence store (hashed, scanned, snapshotted source revisions);
- a dynamic `knowledge/` OKF bundle: the fixed `index.md` and `log.md`, plus emergent concept files including exactly one `context_manifest`, one `discovery_boundary`, and one `readiness_assessment`;
- when the resolved facets include `acquisition`: one or more `source_system_profile`, `acquisition_contract`, and `ingestion_spec` concepts;
- when the archetypes include `migration-modernization`: one `migration_assessment` and one or more `migration_unit` concepts (plus a proposed `migration_plan` for a `design-ready` target);
- a closing summary of the knowledge entrypoint path, readiness target and result, concepts changed, unresolved blockers, Databricks resources created, research mode and material web evidence, and the validation result.

It never auto-chains into Requirements, Design, or another package — the run ends with a recommendation, and the next phase runs only when you send a fresh message or command. See [Workflow phases](../workflow/phases.md) for the full seven-phase method.

## Underlying deterministic utility: `de_discovery.py`

The skill drives a deterministic Python utility so that state, hashing, evidence, and validation are not left to model judgment:

```powershell
python skills\discover-project\scripts\de_discovery.py --help
```

| Command | Required flags | Use it for |
|---|---|---|
| `doctor` | — | Confirm local parser dependencies and inspect available Databricks/web capabilities and the active configuration. |
| `init` | — (accepts `--project-id`, `--objective`, `--readiness-target`, `--knowledge-root`) | Create state, evidence folders, and knowledge navigation for a new project. |
| `ingest` | `--path` (repeatable) | Hash, scan, snapshot, and extract text from a supplied file or directory. |
| `register-observation` | `--kind`, `--title`, `--source-uri`, `--content-file` (`--publisher`/`--applicability` required for `--kind web`) | Add a redacted Databricks, interview, web, decision, or other observation with provenance. |
| `status` | — | Show resumable state, changed sources, pending revisions, and open questions. |
| `authorize-action` | `--action`, `--resource-name` (optional `--system`, `--catalog`, `--schema`) | Check a requested Databricks action against boundary and policy before attempting it. |
| `record-resource` | `--type`, `--name`, `--purpose` (optional `--uri`) | Record an agent-created Databricks resource. |
| `review-source` | `--revision-id`, `--disposition` (`applied`\|`reviewed-no-change`\|`out-of-scope`), `--reason` (optional `--concept`, repeatable) | Resolve a pending source revision after impact review. |
| `record-question` | `--id`, `--question` (optional `--owner`, `--blocking`/`--no-blocking`) | Track a blocking or non-blocking question. |
| `resolve-question` | `--id`, `--resolution` | Resolve a persisted question. |
| `rebuild-index` | — | Regenerate OKF knowledge navigation from current concepts. |
| `validate` | optional `--profile` | Validate the OKF bundle, and with `--profile`, the DE Agents downstream-readiness rules. |
| `set-phase` | `--phase` (`intake`\|`clarify`\|`plan`\|`discover`\|`synthesize`\|`validate`\|`complete`\|`blocked`), optional `--last-step` | Update the resumable discovery phase. |
| `score-candidates` | `--input` | Validate and rank a YAML/JSON candidate-asset file using the scoring rubric. |
| `export-ingestion-config` | `--canonical-id` (optional `--output`) | Export one `implementation-ready` OKF ingestion spec as plain `sources`/`datasets` YAML under `.de-discovery/reports/ingestion-configs/`. |

Every subcommand accepts `--project-root` (defaults to the current directory) and `--config` (defaults to `.de-discovery.yaml`, project-relative).

See [Configuration](../reference/configuration.md) for the `.de-discovery.yaml` schema these commands read, and [Inputs and outputs](../workflow/inputs-and-outputs.md) for exactly what each command reads and writes on disk.
