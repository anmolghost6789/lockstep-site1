# CONTEXT MANAGEMENT POLICY

## Purpose

Long artifact-generation runs can fill the main Claude Code context before the workflow finishes. This package must not rely on manual `/compact` or chat memory as the primary state mechanism. The run state, facts, decisions, and handoffs must live on disk so the workflow survives context pressure, auto-compaction, session restarts, and subagent delegation.

## Operating principle

The main conversation is the orchestrator. It is not a `.claude/agents/` subagent. For detailed role ownership, also read `.claude/skills/design-agent/utilities/orchestrator-role.md`. It owns:

- active run selection
- human-facing communication
- phase-boundary summaries and next-command recommendations
- run state transitions
- final conflict decisions
- final package behavior

The orchestrator should keep its own context small. It should read concise stage reports, manifests, handoff summaries, and canonical JSON artifacts. It should avoid loading large raw input documents, parsed file dumps, generated workbooks, or long logs unless needed to resolve a specific issue.

## Canonical state is file-based

Every run must maintain canonical state under its run-scoped intermediate folder:

```text
outputs/00_state/
  run_state.json
  file_inventory.json
  validation_log.json
  handoffs/
  context_packets/
  ideal_input_set/
  standard_input_set/
  source_discovery/
  design/
  execution_plan/
  human_review/
  evaluation/
  logs/
```

The top-level `outputs/00_state/run_state.json` points to the active run when no run ID is supplied.

A fact, decision, unresolved question, risk, selected source, mapping, DQ rule, validation finding, or human answer is not considered durable until written to the correct run artifact.

## Context budget guardrails

Delegate to a subagent when any of these are true:

- A task requires reading 10 or more files.
- A task requires inspecting large PDFs, PowerPoints, workbooks, zipped inputs, or many parsed files.
- A task requires repetitive validation across many sheets/tables/columns.
- A task benefits from an independent fresh review.
- The orchestrator would need to load large raw text or many generated artifacts to proceed.
- The task can be completed from a focused input packet and returned as a bounded report.

Do not delegate when:

- The task is a small clarification or a phase-boundary summary.
- The task requires direct human conversation.
- Several subagents would need to edit the same file concurrently.
- A single sequential reasoning thread is safer than multiple handoffs.

## Context packets

At the end of each major stage, create or update a compact packet:

```text
outputs/00_state/context_packets/{stage_number_slug}_summary.json
outputs/00_state/context_packets/{stage_number_slug}_summary.md
```

Minimum contents:

```json
{
  "run_id": "RUN_YYYYMMDD_HHMMSS_IST",
  "stage": "02 - Standardize_Inputs",
  "status": "complete | blocked | needs_human | risk_documented",
  "canonical_artifacts": ["outputs/00_state/standard_input_set/data_requirements.json"],
  "key_decisions": [],
  "open_questions": [],
  "risks": [],
  "confidence": 0,
  "next_stage_inputs": [],
  "do_not_forget": []
}
```

The orchestrator should read these packets before deciding whether to inspect detailed artifacts.

## Main-context loading policy

The orchestrator may read directly:

- `outputs/00_state/run_state.json`
- `input_set_evaluation_report.md`
- stage summaries/context packets
- small JSON manifests
- specific evidence snippets needed for a decision

The orchestrator should delegate or request a focused report before reading:

- complete BRDs or PDFs
- large parsed files
- complete source inventories with many tables
- complete column mappings for many tables
- generated Excel workbook content
- verbose logs

## Handoff summaries

Every subagent result must include a bounded summary with:

- task scope
- files inspected
- artifacts written/updated
- key findings
- blockers
- assumptions
- confidence
- explicit items requiring orchestrator or human decision

The orchestrator should not accept a handoff that lacks artifact paths or evidence references.

## Compaction-resilience rule

Before and after any context-heavy stage, ensure these exist and are current:

```text
outputs/00_state/run_state.json
outputs/00_state/context_packets/latest_summary.md
outputs/00_state/handoffs/{stage}/
```

If auto-compaction or session restart happens, `/status` and the normal continuation conversation must be able to reconstruct the workflow from disk without relying on chat-only memory.

## No information loss rule

Subagents may summarize for the orchestrator, but they must not discard source evidence. Detailed extraction, evidence maps, design matrices, and validation outputs remain in run artifacts. Summaries are navigation aids, not replacements for canonical data.
