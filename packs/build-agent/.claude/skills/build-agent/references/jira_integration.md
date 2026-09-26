# Jira Integration — Build Agent

## Scope

Build uses Jira for three things:

1. **Fetch context at run start** — `/fetch-jira-context` downloads Design-phase deliverables (STTM, Data Model, DQ rules, prior docs) from the Jira Epic's attachments and populates `inputs/`.
2. **Write traceability** — each phase posts one `[BUILD]` comment to the Epic. Per-story summaries are posted only at the end by `/publish-build-summary`.
3. **Move status** — `/fetch-jira-context` transitions stories to *In Progress* with label `phase:build`. `/publish-build-summary` transitions them to *Done*.

Build NEVER:

- Uploads its own generated files to Jira. Outputs stay local.
- Reads from Jira mid-run. The only Jira read is `/fetch-jira-context` at the start.

If `inputs/additional_documents/jira_issue_mapping.json` is absent, every Jira step in every skill silently skips. Build MUST NOT fail because of Jira.

## Discovery (no hardcoded keys, sites, or issue refs anywhere)

Discovery runs once per run, in `/fetch-jira-context`. Subsequent phases read the cached result from `inputs/additional_documents/jira_context.json` — they do not re-discover.

### Procedure

1. **Scan `inputs/**` and `context/**` for Atlassian URLs** matching either of:

   ```
   https://<SITE>.atlassian.net/browse/<KEY>-<N>
   https://<SITE>.atlassian.net/jira/software/projects/<KEY>/...
   ```

   Extract `site` (the `<SITE>` subdomain), `project_key` (the `<KEY>` prefix), and `issue_key` (the `<KEY>-<N>` if the URL targets a specific issue — treat as Epic).
   Walk every supported extension (`.md`, `.txt`, `.docx`, `.pdf`, `.json`, `.yaml`, `.yml`, `.csv`, `.xlsx`) using the input-evaluator's existing readers for binary formats.

2. **Else look for explicit project_key mentions** in JSON/YAML configs or plain text. Regex: `project[\s_-]?key\s*[:=]\s*([A-Z][A-Z0-9_]+)` (case-insensitive).

3. **Else check `.mcp.json`** for any `cloudId` / `defaultProject` hint.

4. **Else ask the user once** for a Jira URL or project key.

If only `project_key` is found, search MCP for the Epic:

```
searchJiraIssuesUsingJql: project = <DISCOVERED_PROJECT_KEY> AND type = Epic ORDER BY created DESC
```

If multiple Epics exist, show keys + summaries and ask which one. If none, ask for the Epic key.

### cloudId

