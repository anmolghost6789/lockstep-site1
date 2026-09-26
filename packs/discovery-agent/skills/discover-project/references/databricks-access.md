# Databricks access and autonomy

## Provider order

1. Use already configured Databricks AI Dev Kit MCP tools when available.
2. Otherwise use the Databricks CLI and the configured profile.
3. Otherwise continue with offline artifacts and mark live observations unavailable.

MCP tools perform actions; installed official Databricks skills provide current procedural guidance. Do not copy those skills into this plugin.

Do not connect to source databases with plugin-owned drivers. When live source access is needed, create the approved Databricks access path—such as a connection and foreign catalog, an external location, or Lakeflow Connect—according to source support and the installed Databricks guidance.

Install the current official skills separately when desired:

```text
databricks aitools install --agents claude-code
```

## Metadata-first inspection

- Query Unity Catalog information schema with catalog, schema, or name predicates.
- Inventory only the seed neighborhood.
- Inspect detailed schema and aggregate statistics only for shortlisted assets.
- Treat lineage system tables as evidence with known coverage limits, not a complete graph.
- Record workspace identity, catalog/schema/object, observation time, query or operation summary, and provider.
- Avoid row sampling by default. If permitted, select only necessary non-sensitive columns and the smallest adequate sample.

## Action classes

The config is authoritative:

- **read:** list/get/describe/query metadata and aggregate profile within the boundary;
- **create_owned:** create an agent-owned connection, foreign catalog, external location, Lakeflow Connect resource, or supporting object;
- **modify_existing:** alter existing objects, jobs, pipelines, connections, locations, or settings;
- **manage_permissions:** grants, ownership, credentials, policies, or entitlements;
- **delete:** delete, drop, purge, truncate, or destroy.

Default policy:

| Class | Decision |
|---|---|
| read | allow in boundary |
| create_owned | allow in boundary with `de_discovery_` prefix |
| modify_existing | ask |
| manage_permissions | ask |
| delete | deny |

`authorize-action` must be executed before mutation. Approval in chat does not override a `deny` policy; the project config must be deliberately changed.

## Credentials and connections

- Reference Databricks secrets or an approved credential mechanism. Never place a secret literal in SQL, YAML, Markdown, shell history, or evidence.
- Creating a connection or foreign catalog does not make it automatically relevant; discovery still applies its boundary and shortlist.
- Record the exact agent-created resource and its purpose in local state and the context manifest.
- Discovery does not clean up resources automatically because deletion is denied. Hand the resource list to an authorized operator.

## Capability honesty

Do not assume a specific MCP method exists. Inspect available MCP tools. For CLI use, run `databricks --version` and confirm the profile before queries. If live access is not available, label all system descriptions as reported or inferred from supplied artifacts.
