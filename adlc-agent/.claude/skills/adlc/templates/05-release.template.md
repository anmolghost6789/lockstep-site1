# Governed Production Release: {{release_id}}

## Release Summary

| Field | Value |
|---|---|
| Release ID | REL-{{NNN}} |
| Intent ID | {{intent_id}} |
| Scorecard sha256 (approved at G4) | {{sha256}} |
| Risk level | {{low / medium / high / critical}} |
| Required approvers | release_manager{{, security_officer}}{{, waiver_approver}} |

## Versions

| Component | Version (pinned) |
|---|---|
| Application commit | {{sha}} |
| Container image | {{registry/image@sha256:...}} |
| Models | {{model ids per agent}} |
| Prompts and agent configs | {{path@version}} |
| Eval dataset | {{version}} |

## Deployment Plan

{{Environments, CI/CD workflow, feature flag, rollout stages (start at the configured %), promotion criteria as numbers.}}

## Rollback Plan

{{Automatic rollback triggers as numbers, manual steps, owner, and link to the staging rehearsal evidence.}}

## Runbook

{{Alerts, dashboards, on-call rota, known failure modes and responses, and how to disable each agent or write tool.}}

## Risk Assessment

{{Blast radius, data classification touched, write tools enabled, residual risks and why the chosen risk level applies.}}

## Readiness Checklist

Written by `release-auditor`.

| Check | Result | Evidence |
|---|---|---|
| All versions pinned | {{pass/fail}} | {{link}} |
| SBOM produced | {{pass/fail}} | adlc/.state/evidence/sbom_present.json |
| Rollback rehearsed | {{pass/fail}} | {{link}} |
| Secrets referenced from vault only | {{pass/fail}} | {{link}} |
| Access and least privilege reviewed | {{pass/fail}} | {{link}} |
| Monitoring and alerts live in staging | {{pass/fail}} | {{link}} |
