---
name: generate-jira-stories
description: >-
  Generate or incrementally update the selected Jira Story Pack from linked
  requirements knowledge and the actual dynamic Jira framework/template.
---

# Generate Jira Story Pack

Follow `requirements-agent/references/document_authoring.md` with
`DELIVERABLE=JIRA`. Prepare the generation transaction, delegate one
`deliverable-author`, validate `outputs/02_deliverables/JIRA.md`, then commit it
serially with `knowledge_layer.py commit-generation`.

Derive story IDs, fields, phase labels, hierarchy, and acceptance-criteria shape
from the supplied framework/template. Preserve requirement links and write
complete, independently valuable stories. Do not publish to Jira or run deep
evaluation. Render the generation result using
`requirements-agent/references/phase_completion.md`; then stop.
