# Jira publication

Use this reference only after the user invokes `/publish-to-jira`. Generation
never writes to Jira.

## Preconditions

- JIRA is selected and `outputs/02_deliverables/JIRA.md` is complete.
- Required project/site configuration is supplied by the user, linked evidence,
  or the configured Jira integration.
- Story IDs, hierarchy, required fields, acceptance criteria, dependencies, and
  blocking open items have been validated.
- The user confirms the exact create/update plan immediately before the first
  external write.

Never cache credentials, site identifiers, or project configuration in an
undeclared state file. Never infer keys, issue types, field IDs, or workflow
values from package examples.

## Publish behavior

Use the configured Jira tools available to the parent runtime. Resolve the site
and project once, preview create/update counts, then upsert in dependency order.
Use stable story IDs and the prior issue mapping for idempotency. Preserve the
hierarchy and fields defined by the selected Jira template or supplied framework.

Include canonical knowledge/source traceability in issue descriptions without
exposing private runtime state. Upload attachments only when explicitly requested
and supported by the configured Jira tool; otherwise report them as unsupported
without attempting an alternate credential or REST path.

## Durable result

Write exactly:

```text
outputs/04_publish_handoff/
  jira_issue_mapping.json
  jira_publish_summary.md
```

The mapping is valid JSON with a top-level `issues` list. Each row records the
stable story ID, resulting Jira key and URL, action (`created`, `updated`,
`skipped`, or `failed`), and error when applicable. The summary states the
confirmed target, counts, partial failures, attachment results, and remediation.

Do not hide partial failure. A retry reuses successful mappings and acts only on
unresolved rows.
