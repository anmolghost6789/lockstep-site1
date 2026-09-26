# MEMORY POLICY

## Two durable stores

- `memory/`: operational learnings about running the ADLC here, across runs. Promoted into only at phase completion, and only when a learning is confirmed.
- `context/reference/`: governed reusable reference material (blueprint fragments, evaluation suites, runbook sections), promoted into only with explicit human approval under `reference-store-governance.md`.

Both are separate from `adlc/.state/`, which is run-scoped, and from the phase artifacts under `adlc/`.

## The memory files

- `README.md`: the store and its promotion rules
- `MEMORY.md`: durable, non-confidential operational facts
- `CONVENTIONS.md`: conventions the lifecycle should follow
- `DECISIONS.md`: decisions that persist until superseded (link the ADR)
- `PATTERN_LIBRARY.md`: reusable, generic patterns

## Promotion

Only reusable, safe learnings validated by a gate decision or explicit user feedback, and only with the user's agreement:

- conventions → `CONVENTIONS.md`
- durable decisions → `DECISIONS.md`
- reusable patterns → `PATTERN_LIBRARY.md`
- other durable facts → `MEMORY.md`

Mention every promotion in the phase summary so reviewers can see it.

## Never store

client confidential data, PII/PHI, credentials, raw telemetry, prompts containing client data, copied artifact content, unapproved business rules, or one-off assumptions.

## Memory is not evidence

Never cite memory as the basis for a requirement, design choice, threshold or release decision. Evidence comes from current inputs, human answers, approved upstream artifacts, config defaults, or approved reference-store items. Memory never overrides any of them.
