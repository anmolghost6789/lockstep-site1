---
name: refresh-reference-store
description: "Rebuild processed governed reference-store patterns from raw reference-store material. User-invoked only."
argument-hint: "[optional refresh scope]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Grep
  - Glob
  - Bash(cat:*)
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(grep:*)
  - Bash(mkdir:*)
  - Bash(cp:*)
  - Bash(mv:*)
  - Bash(rm:*)
  - Bash(python3:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# /refresh-reference-store

Rebuild the processed reference store from raw governed material.

1. Read `CLAUDE.md`, `.claude/skills/design-agent/SKILL.md`, `.claude/skills/design-agent/utilities/reference-store-governance.md`, and `.claude/skills/design-agent/utilities/file-parsing.md`.
2. Scan `context/reference/raw/` recursively:
   - `organizational/`
   - `past_runs/`
   - `explicit/`
3. Parse each file without executing user-provided `.py` files. Classify each file as STTM, Data Model, DQ, BRD, SQL, rules, source catalog, or other.
4. Extract patterns with governance metadata/defaults:
   - `source_usage_patterns.json`
   - `column_mapping_patterns.json`
   - `transformation_catalog.json`
   - `entity_design_patterns.json`
   - `dq_patterns_history.json`
   - `domain_knowledge.json`
5. Exclude, quarantine, or mark inactive any restricted/rejected/deprecated/do-not-reuse-directly patterns.
6. Write processed outputs to `context/reference/processed/` and update `context/reference/_metadata.json` with an IST `+05:30` timestamp, counts, schema version, governance defaults, blocked/quarantined counts, and eligible cross-client counts.
7. Report a concise summary to the human, including patterns blocked by governance and patterns eligible for reuse.

This skill is user-invoked only because it mutates persistent governed knowledge.

Arguments: $ARGUMENTS

