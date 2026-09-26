# Jira integration

Jira is entirely optional. You can complete every requirement phase —
including generating a complete, reviewable Jira Story Pack — without any
Jira access at all.

## Two separate things: generating vs. publishing

| Command | Touches Jira? |
|---|---|
| `/generate-jira-stories` (or `/generate-deliverables` with JIRA selected) | Never. Produces `outputs/02_deliverables/JIRA.md` — a local Markdown draft only. |
| `/publish-to-jira` | Yes — the **only** command in the package that writes anything outside the run workspace. |

Generating a story pack never sends data externally. Only the explicit
`/publish-to-jira` command reaches out to Jira, and only after you confirm the
exact plan immediately before the first write.

## Credential handling

If a run needs publication, create the gitignored local settings file from
the versioned template:

```powershell
Copy-Item .claude\settings.local.template.json .claude\settings.local.json
```

and fill in:

- `JIRA_PROJECT_KEY`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`

or supply the same values through your organization's approved environment
variables instead. `settings.local.json` is gitignored; `settings.json` and
`settings.local.template.json` are committed and must never contain a live
credential.

Never place a project key, account email, or API token in:

- a file under `inputs/` (a source document),
- a generated deliverable — including `JIRA.md` itself,
- this documentation or any other committed file,
- a Git commit of any kind.

The package's own `.claude/settings.template.json` explicitly denies reading
`.env`, `secrets/**`, `credentials/**`, and key/certificate files, and the
agent never invents or caches Jira configuration (site, project, field IDs,
issue types) in private state — it resolves them through the configured Jira
integration or explicit user input at publish time only.

## What `/publish-to-jira` validates before writing

- JIRA is selected and `outputs/02_deliverables/JIRA.md` is complete.
- Required project/site configuration is supplied by you, linked evidence, or
  the configured Jira integration.
- Story IDs, hierarchy, required fields, acceptance criteria, dependencies,
  and blocking open items have all been validated.

## The confirmation gate

Immediately before the first external write, the agent shows the exact site,
project, and create/update counts and the attachment plan, and asks for your
explicit confirmation. Only after you confirm does it upsert issues, in
dependency order, using stable story IDs and any prior issue mapping for
idempotency.

## Durable publication record

```text
outputs/04_publish_handoff/
  jira_issue_mapping.json   valid JSON, top-level "issues" list
  jira_publish_summary.md   confirmed target, counts, partial failures, remediation
```

Each row in `jira_issue_mapping.json` records the stable story ID, resulting
Jira key and URL, and an action of `created`, `updated`, `skipped`, or
`failed` (with error detail when applicable). Partial failure is always
reported — never hidden — and a retry reuses the successful mappings from a
prior attempt and acts only on the unresolved rows.

## If Jira is unavailable

Continue locally. Publication is optional and must never block document
generation, evaluation, or revision — those phases have no dependency on Jira
being reachable or configured at all.
