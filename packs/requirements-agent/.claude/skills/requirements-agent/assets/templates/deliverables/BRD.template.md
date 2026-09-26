<!--
Template ID: BRD
Template role: Source-of-truth structure for the consolidated Business Requirements Document.

This is the CONSOLIDATED BRD template. It absorbs the prior UC, KBQ, KPI, and Metric
deliverables as embedded sections (4A, 5A, 5B, 5C). Stakeholders consume the BRD,
not separate UC / KBQ / KPI / Metrics documents.

Generation rules:
- Preserve every heading in this template in the generated markdown.
- Replace guidance comments with evidence-backed content; do not copy comments into the final deliverable.
- Do not invent content to fill a section.
- Missing required evidence must appear inline as:
    [INSUFFICIENT INPUT] <specific missing detail and expected content (NOT a filename)>.
- Reasonable assumptions must appear inline as:
    [ASSUMPTION] <assumption>. Confidence: <Low|Medium|High>. Validation needed from <source/stakeholder>.
- Every inline missing item or assumption must also be listed in "11. Open Items".
- Keep content depth proportional to extracted evidence.

Embedded analytical sections (4A, 5A, 5B, 5C) — generation rules:
- Sections 4A, 5A, 5B, 5C are ALWAYS present in the template.
- Populate them from applicable linked knowledge.
- If no supported concept exists for a category, populate the section
  with: "[INSUFFICIENT INPUT] No <category> were identified from available inputs. If
  <category> are relevant, provide <content description> in your inputs."
- Do NOT omit sections 4A / 5A / 5B / 5C. They must always appear, even if sparse.
- Do not bypass the knowledge phase or infer missing facts from the template.

Evidence-driven exception:
- Section 6 may be retitled to match the evidenced dependency landscape (data,
  interfaces, events, or external services) while preserving its purpose. Mark
  unsupported required fields as insufficient input; do not infer a domain model.
-->

# Business Requirements Document

## Cover Page

| Field | Value |
|---|---|
| Client |  |
| Project |  |
| Document | Business Requirements Document |
| Version |  |
| Date |  |
| Confidentiality |  |

## Document Control

### Revision History

| Version | Date | Author | Changes |
|---|---|---|---|

### Approval and Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|

### Distribution List

| Name/Group | Role | Purpose |
|---|---|---|

## Table of Contents

<!-- Generate a fully clickable GFM TOC using standard GitHub Markdown heading slugs.
Two-level: top-level numbered sections as bullets (`-`), sub-sections (3.1, 4A, 5B …) indented two spaces.
Every line is an anchor link, never plain numbered text. The DOCX renderer replaces this block. -->

## 1. Executive Summary

<!-- Summarize the business problem, solution direction, outcomes, scope boundaries, requirement coverage, and major known gaps without duplicating later sections. -->

## 2. Business Context

### 2.1 Background and Business Drivers

### 2.2 Current State

### 2.3 Future State

## 3. Stakeholders and User Groups

### 3.1 Stakeholder Matrix

| Stakeholder Group | Role | Primary Needs | Priority | Evidence |
|---|---|---|---|---|

### 3.2 User Groups

| User Group | Description | Key Activities | Data Needs | Access Pattern | Evidence |
|---|---|---|---|---|---|

## 4. Scope

### 4.1 In Scope

| Scope Item | Description | Linked UC IDs | Evidence |
|---|---|---|---|

### 4.2 Out of Scope

| Excluded Item | Rationale | Evidence/Decision |
|---|---|---|

### 4.3 Dependencies

| Dependency | Type | Owner/System | Impact | Evidence |
|---|---|---|---|---|

## 4A. Use Case Scenarios

<!-- Absorbed from the former Use Case Document (UC). Contains the analytical depth
     previously in the standalone UC deliverable. Populate from applicable UC-* concepts. -->

### 4A.1 Summary Table

| UC ID | Use Case Name | Primary Actor | Trigger | Priority | Linked BR IDs | Evidence |
|---|---|---|---|---|---|---|

### 4A.2 Detailed Use Cases

<!-- Repeat the block below for every evidence-backed use case. Preserve the same
     analytical depth as the former UC document. -->

#### UC-<NNN>: <Use Case Name>

| Field | Value |
|---|---|
| Primary Actor |  |
| Supporting Actors |  |
| Trigger |  |
| Preconditions |  |
| Priority |  |
| Evidence |  |
| Confidence |  |

**Main Flow:**

1. <step>

**Alternative Flows:**

- <alt flow>

**Exception Flows:**

- <exception>

**Postconditions:**

- <post>

**Business Rules:**

- <rule>

