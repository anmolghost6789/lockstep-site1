# DE Discovery overview

DE Discovery is a local-first **Claude Code plugin**, not a run-workspace package. It exists to do the evidence-gathering and readiness work that has to happen before a data-engineering delivery can be planned confidently, and it is invoked inside a Claude Code session as `/de-discovery:discover-project` (see the plugin manifest at [`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json)).

It collects bounded evidence from supplied files, interviews, controlled web research, and a bounded Databricks environment; records source revisions and open questions; applies a configured access boundary; and builds a validated, dynamic Google Open Knowledge Format (OKF) v0.2 knowledge layer that other DE Agents (Requirements, Design, Build) can navigate on their own.

## What it owns

| Owns | Does not own |
|---|---|
| Bounded, evidence-linked discovery of a data-engineering initiative. | A source-system contract, graph database, or pipeline executor. |
| Versioned evidence snapshots with hashing and secret scanning. | A generic web-research bot with unrestricted scope. |
| A dynamic OKF knowledge layer (`knowledge/index.md`, `knowledge/log.md`, and emergent concept files). | A fixed enterprise/domain/project folder taxonomy — concepts and folders emerge from the evidence. |
| Source-system profiles, acquisition contracts, and ingestion specifications when the engagement requires them. | Deployable ingestion pipelines — an ingestion specification is a handoff, not an executed pipeline. |
| Migration assessments and dependency-aware migration units when the engagement is a migration. | An executed migration, cutover, or decommission. |
| A readiness assessment against a requested gate (`discovery-only`, `requirements-ready`, `design-ready`). | A guarantee that no unknowns remain — readiness means sufficient evidence for the next decision. |

## When to use it

Use Discovery before the [Requirements -> Design -> Build -> Deploy -> Test lifecycle](../../../README.md) whenever a data initiative is new, changing, or poorly understood. The package README frames its per-engagement archetypes as: greenfield data products, source onboarding, brownfield change, legacy migration/modernization, platform modernization, data sharing, quality/reliability remediation, governance/compliance, performance/cost optimization, and decommission/archive. See [project archetypes and facets](../../skills/discover-project/references/project-archetypes.md) for the full, reusable classification — a legacy migration that also moves source data normally uses both `migration-modernization` and `source-onboarding` rather than a one-off workflow.

Discovery is not required when the engagement is already fully scoped with agreed evidence; in that case a Requirements run can start directly. It earns its place when you would otherwise start Requirements, Design, or Build on assumptions instead of evidence.

## Key concepts

| Concept | What it means here |
|---|---|
| **Versioned evidence** | Every ingested file is hashed, scanned for common secret patterns, and snapshotted immutably. A changed file creates a new source revision instead of silently overwriting history; every pending revision must be reviewed with a recorded disposition before a run can be marked complete. |
| **OKF knowledge layer** | A dynamic, Markdown-based knowledge bundle under `knowledge/`. Only `knowledge/index.md` (navigation) and `knowledge/log.md` (change log) have fixed paths; every other concept file's path is its own OKF concept ID, and its shape emerges from the evidence and the engagement's archetypes/facets. See [OKF profile](../../skills/discover-project/references/okf-profile.md). |
| **Readiness assessment** | A single concept (`de_agents.role: readiness_assessment`) that scores each required criterion as `supported`, `partial`, `missing`, or `not_applicable`, and rolls up to an overall `supported`, `blocked`, or `conditional` result against the requested readiness target. See [evidence and readiness](../../skills/discover-project/references/evidence-and-readiness.md). |
| **Discovery boundary** | A concept (`de_agents.role: discovery_boundary`) stating included seeds/systems, explicit exclusions, read/profile/mutation permissions, breadth/depth limits, and stop conditions. Discovery widens this boundary only when a named readiness gap requires it. |
| **Context manifest** | The single stable entrypoint (`de_agents.role: context_manifest`) that a downstream DE Agent loads to find the concepts relevant to its own work, without inheriting this conversation. |

## Where to go next

- [Prerequisites](prerequisites.md) — what must be installed and configured before running Discovery.
- [Quick start](quick-start.md) — the fastest concrete path from a clean checkout to a readiness assessment.
- [Command reference](../how-to-run/command-reference.md) — full detail on `/de-discovery:discover-project`.
