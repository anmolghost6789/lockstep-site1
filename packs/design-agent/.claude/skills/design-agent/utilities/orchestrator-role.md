# ORCHESTRATOR ROLE

## Purpose

The orchestrator is **not** a project subagent. The orchestrator is the main Claude Code conversation running the skill/package. This matches the Claude Code subagent model: subagents run isolated loops and return summarized results to the main conversation, while the main conversation retains user interaction, task coordination, and final decisions.

## Orchestrator owns

The main conversation owns:

- run creation and active run selection
- stage transitions across all four phases (/start-design through /evaluate-design)
- reading `CLAUDE.md`, `config/project_config.json`, and the phase skill's SKILL.md before work
- creation and maintenance of `outputs/00_state/run_state.json`, and the run-root `progress.json` UI projection derived from it at each phase boundary (see `utilities/progress-contract.md`)
- creation and maintenance of `outputs/00_state/context_packets/latest_summary.md`
- deciding when a subagent is useful
- narrating when a subagent is spawned, when it finishes, and when no subagent is used
- writing bounded subagent task briefs
- reviewing subagent handoff results
- asking the human questions
- phase-boundary summaries and next-command recommendations
- applying or rejecting context-hierarchy overrides after explicit human confirmation
- final source-selection enforcement
- final same-layer dependency enforcement
- final quality and completion decisions
- reference-store governance decisions after the evaluate-design closure human confirmation

## Orchestrator must not do

The orchestrator must not:

- load every raw document when a subagent can parse and summarize it safely
- ask immediate `/start-design` questions before the input set evaluation report exists
- delegate human conversation to subagents
- allow subagents to talk directly to each other as the primary communication path
- let a subagent silently redesign approved artifacts
- let reference-store material override current run evidence or human input
- rely on chat-only memory for decisions, facts, risks, mappings, or human answers
- store client data, generated artifact content, credentials, PII/PHI, or unapproved business decisions in Claude Code agent memory

## State rule

Durable run state lives on disk, not only in the chat. A decision is not durable until written to the correct run artifact.

Required durable state:

```text
outputs/00_state/run_state.json
outputs/00_state/context_packets/latest_summary.md
outputs/00_state/handoffs/{stage}/
canonical artifacts for the completed/current stage
```

## Subagent coordination rule

The orchestrator delegates focused, bounded tasks to subagents only when context isolation or an independent review is useful. The orchestrator always provides:

```text
outputs/00_state/handoffs/{stage}/{agent_name}_task.md
```

and requires the subagent to return:

```text
outputs/00_state/handoffs/{stage}/{agent_name}_result.md
outputs/00_state/handoffs/{stage}/{agent_name}_result.json
```

The orchestrator reads the result summary first, then only reads detailed artifacts when needed.

## Learnings/reference-store ownership

- The /start-design source-discovery step may consult `context/reference/processed/` only through governed filtering and records the consultation in `source_decisions.json.reference_store_audit`.
- /design-architecture may consult `context/reference/processed/` only through governed filtering and must write `outputs/00_state/design/reference_use_audit.json`.
- The evaluate-design closure tail (or learning-curator) may propose learnings and reference-store candidates, but the orchestrator must ask the human before adding current-run material into `context/reference/`.
- The orchestrator applies conservative metadata defaults when metadata is missing.
- Client-specific or provisional patterns are advisory only and cannot be the sole grounding for design decisions.

## User-visible delegation updates

The orchestrator must keep the user informed about delegation at a high level:

- When spawning a subagent, say which subagent is being used, why it is being used, and what handoff it will produce.
- When a subagent finishes, say whether it completed, was blocked, or needs human input, and list the key durable outputs.
- When the orchestrator decides not to delegate a stage that could have used a subagent, say briefly why the work is being handled directly.

These updates must be concise and must not expose private reasoning or raw internal scratch work.

## Agent memory usage

The orchestrator may use Claude Code project memory only for safe operational lessons about using this package. It must follow `.claude/skills/design-agent/utilities/memory-policy.md` and keep that memory separate from:

```text
memory/
context/reference/
outputs/
```

Business facts, client-specific mappings, human approvals, run decisions, and artifact lineage must be written to durable run files or governed learning/reference-store artifacts, not to agent memory.

