---
name: fetch-jira-context
description: >-
  Fetch project context from Jira for the Build agent: discover the Jira connection from inputs, download stories, comments, and attachments (STTM, Data Model, DQ rules, prior deliverables) from the Epic, populate inputs/, derive a story-to-table mapping, and transition stories to "In Progress" with label phase:build. Runs BEFORE /start-build-run. This downloads from and writes to REAL Jira, so use ONLY when the user explicitly asks to fetch, pull, or seed build context from Jira.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Fetch Jira Context

## Purpose

Seed a Build run from Jira instead of from manually-placed input files. After this skill completes, the Build agent's `inputs/` folder looks the same as if a human had dropped in the STTM, data model, DQ workbook, and prior deliverables — plus a structured decision history derived from Jira comments.

## When to run

BEFORE `/start-build-run`. Once per build run. If the project does not use Jira, skip this skill — `/start-build-run` will use whatever is already in `inputs/`.

## Required reads

- `.claude/skills/build-agent/references/jira_integration.md` — Jira link discovery, JQL conventions, comment protocol
- `.mcp.json` — Jira MCP endpoint and auth header
- All files under `inputs/**` and `context/**` (for Jira link discovery)

## Step 1 — Discover Jira connection

Follow the link discovery procedure in `references/jira_integration.md`:

1. Scan `inputs/**` and `context/**` for Atlassian URLs (`https://<site>.atlassian.net/browse/<KEY>-<N>` or `/jira/software/projects/<KEY>/...`). Extract `site`, `project_key`, and `epic_key` (if the URL targets an issue).
2. Else look for `project_key` in JSON/YAML configs or `Jira project: <KEY>` in instruction files.
3. Else check `.mcp.json`.
4. Else ask the user once.

If only a `project_key` is found (no `epic_key`), search for the Epic via MCP:

```
searchJiraIssuesUsingJql: project = {discovered_project_key} AND type = Epic ORDER BY created DESC
```

- If exactly one Epic: use it.
- If multiple Epics: present them to the user with key + summary and ask which to use.
- If none: ask the user for the Epic key.

**Resolve cloudId.** Because this package uses API-token auth on MCP (see `.mcp.json`), cloudId is not implicit. Call `getAccessibleAtlassianResources` once; cache the cloudId.

**Cache the resolved config** in the run's session file (or a local `jira_context.json` if running before `/start-build-run` has created the run dir):

```json
{
  "site": "<discovered>",
  "project_key": "<discovered>",
  "epic_key": "<resolved>",
  "cloud_id": "<resolved>",
  "source": "<the input file the URL/key was found in>"
}
```

Write this to `inputs/additional_documents/jira_context.json` so it survives across phases and so `/start-build-run` can pick it up.

## Step 2 — Fetch stories

Use `searchJiraIssuesUsingJql`. Prefer the unified `parent` JQL:

```
project = {project_key} AND type = Story AND parent = {epic_key}
```

If that returns zero stories on what looks like a legacy company-managed project, fall back to:

```
project = {project_key} AND type = Story AND "Epic Link" = {epic_key}
```

If the prior phase used label-based grouping rather than Epic membership:

```
project = {project_key} AND type = Story AND labels = "phase:design"
```

For each story key returned, call `getJiraIssue` to read:

- Description (requirement text, acceptance criteria, design summary)
- Labels (requirement IDs prefixed `req:`, phase tags `phase:<name>`)
- Comments (the full `[REQ]` / `[DESIGN]` / `[HUMAN]` trail)

Cache the raw responses in `inputs/_from_jira/_raw/stories/<KEY>.json` so re-runs do not re-hit MCP.

## Step 3 — Download attachments from Epic

Use the attachment script:

```bash
python .claude/skills/build-agent/scripts/jira_attachments.py \
  --action download \
  --site <jira_context.site> \
  --issue <jira_context.epic_key> \
  --dest inputs/_from_jira/
```

The script needs `--email` and `--token` from env vars (`JIRA_EMAIL`, `JIRA_API_TOKEN`) or a `.jira_config.json` in CWD. If those are missing, the script exits non-zero — report the missing credentials and stop. Do NOT proceed to Step 4 without the attachments.

## Step 4 — Place files in expected input paths

Classify each downloaded file by name pattern and copy to the Build agent's expected input folder:

| Filename pattern (case-insensitive contains) | Place in |
|---|---|
| `STTM` | `inputs/sttm/` |
| `DATA_MODEL`, `data-model`, `data_model` | `inputs/data_model/` |
| `DQ`, `data_quality`, `data-quality` | `inputs/dq_rules/` |
| `BRD`, `FRD`, `URS`, `UC`, `KPI`, `DR`, `JIRA.md` | `inputs/additional_documents/` |
| `jira_issue_mapping.json` | `inputs/additional_documents/` |
| Anything else | `inputs/additional_documents/` |

