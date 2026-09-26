# CONTEXT MANAGEMENT POLICY

## Purpose

A full lifecycle run can fill the conversation's context before it finishes. The ADLC must not depend on chat memory or manual compaction. State, decisions and handoffs live on disk, so a run survives context pressure, restarts, a switch between Copilot and Claude Code, and subagent delegation.

## Canonical state

```text
adlc/.state/
  run_state.json          # the ledger (written by scripts/state.py)
  validation/             # per-phase validation results
  policy/                 # per-phase policy results
  context_packets/        # compact summaries per phase + latest_summary.md
  handoffs/{phase}/       # subagent task briefs and results
  index/                  # input index (pointers, not content)
  eval/                   # evaluation raw results and human-review samples
  evidence/               # CI evidence files (license scan, SBOM)
  runtime_scratch/        # temporary code (see runtime-code-policy.md)
```

## Delegate when

- a task needs 10 or more input files, or large PDFs, spreadsheets or archives
- validation is repetitive across many units, metrics or files
- an independent review is required (evaluation, release readiness)
- the orchestrator would otherwise load large raw text

## Don't delegate when

- it is a small clarification or a phase-boundary summary
- the task needs direct human conversation
- several subagents would edit the same file

## Context packets

At the end of each phase write `adlc/.state/context_packets/{NN}-{phase}.json` and `.md`:

```json
{
  "run_id": "adlc-xxxxxxxx",
  "phase": "02 architect-design",
  "status": "complete | blocked | needs_human",
  "artifact": "adlc/02-blueprint.md",
  "gate": { "id": "G2", "pull_request": "url", "approver_role": "architect" },
  "key_decisions": [],
  "open_questions": [],
  "risks": [],
  "next_phase_inputs": [],
  "do_not_forget": []
}
```

Update `latest_summary.md` at the same time. Read packets before reading detailed artifacts.

## Main-context loading

Read directly: `run_state.json`, context packets, small JSON reports, and the specific artifact section needed for a decision. Delegate or ask for a focused report before reading whole input documents, full evaluation results, or long logs.

## Handoff summaries

Every subagent result states: scope, files inspected, files written, key findings, blockers, assumptions, confidence, and items needing an orchestrator or human decision. Reject a result that lacks file paths or evidence.

## Resilience

Before and after a context-heavy phase, make sure `run_state.json`, `latest_summary.md` and the phase handoffs are current. After a restart, `/status` must be able to reconstruct where the run is from disk alone.

## No information loss

Summaries are navigation aids. Detailed evidence stays in the run artifacts.
