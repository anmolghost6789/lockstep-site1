# Jira Story Pack

<!--
Use this template only when no user-supplied Jira template is selected.
Preserve the structure, replace placeholders with grounded content, and remove
instruction comments from the final document. Do not invent Jira configuration,
roles, estimates, labels, priorities, or workflow states.
-->

## Cover Page

| Field | Value |
|---|---|
| Project / Product | `<name or [INSUFFICIENT INPUT]>` |
| Story Pack Version | `<version>` |
| Status | `<Draft / Reviewed / Approved, when evidenced>` |
| Prepared Date | `<YYYY-MM-DD>` |
| Source Baseline | `<source or knowledge references>` |

## Document Control

### Revision History

| Version | Date | Change | Author / Owner |
|---|---|---|---|
| 0.1 | `<YYYY-MM-DD>` | Initial evidence-based draft | `<owner or [INSUFFICIENT INPUT]>` |

### Distribution List

| Audience | Purpose |
|---|---|
| `<audience>` | `<purpose>` |

## 1. Purpose and Scope

State the purpose, included and excluded work, source baseline, and target Jira
project when known. Generation does not publish issues; publication requires the
separate `/publish-to-jira` command and explicit confirmation.

## 2. Jira Configuration

Record only fields established by evidence or a selected template.

| Configuration | Value | Evidence / Open Item |
|---|---|---|
| Project key | `<value or [INSUFFICIENT INPUT]>` | `<source ID or OI-ID>` |
| Issue hierarchy | `<value or [INSUFFICIENT INPUT]>` | `<source ID or OI-ID>` |
| Required fields | `<value or [INSUFFICIENT INPUT]>` | `<source ID or OI-ID>` |
| Acceptance style | `<value or [INSUFFICIENT INPUT]>` | `<source ID or OI-ID>` |
| Estimation / priority / labels | `<only when defined>` | `<source ID or OI-ID>` |

## 3. Actors and Delivery Roles

Include only actors and roles grounded in evidence or the selected template.

| Actor / Role | Responsibility in Scope | Evidence IDs |
|---|---|---|
| `<actor or role>` | `<responsibility>` | `<IDs>` |

## 4. Definition of Done

State project-wide completion criteria only when supported by evidence. Story-
specific acceptance criteria remain with each story.

| DoD ID | Completion Criterion | Evidence IDs / Open Item |
|---|---|---|
| DOD-001 | `<criterion or [INSUFFICIENT INPUT]>` | `<IDs or OI-ID>` |

## 5. Epic Proposals

| Epic ID | Outcome | Scope | Evidence IDs | Dependencies |
|---|---|---|---|---|
| `<EPIC-ID>` | `<measurable outcome>` | `<included scope>` | `<IDs>` | `<IDs or None>` |

## 6. Stories

Repeat this block for every independently valuable outcome.

### Story: `<Story ID>` — `<Summary>`

| Field | Value |
|---|---|
| Epic | `<EPIC-ID>` |
| Issue Type | `<evidenced value or [INSUFFICIENT INPUT]>` |
| Actor / Responsible Role | `<grounded actor or role>` |
| Outcome | `<capability and measurable benefit>` |
| Priority | `<evidenced value or blank>` |
| Estimate | `<evidenced value or blank>` |
| Labels / Custom Fields | `<evidenced values or blank>` |
| Dependencies | `<Story IDs, external dependency IDs, or None>` |
| Source Evidence | `<source IDs>` |
| Knowledge Links | `<canonical knowledge IDs>` |

#### Description

`<Evidence-grounded description. Use a user-story sentence only when the selected template requires one.>`

#### Acceptance Criteria

| AC ID | Observable Criterion | Evidence IDs | Open Item |
|---|---|---|---|
| `<Story ID>-AC-001` | `<observable, independently testable outcome>` | `<IDs>` | `<OI-ID or None>` |

#### Constraints and Assumptions

| Type | Statement | Evidence IDs / Open Item |
|---|---|---|
| `<Constraint / Assumption>` | `<statement>` | `<IDs or OI-ID>` |

#### Subtasks

Include this subsection only when the selected template or evidenced delivery
process requires subtasks. Derive every role, field, and completion condition
from that source.

| Subtask ID | Outcome / Responsibility | Owner Role | Completion Condition | Evidence IDs |
|---|---|---|---|---|
| `<ID>` | `<outcome>` | `<grounded role>` | `<observable condition>` | `<IDs>` |

## 7. Traceability Matrix

| Story ID | Epic ID | Requirement / Knowledge IDs | Acceptance Criteria | Open Items |
|---|---|---|---|---|
| `<Story ID>` | `<EPIC-ID>` | `<IDs>` | `<AC IDs>` | `<OI IDs or None>` |

## 8. Open Items

Every `[INSUFFICIENT INPUT]` marker must resolve to one row here.

| Open Item ID | Missing Decision / Evidence | Impact | Requested From | Related IDs | Status |
|---|---|---|---|---|---|
| OI-001 | `<specific question or missing evidence>` | `<affected fields or stories>` | `<role or stakeholder>` | `<IDs>` | Open |