After classification:

1. Remove the staging folder `inputs/_from_jira/` (except `_raw/` — keep that for audit).
2. Move `_raw/` to `inputs/additional_documents/_jira_raw/` so it lives alongside the other input docs.

## Step 5 — Build story-to-table mapping

Parse the STTM workbook(s) just placed in `inputs/sttm/`. For each row, read the requirement ID column (typical names: `requirement_id`, `req_id`, `URS_ID`, `FRD_ID` — discover the actual column from the header row).

Build the reverse mapping by joining `jira_issue_mapping.json` (story → requirement_ids) with the STTM (requirement_id → target tables):

```json
{
  "<STORY_KEY>": {
    "requirement_ids": ["<REQ_ID>", "<REQ_ID>"],
    "tables": ["<table_name>", "<table_name>"],
    "sttm_rows": "<row_range>"
  }
}
```

Write to `inputs/additional_documents/story_table_mapping.json`. Validate as JSON (see JSON output discipline in CLAUDE.md). If any story in `jira_issue_mapping.json` has no STTM match, include it with an empty `tables: []` and a `notes: "no STTM rows reference this requirement"` field — do not silently drop it.

## Step 6 — Summarise prior-phase decisions

Walk every story's comments (from the `_raw/stories/<KEY>.json` cached in Step 2). Group by tag prefix:

- `[REQ]` — Requirements-phase decisions and traceability
- `[DESIGN]` — Design-phase decisions and rationale
- `[HUMAN]` — Human corrections, overrides, additions made between phases

Write a structured summary to `inputs/additional_documents/jira_decisions.md`:

```markdown
# Jira Decisions — context for Build

Run seeded from Jira at <UTC timestamp>. Epic: <epic_key>. Stories: <count>.

## Key decisions (Design phase)
- <story_key>: <one-line decision summary> — source: comment <id>
- ...

## Human corrections and overrides
- <story_key>: <what the human changed> — source: comment <id>
- ...

## Unresolved questions
- <story_key>: <question> — source: comment <id>
- ...

## Design assumptions
| Story | Assumption | Confirmed / Rejected | Source |
|---|---|---|---|
| ... | ... | ... | comment <id> |
```

Do NOT paraphrase rejected assumptions as if they were accepted. If a comment says "rejected", show it as rejected. The Build agent uses this file as authoritative context; misclassification here propagates into generated code.

## Step 7 — Transition stories

For each story key in `jira_issue_mapping.json`:

1. **Swap label** via `editJiraIssue`: remove `phase:design`, add `phase:build`. Preserve all other labels (`req:*`, team conventions, issue-type defaults).
2. **Transition status** to "In Progress":
   - Call `getTransitionsForJiraIssue` to discover the available transition IDs for the current status. Do NOT hardcode IDs — workflow IDs vary per project.
   - Call `transitionJiraIssue` with the resolved ID.
   - Standard flow is `In Review → In Progress`. If only an intermediate path is available, perform two hops and re-fetch transitions between them.

3. **Post a `[BUILD]` comment** confirming pickup:

   ```
   [BUILD] Build phase started for this story
   ---
   Run: <run_id placeholder — fill from session.json after /start-build-run, or note as "pending" here>
   Picked up at: <UTC timestamp>
   ```

If transitions or label edits fail for an individual story, log the key in `inputs/additional_documents/jira_decisions.md` under an `## Unable to transition` section and continue. Do not abort the whole skill on one failure.

## Required writes

```text
inputs/sttm/<downloaded STTM files>
inputs/data_model/<downloaded data model files>
inputs/dq_rules/<downloaded DQ files>
inputs/additional_documents/jira_context.json
inputs/additional_documents/jira_issue_mapping.json
inputs/additional_documents/story_table_mapping.json
inputs/additional_documents/jira_decisions.md
inputs/additional_documents/_jira_raw/   (audit trail of raw responses)
inputs/additional_documents/<other downloaded files: BRD, FRD, URS, UC, KPI, DR, JIRA.md>
```

## Final response

Tell the user, concisely:

- Epic key picked up
- Stories fetched (count)
- Attachments downloaded (count) and what was placed where
- Tables mapped (from story_table_mapping.json)
- Whether the JIRA decision summary contains unresolved questions worth reviewing before `/start-build-run`
- Recommend: `/start-build-run`

Do not auto-invoke `/start-build-run`.
