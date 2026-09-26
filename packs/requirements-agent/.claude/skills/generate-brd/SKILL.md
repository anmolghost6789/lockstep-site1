---
name: generate-brd
description: >-
  Generate or incrementally update the selected Business Requirements Document
  from linked requirements knowledge and the actual dynamic BRD template.
---

# Generate BRD

Follow `requirements-agent/references/document_authoring.md` with
`DELIVERABLE=BRD`. Prepare the generation transaction, delegate one
`deliverable-author`, validate the final `outputs/02_deliverables/BRD.md`, then
commit it serially with `knowledge_layer.py commit-generation`.

Preserve business scope, stakeholders, outcomes, use cases, questions, metrics,
business rules, evidence, assumptions, and gaps supported by the linked concept
pages. Do not reread the raw corpus or run deep evaluation. Render the
generation result using `requirements-agent/references/phase_completion.md`;
then stop.
