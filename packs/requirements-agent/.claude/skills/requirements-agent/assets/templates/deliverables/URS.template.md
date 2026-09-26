<!--
Template ID: URS
Template role: Source-of-truth structure for User Requirements Specification output.

Default alignment: a general professional URS structure with optional
regulatory, risk, and qualification sections. Populate specialized governance
only when linked evidence or the selected run-local template requires it.

Generation rules:
- Preserve every heading in this template in the generated markdown.
- URS captures user/stakeholder needs and required outcomes. It must not drift
  into solution design unless the source explicitly states a constraint.
- Every URS requirement must be atomic, uniquely identified, verifiable, and
  traceable to evidence and upstream/downstream artifacts where available.
- Missing evidence appears inline as [INSUFFICIENT INPUT] and is repeated in
  "18. Open Items".
- Reasonable assumptions appear inline as [ASSUMPTION] and are repeated in
  "18. Open Items".
- Regulatory, risk, criticality, and verification fields follow linked evidence.
  Never infer a regime or qualification method from industry keywords alone.
- URS links BRD/UC/KBQ/KPI/DR evidence to FRD-ready functional detail.
-->

# User Requirements Specification

## Cover Page

| Field | Value |
|---|---|
| Client |  |
| Project |  |
| Document | User Requirements Specification |
| Document ID |  |
| Version |  |
| Date |  |
| Domain / Operating Context |  |
| Confidentiality |  |

## Document Control

### Revision History

| Version | Date | Author | Changes | Approval Status |
|---|---|---|---|---|

### Approval and Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|
| Business Owner |  |  |  |
| Technical Owner |  |  |  |
| Quality / Compliance |  |  |  |
| Project Manager |  |  |  |

### Distribution List

| Name / Group | Role | Purpose |
|---|---|---|

## Table of Contents

<!-- Generate a fully clickable GFM TOC using standard GitHub Markdown heading slugs.
Two-level: top-level numbered sections as bullets (`-`), sub-sections indented two spaces.
Every line is an anchor link, never plain numbered text. The DOCX renderer replaces this block. -->

## 1. Purpose and Scope

### 1.1 Purpose

State why this URS exists, what decisions it informs, and which lifecycle stage it supports (concept, design qualification, validation, change control).

### 1.2 Scope of the URS

Define the system or capability boundaries: what the URS covers and what it explicitly does not. Cite governing evidence when regulation shapes scope.

### 1.3 Out of Scope

List capabilities, interfaces, or processes that look in scope but are explicitly excluded, with rationale.

### 1.4 Relationship to Other Artifacts

| Artifact | Relationship to URS | Generated / Expected Path |
|---|---|---|
| BRD | Business objectives and business requirements feed user needs. |  |
| UC | Use cases provide user interactions and outcomes. |  |
| KBQ | Business questions clarify decision needs. |  |
| KPI | Metrics define measurable user/business outcomes. |  |
| DR | Data requirements constrain data availability and quality. |  |
| FRD | FRD derives functional requirements from approved URS requirements. |  |
| Jira Stories | Stories decompose approved URS/FRD needs into delivery work. |  |
| Test / Qualification | URS acceptance intent drives FAT/SAT and IQ/OQ/PQ where applicable. |  |

## 2. System Overview and Intended Use

### 2.1 System Description

Plain-language description of the system or capability. Cite the source documents that established this view and avoid repeating later sections.

### 2.2 Intended Use and User Benefits

Identify the primary intended use, the user benefits, and the business outcomes the system enables.

### 2.3 Operating Environment

| Aspect | Description | Evidence |
|---|---|---|
| Deployment context (cloud / on-prem / hybrid) |  |  |
| Integration landscape (upstream / downstream systems) |  |  |
| User access channels (web / mobile / API / batch) |  |  |
| Geographic scope and jurisdictions |  |  |
| Operating hours and availability window |  |  |

### 2.4 Constraints from Intended Use

