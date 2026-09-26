# AGENT MEMORY POLICY

## Purpose

This package has two distinct durable stores. Do not confuse them:

- Top-level `memory/`: the package's operational durable memory. It holds only reusable, safe, human-validated operational learnings across runs. It is maintained as five markdown files (see below) and is promoted into only at run close.
- `context/reference/`: the governed reusable business/data-engineering reference store, promoted into only with explicit human approval per its own governance metadata.

Both are separate from `outputs/00_state/`, which holds run-scoped intermediate state, and from `outputs/`, which holds deliverables.

## The five memory files

Top-level `memory/` contains exactly five markdown files:

- `README.md` — explains the store and the promotion rules.
- `MEMORY.md` — durable, non-confidential operational facts that do not fit the other files.
- `CONVENTIONS.md` — recurring conventions the package should follow.
- `DECISIONS.md` — durable operational decisions worth remembering across runs.
- `PATTERN_LIBRARY.md` — reusable, generic process/design patterns.

Seed copies live under `.claude/skills/design-agent/templates/memory/`.

## Promotion routing

Only reusable, safe, human-validated learnings are promoted, and only at the `/evaluate-design` closure tail under human approval:

- conventions → `CONVENTIONS.md`
- durable decisions → `DECISIONS.md`
- reusable patterns → `PATTERN_LIBRARY.md`
- other durable, non-confidential facts → `MEMORY.md`

## Boundaries

Agent memory is operational only. It must never contain:

- client confidential data, raw source extracts, or generated artifact contents;
- PII/PHI;
- unapproved client-specific business rules or business facts;
- credentials.

Such material belongs only in `outputs/00_state/`, or in `context/reference/` under its governance rules once human-approved.

Do not use agent memory as evidence for generated artifacts. Generated artifact `References` must point to current-run inputs, human clarifications, `config/project_config.json` defaults, approved reference-store items, or explicit inference records.

Do not use agent memory to override current BRD, source inventory, selected sources, approved design, human input, or reference-store governance.
