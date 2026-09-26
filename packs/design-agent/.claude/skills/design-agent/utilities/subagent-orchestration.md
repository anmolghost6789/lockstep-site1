# SUBAGENT ORCHESTRATION PROTOCOL

## Why this exists

This workflow can read many documents, parse complex source inventories, design multi-layer lineage, generate multiple Excel workbooks, and validate outputs. Doing all of that in the main conversation fills context quickly. Subagents provide isolated context windows for focused work and return bounded results to the main conversation.

## Correct Claude Code pattern

The orchestrator is the **main Claude Code conversation** using this skill/package. It is not a `.claude/agents/` subagent. Project subagents are worker specialists under `.claude/agents/`.

Subagents:

- run in isolated context windows
- receive a focused task and selected files/artifacts
- return summaries and handoff files
- do not ask the human directly
- do not talk to each other directly as the normal communication path

When direct peer-to-peer multi-session coordination is needed, that is an agent-team pattern, not this package's default. This package intentionally uses a single main orchestrator plus file-based subagent handoffs because it is safer for human decision points, auditability, and information preservation.

## Roles

### Orchestrator: main conversation only

The orchestrator:

- reads `CLAUDE.md`, `config/project_config.json`, `.claude/skills/design-agent/utilities/orchestrator-role.md`, and the current phase skill's SKILL.md
- creates/updates `run_state.json`
- decides when to delegate
- writes task briefs
- receives and reviews handoffs
- asks the human questions
- presents phase-boundary summaries and recommends the next command
- resolves conflicts after human confirmation
- enforces selected-source-only design
- enforces same-layer dependency rules
- ensures final outputs comply with the package contract
- owns final reference-store decisions

The orchestrator does not hand off human communication to subagents.

### Subagents

Subagents are focused workers defined in `.claude/agents/`:

| Subagent | Main phase | Purpose |
|---|---|---|
| `input-analyzer` | /start-design | Thin-index classification of large input sets (two parallel instances with disjoint `scope=requirements` / `scope=sources` assignments). |
| `design-writer` | /design-architecture (escape hatch only) | Appends pre-designed table specs for one layer to the shared canonical design JSONs. |
| `artifact-writer` | /generate-artifacts (rare) | Layer-scoped invocation of the shipped canonical generator; never writes its own generator. |
| `design-evaluator` | /evaluate-design (always) | Independent output review, deterministic-check ingestion, semantic scoring, error classification. |

There is intentionally no separate orchestrator worker subagent. Keeping the orchestrator as the main conversation preserves human decision handling and follows the normal Claude Code subagent control flow.

## User-visible delegation narration

The orchestrator must narrate subagent usage to the user. This is not optional.

Before spawning a subagent, state:

```text
I am delegating {stage/task} to `{agent_name}` because {reason}. It will write `{handoff_path}` and I will review the result before proceeding.
```

When a delegation rule is considered but not used, state:

```text
I am handling {stage/task} in the main orchestration context because {reason}. No subagent is needed for this step.
```

After the subagent returns, state:

```text
`{agent_name}` completed {stage/task}. Status: {status}. Key outputs: {files_or_findings}. Next: {orchestrator_next_action}.
```

Keep the message brief. Do not expose raw chain-of-thought or large internal handoffs in chat.

## Agent memory boundary

Project-level Claude Code memory, when available, may be used for operational package behavior only: recurring orchestration mistakes, useful delegation heuristics, validator failures, template-handling lessons, and safe workflow improvements. It is separate from `memory/` and `context/reference/`.

Subagents must follow `.claude/skills/design-agent/utilities/agent-memory-policy.md`. They must not store client confidential information, raw source data, generated artifact rows, business facts, credentials, PII/PHI, or unapproved project-specific decisions in agent memory.

## Communication contract

Subagents do not talk to each other directly. Communication path is:

```text
Orchestrator -> task brief file + subagent prompt
Subagent -> handoff result files + concise returned summary
Orchestrator -> reads result, updates run state, decides next action
```

Use these paths:

```text
outputs/00_state/handoffs/{stage}/{agent_name}_task.md
outputs/00_state/handoffs/{stage}/{agent_name}_result.md
outputs/00_state/handoffs/{stage}/{agent_name}_result.json
outputs/00_state/context_packets/{stage_number_slug}_summary.md
outputs/00_state/context_packets/{stage_number_slug}_summary.json
```

## Task brief template