Constraints that arise from how the system is intended to be used (regulatory category of the workload, peak load expectations, data-residency expectations, language/locale, accessibility floor).

## 3. Source Corpus and Evidence Basis

| Source ID | Source Path | Source Type | Evidence Role | Read Status | Authority | Notes |
|---|---|---|---|---|---|---|

Read `.claude/skills/requirements-agent/references/input_model.md` for source-role and authority definitions. Read `.claude/skills/requirements-agent/references/traceability.md` for citation format per source type (line numbers for `.md/.txt/.csv`, section + paragraph for `.docx`, page + paragraph for `.pdf`, sheet + cell for `.xlsx`, JSON Pointer for `.json/.yaml`).

## 4. Business and User Context

### 4.1 Business Objectives

| Objective ID | Objective | Linked BRD Req IDs | Evidence | Confidence |
|---|---|---|---|---|

### 4.2 User Groups, Personas, and Stakeholders

Use actors and user groups established in linked knowledge. When evidence does
not establish them, record the gap rather than inserting a default persona pool.

| Persona / User Group ID | Name | Description | Primary Goals | Pain Points | Access Level | Evidence |
|---|---|---|---|---|---|---|

Business-stakeholder consumer roles that surface from evidence but are NOT part of the configured persona pool (e.g. report consumers, downstream operations roles named in BRD Section 3) belong in Section 5 User Needs Summary as the `User / Persona` of the relevant need — NOT as new rows here.

### 4.3 User Roles and Responsibilities

System-access roles for the system being built: who can do what once the system is operational. Distinct from the delivery persona pool in Section 4.2.

| Role ID | Role | Responsibilities | System Privileges | Linked Persona IDs | Evidence |
|---|---|---|---|---|---|

## 5. User Needs Summary

| Need ID | User / Persona | Need Statement | Business Value | Priority | Evidence | Confidence |
|---|---|---|---|---|---|---|

User needs are the "why." User Requirements in Section 6 are the "what." Keep this section short and intent-focused.

## 6. User Requirements

Subsections 6.x repeat by capability or user journey. Every row is one atomic requirement.

### 6.x Capability or User Journey: \<Name\>

| URS ID | User Requirement | User / Persona | Priority | GMP / Regulatory Criticality | Rationale | Verification Intent | Verification Method | Linked UC IDs | Linked BRD Req IDs | Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|

Column rules:

- **URS ID** — stable identifier (`URS-001`, `URS-AN-001`, `URS-DATA-001`).
- **Priority** — Must / Should / Could / Won't (MoSCoW), or High / Medium / Low.
- **GMP / Regulatory Criticality** — High / Medium / Low / N/A when the governing evidence defines such a scheme; otherwise use N/A and explain the evidence gap once.
- **Verification Intent** — short prose: how a reviewer would know the requirement is met.
- **Verification Method** — enumerated value: `FAT` (Factory Acceptance Test) / `SAT` (Site Acceptance Test) / `IQ` (Installation Qualification) / `OQ` (Operational Qualification) / `PQ` (Performance Qualification) / `UAT` (User Acceptance Test) / `Inspection` / `Review` / `Demo` / `Data Validation` / `Signoff`. Choose the most rigorous applicable method given the profile. Non-regulated runs typically use `Review`, `Demo`, `UAT`, or `Inspection`.
- **Evidence** — source pointer in the format from `traceability.md`.
- **Confidence** — High / Medium / Low per `evidence_rules.md`.

## 7. Data and Information Requirements from User Perspective

| URS Data Req ID | User Information Need | Data / Metric Needed | Freshness / Grain | Quality Expectation | Linked KPI / DR IDs | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

## 8. Reporting, Analytics, and Decision Requirements

| URS Analytics Req ID | Decision or Question | Expected Output | Linked KBQ IDs | Linked KPI IDs | User Group | Evidence |
|---|---|---|---|---|---|---|

## 9. Non-Functional User Requirements

| NFR ID | Quality Attribute | User Requirement | Measurement / Threshold | Verification Intent | Verification Method | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

