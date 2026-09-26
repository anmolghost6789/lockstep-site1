---
name: publish-build-summary
description: >-
  Post a per-story [BUILD] summary comment to each Jira story (tables + DDL/DML/DQ/pipeline/test artifacts generated), add an Epic-level rollup, and transition stories to Done. Runs after /evaluate-build; skipped silently if the run was not seeded from Jira. This posts to and transitions REAL Jira stories, so use ONLY when the user explicitly asks to publish, post, or send the build summary to Jira.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Publish Build Summary

## Purpose

Close the Jira side of a Build run. For each story the agent built code for, write a comment that describes exactly what was produced (table list, file counts, quality verdict), then move the story to Done. Posts a single Epic-level rollup with the totals.

## When to run

AFTER `/evaluate-build`. Once per run. If `inputs/additional_documents/jira_issue_mapping.json` is absent, this skill is a no-op — the run was not seeded from Jira and there is nothing to publish.

## Required reads

- `inputs/additional_documents/jira_issue_mapping.json` — story keys + epic key
- `inputs/additional_documents/jira_context.json` — site, project_key, epic_key, cloud_id
- `inputs/additional_documents/story_table_mapping.json` — story → tables
- `runs/run_id_<ID>/session.json` — scope, run id, summary metrics
- `runs/run_id_<ID>/evaluation/` — score files, quality gate verdict
- `runs/run_id_<ID>/generated/{ddl,dml,dq,pipeline,tests_data,tests_pipeline}/` — file counts (read via Bash `ls` + `wc -l`, not Read tool)
- `.claude/skills/build-agent/references/jira_integration.md`

## Step 0 — Existence check

If `inputs/additional_documents/jira_issue_mapping.json` does not exist, print:

```
No Jira context for this run. /publish-build-summary skipped.
```

and stop. Do not error.

## Step 1 — Load mappings and metrics

Load the JSON inputs above into in-memory dicts. From the run's `generated/` tree, count files per family:

- `ddl_count` = `*.sql` files under `generated/ddl/`
- `dml_count` = `*.sql` files under `generated/dml/`
- `dq_count` = files under `generated/dq/`
- `pipeline_present` = boolean — any files under `generated/pipeline/`
- `tests_data_count` = files under `generated/tests_data/`
- `tests_pipeline_count` = files under `generated/tests_pipeline/`

Read the platform from `session.json.scope_selection.pipeline_platform` (if pipeline was in scope). Read quality verdict from `session.json.evaluation_summary` (gate result + overall score).

## Step 2 — Post per-story summary comment

For each story key in `jira_issue_mapping.json.stories[]`, look up its `tables` from `story_table_mapping.json`. For each story, count which of the run's generated files are for those tables (filename prefix match against the table name list).

Post one comment via `addCommentToJiraIssue`:

```
[BUILD] Build complete for this requirement
---
Tables: <comma-separated table list from story_table_mapping>
DDL: <N> CREATE TABLE statements
DML: <N> transformation scripts
DQ: <N> check scripts
Pipeline: <"included in orchestration YAML" if pipeline_present and this story's tables appear in pipeline files, else "not in pipeline scope">
Tests: <N> data tests, <M> pipeline tests
Quality: <pass/passed_with_actions/failed> (score: <score>)
Run: <run_id>

Note: Build outputs are available in the application, not uploaded to Jira.
```

If a story has `tables: []` (no STTM rows mapped to its requirements), post:

```
[BUILD] No build artifacts generated for this requirement
---
Reason: No STTM rows referenced this requirement's IDs (<list>).
Action: Either the requirement was out of scope for this build, or the STTM is missing a row. Please review.
Run: <run_id>
```

Do NOT transition such stories to Done in Step 3 — leave them at In Progress and surface them in the final response.

## Step 3 — Transition stories to Done

For each story whose comment in Step 2 reported real artifacts (i.e., non-empty `tables`):

1. Call `getTransitionsForJiraIssue` to discover available transition IDs.
2. Call `transitionJiraIssue` with the ID matching "Done".

Standard flow is `In Progress → Done`. Some workflows require `In Progress → In Review → Done`. If only an intermediate hop is available, perform two transitions, re-fetching between them. If neither path is available, log the key under `## Unable to transition` in the publish summary file (Step 5) and continue.

Do NOT transition the Epic.

## Step 4 — Post Epic rollup comment

Post ONE comment to the Epic via `addCommentToJiraIssue`:

```
[BUILD] Build phase complete
---
Total tables: <N>
DDL: <N> files
DML: <N> files
DQ: <N> check scripts
Pipeline: <platform or "not in scope">
Tests: <N> data + <M> pipeline
Quality gate: <pass/passed_with_actions/failed> (overall score: <score>)
Stories completed: <N_done>/<N_total>
Stories needing review: <N_skipped> (empty tables — see comments on those stories)
Run: <run_id>
```

## Step 5 — Write publish summary

Write `runs/run_id_<ID>/handoff/jira_build_summary.md` — a human-readable record of what this skill did:

```markdown
# Jira Build Summary — <run_id>

Epic: <epic_key>
Project: <project_key>
Generated at: <UTC timestamp>

## Stories transitioned to Done
- <story_key>: <table_count> tables, <quality_verdict>
- ...

## Stories left at In Progress
- <story_key>: <reason — empty tables / transition failure / etc.>
- ...

## Unable to transition
- <story_key>: <why — workflow path not available>
- ...

## Epic rollup
<copy of the rollup comment from Step 4>
```

Sync this file via `sync_outputs.py <run_id>` so it appears in `outputs/`.

## Failure mode rule

If MCP is unavailable mid-execution (network error, 401, 5xx), record what was completed so far in `jira_build_summary.md` and tell the user what's left. Do NOT mark the build run as failed — Build artifacts and quality are unaffected by Jira availability.

## Final response

Concise:

- Stories closed: count, with example keys
- Stories needing review: count, with example keys
- Epic rollup posted: yes/no
- Path to `jira_build_summary.md`

Do not recommend a next slash command — this is the last step of the build flow.