With API-token auth (this package's `.mcp.json` setup), `cloudId` is not implicit. Call `getAccessibleAtlassianResources` once and cache the value. Every Jira MCP call must pass it.

### Cached shape

Write `inputs/additional_documents/jira_context.json`:

```json
{
  "site": "<discovered>",
  "project_key": "<discovered>",
  "epic_key": "<resolved>",
  "cloud_id": "<resolved>",
  "source": "<input file path the URL/key came from>"
}
```

The `source` field is mandatory — it lets the user audit how the agent chose its Jira target.

## JQL for fetching stories under the Epic

Prefer the unified `parent` JQL — works for both team-managed and company-managed projects:

```
project = <DISCOVERED_PROJECT_KEY> AND type = Story AND parent = <DISCOVERED_EPIC_KEY>
```

If a legacy company-managed project returns zero with `parent`, fall back to the deprecated:

```
project = <DISCOVERED_PROJECT_KEY> AND type = Story AND "Epic Link" = <DISCOVERED_EPIC_KEY>
```

If the prior phase used label-grouping instead of Epic membership:

```
project = <DISCOVERED_PROJECT_KEY> AND type = Story AND labels = "phase:design"
```

## Traceability protocol

Every Build phase that runs to completion posts ONE `[BUILD]` comment to the Epic. Stories receive comments only from `/fetch-jira-context` (pickup) and `/publish-build-summary` (final summary).

### How to post (canonical procedure — referenced by every generation skill)

1. Existence gate: if `inputs/additional_documents/jira_issue_mapping.json` does NOT exist, skip everything below.
2. Load `inputs/additional_documents/jira_context.json` for `epic_key` and `cloud_id`.
3. Call `addCommentToJiraIssue` with `cloudId`, `issueIdOrKey = epic_key`, and the body below.
4. If the call fails (MCP unavailable, 401, network error), swallow the exception and continue. Do NOT log a phase failure. Do NOT retry.

### Comment body template

```
[BUILD] <one-line phase summary with metrics>
---
Run: <run_id from runs/run_id_<ID>/session.json>
Phase: <skill name>
```

### Phase comment bodies

Each generation skill points here for the canonical procedure and supplies only this phase-specific one-liner:

| Skill | One-line summary |
|---|---|
| `/start-build-run`     | `Build run started. Scope: <scope_list>. <N> tables in scope. Input evaluation: <one-line verdict>.` |
| `/analyze-inputs`      | `Input analysis complete. Canonical model built. <N> source columns registered. <N> conventions resolved.` |
| `/plan-build`          | `Build plan complete. <N> tables across <W> waves. Dependency graph written.` |
| `/generate-ddl`        | `DDL generation complete. <N> CREATE TABLE statements. Tables: <first 10 then "and <K> more">.` |
| `/generate-dml`        | `DML generation complete. <N> transformation scripts. Lineage corrections applied: <count or "none">.` |
| `/generate-dq`         | `DQ generation complete. <N> check scripts across <M> tables. Framework: <dq_framework>.` |
| `/generate-pipeline`   | `Pipeline generation complete. Platform: <platform>. <W> waves, <T> tasks.` |
| `/generate-tests`      | `Test generation complete. <D> data tests + <P> pipeline tests.` |
| `/evaluate-build`      | `Build evaluation complete. Score: <overall>. <N> remediation items. Quality gate: <verdict>.` |

The story-level comments posted by `/fetch-jira-context` and `/publish-build-summary` are documented in those skills.

## Story-to-table mapping

Build works at the table level; Jira works at the requirement level. The bridge is the STTM: each STTM row carries a requirement ID column, and the agent uses `jira_issue_mapping.json` to resolve requirement IDs back to story keys.

`/fetch-jira-context` builds this mapping at Step 5 and writes it to `inputs/additional_documents/story_table_mapping.json`. Shape:

```json
{
  "<STORY_KEY>": {
    "requirement_ids": ["<REQ_ID>", "<REQ_ID>"],
    "tables": ["<table_name>", "<table_name>"],
    "sttm_rows": "<row_range>"
  }
}
```

Keys, requirement IDs, table names — all runtime-discovered. Nothing hardcoded.

Stories with no STTM row reference get `"tables": []` and a `"notes"` field — they are not silently dropped. `/publish-build-summary` flags them in its final response.

## Attachment script

Download-only for Build. Lives at `.claude/skills/build-agent/scripts/jira_attachments.py` — identical to the Requirements package's copy (do not fork; copy on change).

Usage:

```bash
python .claude/skills/build-agent/scripts/jira_attachments.py \
  --action download \
  --site  <jira_context.site> \
  --issue <jira_context.epic_key> \
  --dest  inputs/_from_jira/
```

Credentials resolve per field by CLI arg > env var > `.jira_config.json` in CWD. See `--help`.

## Authentication

The Atlassian MCP and the attachment script both use API-token (PAT) auth via Basic auth — never OAuth/SSO.

- MCP: `.mcp.json` uses `https://mcp.atlassian.com/v1/mcp` with `Authorization: Basic ${JIRA_BASIC_AUTH}`. `JIRA_BASIC_AUTH` is the base64 of `<email>:<api_token>`. Requires the Atlassian org admin to have enabled API-token auth for MCP at the org level.
- Script: needs any combination of `--email`/`--token` CLI args, `JIRA_EMAIL`/`JIRA_API_TOKEN` env vars, or `.jira_config.json` in CWD.

With API-token MCP auth, `cloudId` MUST be passed explicitly in every Jira call (it's not encoded in the token). Resolve once via `getAccessibleAtlassianResources`, cache, reuse.

## Workflow summary

```
(optional) /fetch-jira-context  → /start-build-run → /analyze-inputs → /plan-build
  → /generate-{ddl,dml,dq,pipeline,tests} → /evaluate-build → (optional) /publish-build-summary
```

The two optional steps require Jira; the middle is platform-internal. If Jira is unavailable at any phase, the run continues; only the traceability comment for that phase is skipped.
