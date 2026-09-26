---
name: publish-to-jira
description: >-
  Publish or update an approved Jira Story Pack through the configured Jira
  integration after explicit confirmation, then record the durable mapping and summary.
---

# Publish approved Jira stories

This is the only Jira-mutating phase. Read
`references/jira_publication.md`, the final Jira pack, current evaluation when
present, and an existing issue mapping when updating an earlier publication.

Validate selection, story structure, traceability, unresolved blockers, and
required Jira configuration. Resolve site and project through the configured
Jira integration or explicit user input. Never invent or cache configuration in
private state.

Immediately before the first write, ask for explicit confirmation showing the
site, project, create/update counts, and attachment plan. After confirmation,
upsert issues in dependency order using stable story IDs and the prior mapping.

Write `outputs/04_publish_handoff/jira_issue_mapping.json` and
`jira_publish_summary.md`, then run:

```bash
python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . commit-publication
python .claude/skills/requirements-agent/scripts/seed_progress.py --from-state --completed publish
```

Never hide partial failure. Render the publication result using
`requirements-agent/references/phase_completion.md`; then stop.
