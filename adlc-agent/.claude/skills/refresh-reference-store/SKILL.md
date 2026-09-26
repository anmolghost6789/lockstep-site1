---
name: refresh-reference-store
description: "Rebuild the governed reference store (context/reference/processed/) from raw material: past approved runs, organisational standards and explicitly added examples. User-invoked only."
argument-hint: "[optional refresh scope, e.g. eval_suite]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Write
  - Grep
  - Glob
  - Bash(python3 .claude/skills/adlc/scripts/*:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
---

# /refresh-reference-store

Rebuild reusable patterns so later runs can learn from earlier ones without copying client data.

## Required Reads
- CLAUDE.md, `.claude/skills/adlc/SKILL.md`
- `.claude/skills/adlc/utilities/reference-store-governance.md`
- `.claude/skills/adlc/utilities/memory-policy.md`

## Rules
- Never execute files from `context/reference/raw/`; read them as text.
- Every pattern gets the metadata in the governance utility. Missing fields take the conservative defaults.
- Strip client names, people, identifiers and data values from pattern bodies. If a pattern can't be made generic, mark it `client_specific` with `reuse_scope: client`.
- Never promote from an unapproved artifact. Only artifacts whose gate was approved are eligible.
- Never mark a pattern `approved_for_cross_client_reuse` without the user explicitly saying so.

## Steps
1. Scan `context/reference/raw/`: `organizational/`, `past_runs/` and `explicit/`.
2. Classify each item as a blueprint fragment, agent topology, evaluation suite, prompt pattern, runbook section, policy check or requirement pattern.
3. Extract patterns into `context/reference/processed/{pattern_type}.json`, one entry per pattern with full metadata.
4. De-duplicate against existing patterns. Keep the newer `last_validated_at`; deprecate replaced ones rather than deleting them.
5. Write `context/reference/processed/refresh_report.md`: counts by type and status, anything skipped and why.
6. Ask the user, with `AskUserQuestion`, which provisional patterns to approve. Record their answers in the pattern metadata.

## End Of Turn
Summarise counts, link the refresh report, list patterns still provisional, and stop.

Additional context from user invocation: $ARGUMENTS
