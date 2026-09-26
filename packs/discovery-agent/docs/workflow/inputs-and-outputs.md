# Inputs and outputs

DE Discovery does not use the `inputs/`/`context/`/`outputs/` run-workspace layout that the five delivery packages use — it is a plugin, and it reads and writes the following instead.

## What it consumes

| Input | Consumed via | Notes |
|---|---|---|
| `.de-discovery.yaml` | Read by every command via `--config` (default: project-relative `.de-discovery.yaml`). | Declares project ID, objective, readiness target, engagement archetypes, and every policy boundary. See [Configuration](../reference/configuration.md). |
| A user-provided file or input directory | `ingest --path <path>` | Hashed, scanned for likely secrets, snapshotted immutably, and text-extracted. Repeatable — one call per path. |
| A Databricks result, interview answer, URL, or decision | `register-observation --kind <databricks\|interview\|web\|decision\|other>` plus a redacted content file | Never a raw dump — a concise, redacted observation note with provenance (time, provider/tool, bounded operation, result, coverage limits). |
| Live Databricks metadata (optional) | The configured AI Dev Kit MCP tools, or the Databricks CLI | Metadata-first: Unity Catalog information-schema queries with catalog/schema/name predicates, aggregate profiling within the boundary. Row sampling is disabled by default. See [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md). |
| Controlled web research (optional) | `WebSearch`/`WebFetch`, gated by `research.mode` | Gap-driven only — used to answer a named technical/regulatory/best-practice gap, never as free-form browsing. See [research policy](../../skills/discover-project/references/research-policy.md). |

## What it creates

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

Only `knowledge/index.md` and `knowledge/log.md` have fixed paths. Every other concept file's bundle-relative path (without `.md`) is its own OKF concept ID — folders, concept types, and file names emerge from the evidence and the resolved engagement archetypes/facets. Stable `de_agents.role` values (for example `context_manifest`, `discovery_boundary`, `readiness_assessment`) let downstream packages locate current context, boundary, and readiness material without hardcoding a project-specific tree — see [OKF profile](../../skills/discover-project/references/okf-profile.md).

## Concepts every complete bundle contains

Exactly one non-deprecated concept for each of:

- `context_manifest` — the downstream entrypoint: objective, readiness target, archetypes/facets and coverage, boundary and exclusions, canonical-ID routing for Requirements/Design/Build, source-revision summary, authoritative concepts, unresolved contradictions, readiness result, Databricks resources created, and safe refresh instructions.
- `discovery_boundary` — included seeds/systems, exclusions, read/profile/mutation permissions, breadth/depth limits, stop conditions.
- `readiness_assessment` — per-criterion status (`supported`/`partial`/`missing`/`not_applicable`), supporting evidence, gaps, owner, and blocking flag, rolled up to an overall `supported`/`blocked`/`conditional` result.

## Concepts created only when the engagement requires them

| When | Concepts | Reference |
|---|---|---|
| The resolved facets include `acquisition` | One or more `source_system_profile`, `acquisition_contract`, and `ingestion_spec` concepts. | [Source profiles, acquisition contracts, and ingestion specifications](../../skills/discover-project/references/acquisition-contract.md) |
| The archetypes include `migration-modernization` | One `migration_assessment` and one or more `migration_unit` concepts (plus a proposed `migration_plan` for a `design-ready` target). | [Migration and modernization assessment](../../skills/discover-project/references/migration-assessment.md) |

An `ingestion_spec` only becomes exportable once it reaches `implementation-ready`; `export-ingestion-config` then writes a plain `sources`/`datasets` YAML projection under `.de-discovery/reports/ingestion-configs/`. Candidate specifications are intentionally not exportable — this export is a neutral downstream handoff, not an executed ingestion pipeline and not a grant of access.

## What it does not create

DE Discovery does not create an `inputs/`, `context/`, `outputs/`, or `memory/` tree, a `CLAUDE.md`, or a `workspace_layout.yaml` — those belong to the five run-workspace packages (Requirements, Design, Build, Deploy, Test). It also does not create empty taxonomy folders, duplicate reports, raw inventory dumps, or speculative diagrams; the knowledge bundle stays as small as the engagement's evidence and archetypes require.
