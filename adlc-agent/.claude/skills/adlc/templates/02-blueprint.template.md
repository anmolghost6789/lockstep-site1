# Agentic Solution Blueprint: {{intent_title}}

| Field | Value |
|---|---|
| Intent ID | {{intent_id}} |
| AIPRS sha256 (approved at G1) | {{sha256 from adlc/.gates/G1.json}} |

## Context

{{Current and target business/domain flow in a short paragraph plus a diagram reference. Cite AIPRS IDs.}}

## Level-1 Plan

| ID | Unit | Goal | Depends on | Acceptance tests | Trace |
|---|---|---|---|---|---|
| UNIT-001 | {{unit name}} | {{goal}} | {{- or UNIT-00N}} | {{tests}} | Trace: FR-001 |

## Agent Topology

| ID | Agent | Responsibilities | Can take external actions? | Human-in-the-loop control | Trace |
|---|---|---|---|---|---|
| AGT-001 | {{agent}} | {{what it does}} | {{yes/no, which}} | {{approval point}} | Trace: UNIT-001 |

Orchestration: {{how agents hand off, retries, timeouts, and what happens on failure}}.

## Model Selection

| Agent | Model (approved list only) | Why | Data classification seen | Fallback |
|---|---|---|---|---|
| AGT-001 | {{model id}} | {{reason}} | {{level}} | {{fallback}} |

## Knowledge and RAG Design

{{Sources, access control, chunking, retrieval, citation policy, freshness and re-index schedule. Trace to NFRs.}}

## Tools and MCP Integration

| Tool / MCP server | Scopes | Read or write | Dry-run strategy | Trace |
|---|---|---|---|---|
| {{server}} | {{scopes}} | {{r/w}} | {{how writes are simulated before release}} | Trace: UNIT-001 |

## Security and Governance

{{Threat model summary, PII handling, guardrails, audit points, and which NFRs each control satisfies.}}

## Decisions

| ID | Decision | File |
|---|---|---|
| ADR-001 | {{decision}} | adlc/adr/ADR-001-{{slug}}.md |