```markdown
# Subagent Task Brief

- Run ID:
- Stage:
- Subagent:
- Objective:
- Read these package rules:
- Read these run artifacts:
- Write/update only these artifacts:
- Do not modify:
- Reference-store access allowed: yes/no and scope
- Constraints:
- Required result format:
- Stop/return conditions:
```

## Result JSON template

```json
{
  "run_id": "RUN_YYYYMMDD_HHMMSS_IST",
  "stage": "start-design",
  "agent_name": "input-analyzer",
  "status": "complete | blocked | needs_orchestrator | needs_human | failed",
  "files_read": [],
  "files_written": [],
  "key_findings": [],
  "decisions_applied": [],
  "assumptions": [],
  "risks": [],
  "human_questions_recommended": [],
  "reference_store_accessed": false,
  "reference_patterns_used": [],
  "confidence": 0,
  "next_recommended_action": "string",
  "memory_notes_written": false
}
```

## Delegation by phase

### /start-design

Delegate input classification to `input-analyzer` only above the documented thresholds (more than 15 input files, snapshot larger than 15 MB, or more than 30 declared source tables); fan out two instances with disjoint `scope` arguments per `.claude/agents/input-analyzer.md`. The orchestrator still creates the run, owns state, writes the readiness report, and makes every source decision itself (source discovery is orchestrator work — there is no source-discovery subagent). It may consult governed reference-store processed patterns for source-candidate hints and records the consultation in `source_decisions.json.reference_store_audit`.

### /design-architecture

The orchestrator designs inline via the per-table append loop by default. Spawn `design-writer` only in the documented escape-hatch case (single layer > 10 tables AND first-3-table telemetry over 90s each AND context over ~120k tokens), passing fully pre-designed specs. If the orchestrator consults reference-store processed patterns for architecture/mapping/DQ precedents, it writes `outputs/00_state/design/reference_use_audit.json`. The orchestrator ensures the design uses only selected or human-approved sources and no unapproved same-layer physical dependencies before completing the phase; the plan step runs the shipped `build_plan.py` — never a planning subagent.

### /generate-artifacts

Run the shipped canonical generator inline by default. Spawn `artifact-writer` only when the run has more than 15 target tables AND generation demonstrably needs per-layer supervision; the subagent also only invokes the shipped script.

### /evaluate-design

Always delegate independent validation to `design-evaluator`. The evaluator should be a fresh reviewer and should not rely on assumptions from the generation step. The closure tail (learnings, reference-store question, completion) is orchestrator work: it asks the human whether to store current-run material (only when `context/reference/` exists) and applies governance metadata before updating `context/reference/`. Nothing is cleaned up at closure.

## Learnings and reference-store responsibility matrix

| Area | Primary worker | Orchestrator responsibility |
|---|---|---|
| `memory/agent/` | orchestrator (evaluate-design closure tail) | Verify error classification and active/inactive status. |
| `memory/input_set/` | orchestrator (evaluate-design closure tail) | Verify gaps/clarification outcomes are represented accurately. |
| `memory/human/` | orchestrator (evaluate-design closure tail) | Verify human statements are not distorted or over-generalized. |
| `context/reference/raw/` | orchestrator stages selected artifacts after human approval | Decide YES/NO/SELECTIVE with the human. |
| `context/reference/processed/` | `/refresh-reference-store` | Ensure metadata defaults and reuse limits are applied. |
| `context/reference/_metadata.json` | `/refresh-reference-store` | Final review; block unsafe cross-client reuse. |
| Reference use during /start-design and /design-architecture | orchestrator | Record the reference audits (`source_decisions.json.reference_store_audit`, `design/reference_use_audit.json`) and prevent override of current evidence. |

## Conflict and edit safety

- Never run two write-capable subagents concurrently on the same files.
- Do not let subagents modify `inputs/`, `.claude/skills/design-agent/`, `.claude/`, `.claude/skills/design-agent/templates/workbooks/`, or `config/` during a normal artifact-generation run.
- Subagents may write only to their assigned runs/output paths unless the orchestrator explicitly authorizes more.
- Subagents must return rather than improvise when they find a blocker.

## Human communication rule

Subagents can recommend questions. They do not ask the user directly. The orchestrator consolidates questions, removes duplicates, assigns priorities, and asks the human after the correct report.

## State update rule

After each subagent result, the orchestrator must update:

```text
outputs/00_state/run_state.json
outputs/00_state/context_packets/latest_summary.md
```

If those are not updated, the run is not compaction-safe.