Consider only quality attributes supported by scope or governing evidence, such as performance, availability, security, usability, accessibility, maintainability, observability, interoperability, portability, or recoverability.

## 10. Regulatory and Compliance Requirements

Populate only evidence-backed compliance obligations. Each row must cite the
governing regulation, standard, policy, or contract and its useful locator. If
none is evidenced, state that no applicable obligation was identified; do not
invent a regulation or synthetic requirement ID.

| Reg ID | Regulation / Standard | Article / Section | User-Facing Requirement | Applicability Scope | Verification Method | Linked URS IDs | Evidence | Status |
|---|---|---|---|---|---|---|---|---|

## 11. Constraints and Governing Conditions

| Constraint ID | Constraint | Type (regulatory / business / technical / contractual) | Impacted User Requirements | Source / Evidence | Resolution Status |
|---|---|---|---|---|---|

## 12. Risk and Criticality Assessment

Risk-based qualification approach per GAMP-5. Each row groups URS requirements by criticality and names the qualification activities allocated to that group. For non-regulated runs this section is brief — focus on user-impact risks instead of qualification scope.

| Risk / Criticality Group | URS IDs in Group | Risk Description | Likelihood | Impact | Mitigation / Qualification Approach | Owner |
|---|---|---|---|---|---|---|

Where evidence requires qualification activities, name the applicable methods
and source. Otherwise use ordinary user-impact risk and verification language.

## 13. Acceptance and Verification Intent

Per-requirement acceptance intent and the method that will satisfy it. This is the bridge to test design (FRD acceptance criteria → test cases) and to qualification (IQ/OQ/PQ for regulated systems).

| URS ID | Acceptance Intent | Verification Method | Evidence Needed | Linked FRD / Test / Jira IDs | Stage (FAT / SAT / IQ / OQ / PQ / UAT) |
|---|---|---|---|---|---|

## 14. Traceability Matrix

| Source ID | BRD Req ID | UC ID | KBQ ID | KPI / Metric ID | DR ID | URS ID | FRD Req ID | Jira Story ID | Test Case ID | Status |
|---|---|---|---|---|---|---|---|---|---|---|

`Status` values: `complete` (all expected links present) / `partial` (some links missing — open item) / `dirty` (an upstream entity changed since this row was written).

## 15. Assumptions and Gaps

| ID | Type (assumption / gap / dependency) | Description | Impact | Owner / Validation Needed | Status |
|---|---|---|---|---|---|

Section 12 covers qualification-scoped risk. This section captures project-level uncertainty: unconfirmed assumptions, missing evidence the user has been asked to provide, and external dependencies that could change scope.

## 16. References

External standards, internal SOPs, and regulatory documents that govern this URS. Cross-deliverable links inside this run belong in Section 1.4, not here.

| Ref ID | Title | Issuer | Version / Date | Relevance to This URS |
|---|---|---|---|---|

List only references actually cited by linked evidence or the selected template.

## 17. Glossary and Appendices

### 17.1 Glossary

| Term / Acronym | Definition |
|---|---|

Populate with project-, domain-, and acronym-level terms used in this URS. Terms discovered during input classification should appear here.

### 17.2 Diagrams and Mockups

Reference path or embed image references for context diagrams, user-journey flows, wireframes/mockups, or system-architecture views supplied by the user.

### 17.3 Other Appendices

Additional additional material referenced from the body (e.g., risk-assessment worksheet, persona research, accessibility checklist).

## 18. Open Items

| Open Item ID | Section | Type ([INSUFFICIENT INPUT] / [ASSUMPTION] / [INFERRED FROM DOMAIN KNOWLEDGE] / contradiction / decision-needed) | Description | Impact | Owner / Validation Needed | Recommended Action |
|---|---|---|---|---|---|---|

Every inline marker in Sections 1–17 must have a matching row here. Markers without ledger rows are invalid and must be remediated before sign-off. See `references/evidence_rules.md` for the decision rule between marker types.
