# Configuration

Two files configure this plugin: the plugin manifest (fixed, versioned with the package) and the per-project discovery configuration (created per engagement).

## Plugin manifest: `.claude-plugin/plugin.json`

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "de-discovery",
  "displayName": "DE Discovery",
  "version": "0.3.0",
  "description": "Evidence-backed discovery, acquisition and ingestion specifications, migration, and current-practice assessment for data engineering projects, producing a dynamic OKF v0.2 knowledge layer.",
  "author": { "name": "DE Agents" },
  "keywords": ["data-engineering", "discovery", "databricks", "ingestion", "migration", "research", "okf", "knowledge-layer"]
}
```

| Field | Configures |
|---|---|
| `name` | The plugin identifier used in `/de-discovery:discover-project` and `--agent de-discovery:discovery-agent`. |
| `displayName` | The human-readable name shown by marketplace/plugin listings. |
| `version` | The plugin version — also recorded in generated concept frontmatter (`generated.by: de-discovery/<version>`). |
| `description` | The one-line summary of what this plugin produces, shown wherever plugins are listed. |
| `author` | Attribution. |
| `keywords` | Discoverability tags for marketplace search. |

This file is validated by `claude plugin validate . --strict`. Change the `version` field when the plugin's behavior or contract changes materially, since it is stamped into every generated concept.

## Project configuration: `.de-discovery.yaml`

Created per engagement in the target project root (not inside this plugin directory). Copy [`skills/discover-project/assets/discovery.config.example.yaml`](../../skills/discover-project/assets/discovery.config.example.yaml) as a starting point. Every `de_discovery.py` command reads it via `--config` (default `.de-discovery.yaml`, resolved relative to `--project-root`).

```yaml
version: "1"
project_id: replace-me
objective: Replace with the decision or outcome this discovery must enable.
readiness_target: requirements-ready
knowledge_root: knowledge

engagement:
  archetypes:
    - general
  required_facets: []

inputs:
  roots: []
  evidence_mode: snapshot
  max_files: 500
  max_file_bytes: 104857600
  max_extracted_chars: 2000000
  max_tabular_rows: 2000

discovery:
  seeds: []
  include:
    systems: []
    catalogs: []
    schemas: []
    assets: []
  exclude:
    systems: []
    catalogs: []
    schemas: []
    assets: []
  limits:
    max_candidate_assets: 100
    max_deep_profiles: 15
    lineage_depth: 1
    allow_row_sampling: false
  stop_when:
    - requested_readiness_supported
    - material_contradictions_visible
    - remaining_gaps_owned_or_non_blocking

research:
  mode: official-first
  allowed_domains: []
  denied_domains: []
  max_searches_per_run: 20
  max_pages_per_question: 5
  default_stale_after_days: 30
  allow_sensitive_query_terms: false

databricks:
  provider: auto
  profile: DEFAULT
  workspace_hint: null
  agent_resource_prefix: de_discovery_
  policy:
    read: allow
    create_owned: allow
    modify_existing: ask
    manage_permissions: ask
    delete: deny

ownership:
  discovery_owner: null
  boundary_approver: null
```

### Field reference

| Section | Field | Configures |
|---|---|---|
| top-level | `version` | Config schema version. |
| top-level | `project_id` | Real, stable project identifier — replace the placeholder before initializing. |
| top-level | `objective` | The decision or outcome discovery must enable; drives Phase 1 scoping. |
| top-level | `readiness_target` | One of `discovery-only`, `requirements-ready`, `design-ready` — gates what "complete" means. See [evidence and readiness](../../skills/discover-project/references/evidence-and-readiness.md). |
| top-level | `knowledge_root` | The folder the OKF bundle is written under (default `knowledge`). |
| `engagement` | `archetypes` | One or more engagement types (see [project archetypes and facets](../../skills/discover-project/references/project-archetypes.md)); use multiple when the engagement spans types, e.g. `migration-modernization` + `source-onboarding`. |
| `engagement` | `required_facets` | Adds discovery facets for a custom project shape without changing the plugin. |
| `inputs` | `roots` | Optional pre-declared evidence root directories. |
| `inputs` | `evidence_mode` | Evidence handling mode (`snapshot` retains immutable content-addressed copies). |
| `inputs` | `max_files`, `max_file_bytes`, `max_extracted_chars`, `max_tabular_rows` | Bounds on ingestion volume, to keep evidence gathering deliberate rather than exhaustive. |
| `discovery` | `seeds` | Named systems/datasets/schemas that anchor the investigation funnel. |
| `discovery` | `include` / `exclude` | Explicit systems/catalogs/schemas/assets in or out of scope. |
| `discovery` | `limits.max_candidate_assets` | Shortlist cutoff for candidate scoring. |
| `discovery` | `limits.max_deep_profiles` | Cap on assets that get full schema/aggregate/lineage inspection. |
| `discovery` | `limits.lineage_depth` | How many lineage/dependency hops to follow. |
| `discovery` | `limits.allow_row_sampling` | Whether row-level sampling is permitted at all (default: disabled). |
| `discovery` | `stop_when` | Named stop conditions that end the investigation. |
| `research` | `mode` | `off` \| `official-only` \| `official-first` \| `open-with-review` — see [research policy](../../skills/discover-project/references/research-policy.md). |
| `research` | `allowed_domains` / `denied_domains` | Domain allow/deny lists, required for `official-only`. |
| `research` | `max_searches_per_run`, `max_pages_per_question` | Research budget per run/question. |
| `research` | `default_stale_after_days` | Default staleness window for retained web observations. |
| `research` | `allow_sensitive_query_terms` | Whether client-identifying terms may appear in a search query (default: no). |
| `databricks` | `provider` | `auto` resolves AI Dev Kit MCP, then CLI, then offline — see [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md). |
| `databricks` | `profile` | The Databricks CLI profile to use when the CLI is the active provider. |
| `databricks` | `workspace_hint` | Optional workspace identity hint. |
| `databricks` | `agent_resource_prefix` | Prefix required on every agent-created resource (default `de_discovery_`). |
| `databricks` | `policy.read` / `create_owned` / `modify_existing` / `manage_permissions` / `delete` | Default action-class decisions (`allow`, `ask`, or `deny`) enforced by `authorize-action`. |
| `ownership` | `discovery_owner` | The person accountable for this discovery engagement. |
| `ownership` | `boundary_approver` | The person who approves boundary expansion requests. |

Never place a credential, password, API key, or token literal anywhere in this file — reference a Databricks secret or an approved credential mechanism instead. See [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md) for the full guardrail.
