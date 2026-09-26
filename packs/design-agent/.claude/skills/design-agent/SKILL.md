---
name: design-agent
description: "Shared hidden protocol for the Design Agent phase skills that generate STTM, Data Model, DQ, and ER Diagram artifacts."
argument-hint: "[optional run context, project name, or action]"
user-invocable: false
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

# Data Artifact Generation Skill

This hidden skill is the shared protocol for Design Agent phase skills. User-facing actions are /start-design-run (ingest + readiness + source discovery), /design-architecture (design + execution plan), /generate-artifacts, /evaluate-design (which also closes the run), /status, /cancel, and /refresh-reference-store.

Controls:
- Stop at every phase boundary. Recommend the next slash skill; do not auto-invoke it. The user invoking the next command IS the approval to proceed.
- /start-design-run applies the empty-input guard before creating run files.
- Use selected sources only unless a waiver is recorded.
- Use precedence: confirmed clarifications > user_instructions > project_context > domain_context > enterprise_context > reference_store > defaults.
- Delegate only to input-analyzer, design-writer (escape-hatch), artifact-writer, and design-evaluator under their thresholds.
- File-based handoffs are only for parallel artifact-writer fan-out.
- /evaluate-design writes evaluation_report.md and evaluation_scores.json AND runs the closure tail (memory promotion, reference-store decision, runtime scratch cleanup, mark completed).
- Keep chat concise; summarize and link to files rather than pasting report or artifact bodies.
- Every phase is idempotent on re-entry: re-invoking a phase detects existing valid artifacts and redoes only what is missing or stale.

Additional context from user invocation: $ARGUMENTS
