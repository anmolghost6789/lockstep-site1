---
name: generate-urs
description: >-
  Generate or incrementally update the selected User Requirements Specification
  from linked requirements knowledge and the actual dynamic URS template.
---

# Generate URS

Follow `requirements-agent/references/document_authoring.md` with
`DELIVERABLE=URS`. Prepare the generation transaction, delegate one
`deliverable-author`, validate the final `outputs/02_deliverables/URS.md`, then
commit it serially with `knowledge_layer.py commit-generation`.

Preserve user needs, personas, outcomes, constraints, criticality, verification
intent, evidence, assumptions, and gaps. Do not impose a static specification
shape, reread the raw corpus, or run deep evaluation. Render the generation
result using `requirements-agent/references/phase_completion.md`; then stop.