**Linked KBQ IDs / KPI IDs:**

- <link>

## 5. Business Requirements

### 5.1 Summary Table

| Req ID | Category | Requirement Summary | Priority | UC Reference | Confidence |
|---|---|---|---|---|---|

### 5.2 General Requirements

| Req ID | Category | Requirement | Priority | Acceptance Criteria | Evidence | Confidence |
|---|---|---|---|---|---|---|

### 5.3 Capability-Specific Requirements

<!-- Repeat the block below for every evidence-backed capability. -->

#### Capability: <Capability Name>

| Req ID | Category | Requirement | Priority | Release/Phase | Acceptance Criteria | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

## 5A. Key Business Questions

<!-- Absorbed from the former KBQ Catalog. Populate from applicable KBQ-* concepts. -->

| KBQ ID | Business Question | Decision Need | Impact Area | Resolution Status | Linked UC/KPI IDs | Evidence |
|---|---|---|---|---|---|---|

## 5B. Success Metrics, KPIs & Measurement Framework

<!-- Absorbed from the former KPI and Metric Definitions document. Includes BOTH
     KPIs (specific targets) AND general metrics (measurement definitions).
     Populate from applicable KPI-*/MET-* concepts. -->

### 5B.1 KPI Summary

| KPI ID | KPI Name | Formula / Calculation | Target / Threshold | Data Source | Refresh Frequency | Owner | Feasibility | Linked KBQ IDs | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|

### 5B.2 Operational Metrics

| Metric ID | Metric Name | Definition | Grain | Data Source | Calculation | Linked KPI IDs | Evidence |
|---|---|---|---|---|---|---|---|

### 5B.3 Measurement Framework

<!-- How KPIs and metrics will be measured, monitored, and reported. Include data
     quality requirements for the measurements themselves. -->

## 5C. Business Rules

<!-- Business rules inferred from inputs or provided by user.
     - Rules provided by user are marked [USER PROVIDED].
     - Rules inferred by the agent are marked [INFERRED]. Downstream agents treat
       inferred rules as references only, NOT ground truth.
     Populate from applicable BR-* concepts and their linked source evidence. -->

| Rule ID | Business Rule | Source | Type ([USER PROVIDED] / [INFERRED]) | Confidence | Linked BR/UC IDs |
|---|---|---|---|---|---|

## 6. Data Landscape

### 6.1 Source Inventory

| Source | Vendor/System | Data Type | Frequency | Priority | Owner | Evidence |
|---|---|---|---|---|---|---|

### 6.2 Relationships

| Entity/Source A | Relationship | Entity/Source B | Business Meaning | Evidence |
|---|---|---|---|---|

### 6.3 Data Quality

| DQ Area | Requirement/Expectation | Threshold | Severity | Evidence |
|---|---|---|---|---|

### 6.4 Retention

| Data Category | Retention Requirement | Archival/Deletion Rule | Compliance Driver | Evidence |
|---|---|---|---|---|

## 7. Success Measures

### 7.1 Success Criteria

| Criterion ID | Success Criterion | Measurement | Acceptance Threshold | Evidence |
|---|---|---|---|---|

### 7.2 Acceptance

| Acceptance Area | Reviewer/Owner | Acceptance Method | Required Evidence |
|---|---|---|---|

## 8. Assumptions and Constraints

### 8.1 Assumptions

| ID | Assumption | Rationale | Risk if False | Validation Needed |
|---|---|---|---|---|

### 8.2 Constraints

| ID | Constraint | Type | Impact | Evidence |
|---|---|---|---|---|

### 8.3 Risks

| Risk ID | Risk | Impact | Likelihood | Mitigation | Evidence |
|---|---|---|---|---|---|

### 8.4 Detected Contradictions

| Contradiction ID | Source A | Claim A | Source B | Claim B | Severity | Recommended Action |
|---|---|---|---|---|---|---|

### 8.5 Compliance Flags

| Flag ID | Category | Severity | Description | Recommended Action | Evidence |
|---|---|---|---|---|---|

## 9. Referenced Documents

| Document | Version/Date | Location | Relevance |
|---|---|---|---|

## 10. Terms and Definitions

| Term | Definition | Source |
|---|---|---|

## 11. Open Items

| ID | Section | Type | Description | Impact | Owner/Validation Needed |
|---|---|---|---|---|---|

## 12. Cross-Reference Traceability Summary

<!-- Summary view of traceability within this document. Full traceability is in
     outputs/03_evaluation/traceability.yaml after /evaluate-run. -->

| UC ID | KBQ IDs | KPI IDs | Metric IDs | BR IDs | Rule IDs |
|---|---|---|---|---|---|
