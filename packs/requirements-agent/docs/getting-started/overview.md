# Overview

Requirements Agent is the evidence-to-requirements stage of the data-engineering
delivery lifecycle. It reads the business evidence you supply, preserves what
that evidence actually says, records gaps and contradictions instead of
guessing past them, and produces only the requirement documents you selected:
a Business Requirements Document (BRD), a Functional Requirements Document
(FRD), a User Requirements Specification (URS), and/or a Jira Story Pack.

It is deliberately not a generic document writer. Every run keeps an evidence
snapshot, a linked knowledge layer, traceability from requirement back to
source, deterministic state, the generated documents, and evaluation results —
everything a reviewer needs to check or resume the work without replaying the
conversation.

## What this package owns

| Use it for | Do not use it for |
|---|---|
| Turning workshops, transcripts, briefs, policies, source descriptions, and existing documents into requirements. | Designing a target data model, producing DDL/DML, deploying a pipeline, or executing data tests. |
| Maintaining traceability from a requirement back to its source evidence. | Filling a gap with an invented rule merely to make a document look complete. |
| Creating review-ready documents and draft Jira stories. | Publishing to Jira without an explicit user decision. |

## Where it sits in the lifecycle

The five delivery skill packages in this repository follow one lifecycle:

```text
Requirements -> Design -> Build -> Deploy -> Test
```

Requirements Agent is the entry stage. Its typical handoff is
**Requirements -> Design**: Design consumes reviewed business scope, functional
behavior, data requirements, business rules, and open items from this
package's output — it does not need, and should not need, an unreviewed chat
summary. A separate `de-discovery` package can run *before* Requirements Agent
when a data initiative is new, changing, or poorly understood and needs
evidence and readiness assessment first. An `orchestrator-skill-package`
coordinates all five delivery stages end to end in the hosted Guided UI;
Requirements Agent itself only performs the requirements stage and does not
call the other packages.

## Key concepts

### Evidence

Evidence is the material you place under `inputs/` (and durable guidance under
`context/`). The agent classifies it by content, not filename, and tags every
extracted fact with a `source_role` (for example `primary_scope`,
`primary_transcript`, `enterprise_guidance`, `agent_inference`). Evidence
drives every generated statement; the package never fabricates a business
decision to make a document look complete. See
[Inputs and outputs](../workflow/inputs-and-outputs.md) for the full folder
model.

### The knowledge layer

Between "read the evidence" and "write a document" sits a linked Markdown
knowledge layer under `outputs/00_state/knowledge/`. `/extract-requirements`
builds it: stable-ID concepts, typed relationships, evidence links, source
coverage, contradictions, and assumptions. Every later `/generate-*` command
reads from this layer instead of re-reading the raw corpus, and `/evaluate-run`
checks both source-to-knowledge fidelity and knowledge-to-document quality
against it. This bounded, incremental layer is what lets the package update
only what actually changed instead of regenerating everything on every run.

### RA-BLOCK managed ownership

Every generated document section is wrapped in an ownership marker:

```markdown
<!-- RA-BLOCK START id="semantic-name" entities="FR-001,BR-002" -->
...dynamic template-shaped content...
<!-- RA-BLOCK END id="semantic-name" -->
```

This marker records which knowledge entities back that block. `/revise-run`
uses it to patch only the blocks a piece of feedback actually affects, leaving
unrelated reviewed content — including your own manual edits outside a block —
untouched. See
[Revisions and recovery](../workflow/revisions-and-recovery.md) for the full
model.

### Traceability

Traceability is the linked chain across three durable layers:

```text
source page -> topic entity (knowledge layer) -> RA-BLOCK in a final deliverable
```

`/evaluate-run` independently verifies this chain — it reads every source
before trusting the knowledge graph, then reads the graph before trusting the
document — and writes the result to
`outputs/03_evaluation/traceability.yaml`. A reviewer can always walk a
requirement in a BRD/FRD/URS/Jira story back to the exact evidence that
justified it.

## What "done" looks like

There is no single finish line. Each command is a checkpoint: it writes state,
reports what it completed or could not complete, recommends the next command,
and stops. A run is "ready to hand off" when its selected documents pass
`/evaluate-run` with no blocking defects and every contradiction, assumption,
or open item has been reviewed and either resolved or explicitly accepted by a
human owner. See [Phases](../workflow/phases.md) for the full checkpoint
model.
