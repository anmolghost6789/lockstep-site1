# Package Memory

Durable operational learnings that persist across ADLC cycles. Read at the start of each phase; written only at phase completion, and only when a learning is confirmed.

| File | Holds |
|---|---|
| MEMORY.md | Reusable facts and learnings about running the lifecycle here |
| CONVENTIONS.md | Writing, naming and formatting conventions |
| DECISIONS.md | Decisions that persist until superseded (link the ADR) |
| PATTERN_LIBRARY.md | High-value reusable patterns (agent topologies, eval suites, runbook sections) |

## Promotion rules

Promote only what is reusable, safe, concise and validated by a gate decision or user feedback.

Never promote: client data, PII/PHI, secrets, raw telemetry, prompt transcripts, copied artifact content, unapproved business rules, or one-off assumptions. Every promotion writes a `memory.promoted` note in the phase summary so reviewers can see it.
