# AI Product Requirement Spec: {{intent_title}}

| Field | Value |
|---|---|
| Intent ID | {{intent_id}} |
| Business owner | {{owner_role}} (named at gate G1) |
| Source | {{intent_source: file, Jira epic, or backlog item BL-NNN}} |
| Data classification | {{highest level among inputs}} |

## Intent

{{Two or three sentences: the business outcome, for whom, and why now.}}

## Personas

| ID | Persona | Goal | Pain today |
|---|---|---|---|
| P-001 | {{persona}} | {{goal}} | {{pain}} |

## User Stories

| ID | As a | I want | So that | Trace |
|---|---|---|---|---|
| US-001 | {{persona}} | {{capability}} | {{benefit}} | Trace: {{P-001}} |

## Functional Requirements

| ID | Requirement | Acceptance test | Trace |
|---|---|---|---|
| FR-001 | {{testable requirement}} | {{how it is verified}} | Trace: US-001 |

## Non-Functional Requirements

Every NFR measured in phase 04 states its threshold here.

| ID | Category | Requirement | Threshold | Trace |
|---|---|---|---|---|
| NFR-001 | Accuracy | {{what is measured}} | {{e.g. ≥ 0.90}} | Trace: FR-001 |
| NFR-002 | Safety | {{e.g. no credit issued without human approval}} | {{e.g. 0 violations}} | Trace: FR-001 |
| NFR-003 | Latency | {{p95 end-to-end}} | {{e.g. ≤ 5 s}} | Trace: US-001 |

## Risks and Constraints

| ID | Risk or constraint | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-001 | {{risk}} | {{L/M/H}} | {{L/M/H}} | {{mitigation}} |

## Success Criteria

| ID | Measure | Baseline | Target | Window | Trace |
|---|---|---|---|---|---|
| SC-001 | {{business measure}} | {{today}} | {{target}} | {{e.g. 30 days after release}} | Trace: US-001 |

## Open Questions

| # | Question | Answer | Answered by | Status |
|---|---|---|---|---|
| 1 | {{question}} | {{answer}} | {{role}} | {{open / resolved}} |
