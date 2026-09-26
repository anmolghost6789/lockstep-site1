---
name: generate-frd
description: >-
  Generate or incrementally update the selected Functional Requirements
  Document from linked requirements knowledge and the actual dynamic FRD template.
---

# Generate FRD

Follow `requirements-agent/references/document_authoring.md` with
`DELIVERABLE=FRD`. Prepare the generation transaction, delegate one
`deliverable-author`, validate the final `outputs/02_deliverables/FRD.md`, then
commit it serially with `knowledge_layer.py commit-generation`.

Preserve functional behavior, rules, data, interfaces, NFRs, evidence,
assumptions, and explicit gaps. Use EARS when appropriate. Do not reread the raw
corpus or run deep evaluation. Render the generation result using
`requirements-agent/references/phase_completion.md`; then stop.
