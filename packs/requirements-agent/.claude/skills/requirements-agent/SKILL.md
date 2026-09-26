---
name: requirements-agent
description: >-
  Run the evidence-backed requirements workflow for mixed structured or
  unstructured inputs, including input review, linked knowledge extraction,
  dynamic BRD/FRD/URS/Jira generation, revision, evaluation, and Jira publication.
---

# Requirements Agent

Route work through the explicit command skills:

```text
/start-run -> /extract-requirements -> /generate-* or /generate-deliverables
           -> /evaluate-run -> optional /publish-to-jira
```

Do not auto-chain commands or generate unselected outputs.

## Runtime interface

- Read `references/INDEX.md`, then only the references required by the invoked
  command.
- Use `scripts/ingest_inputs.py` for binary ingestion and
  `scripts/knowledge_layer.py` for state, graph, retrieval, and transactions.
- Start knowledge traversal at `outputs/00_state/knowledge/index.md`.
- Resolve public artifact paths and package-default templates from
  `workflow_manifest.json`; never recreate those mappings in prompts.
- At a terminal phase result, render `references/phase_completion.md` from the
  committed result and projected progress instead of forwarding tool chatter.
- Keep model-authored knowledge and deliverables in Markdown. Deterministic
  scripts validate and transact them but do not compile their prose or shape.

## Quality contract

Preserve source meaning, evidence locators, stable IDs, measurable obligations,
contradictions, assumptions, and gaps. Use dynamic templates as authoritative.
Generate from applicable knowledge rather than rereading the corpus. Evaluate
source-to-knowledge fidelity before evaluating knowledge-to-document quality.

## Progressive disclosure

The command skill owns orchestration, the delegated agent owns semantic work,
and the selected reference owns detailed method or schema rules. Do not repeat
the same contract across all three surfaces.
