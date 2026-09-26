<!--
Template ID: FRD
Template role: Source-of-truth structure for the consolidated Functional Requirements Document.

This is the CONSOLIDATED FRD template. It absorbs the prior Data Requirements (DR)
deliverable as embedded Section 4. Stakeholders consume the FRD, not a separate DR document.

Generation rules:
- Preserve every heading in this template in the generated markdown.
- Replace guidance comments with evidence-backed content; do not copy comments into the final deliverable.
- Missing required evidence must appear inline as [INSUFFICIENT INPUT] and be repeated in "11. Open Items".
- Assumptions must appear inline as [ASSUMPTION] and be repeated in "11. Open Items".
- Requirements must be testable, stable-ID based, and traceable to UC, BRD, KBQ, KPI, and MET IDs where available.
- Use EARS-style phrasing for formal requirements unless the user declared an alternative style.

Embedded data section (Section 4) — generation rules:
- Section 4 is ALWAYS present in the template.
- If linked knowledge concepts contain FRD-applicable data requirements (DR-*), use them to populate Section 4.
- If no DR analysis was done, populate Section 4 with [INSUFFICIENT INPUT] noting what
  data evidence was missing. Do NOT omit the section.
- Reshape package-example layer subsections when linked knowledge establishes a
  different architecture. Record the evidence-backed reshape in Open Items.
-->

# Functional Requirements Document

## Cover Page

| Field | Value |
|---|---|
| Client |  |
| Project |  |
| Document | Functional Requirements Document |
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

## Table of Contents

<!-- Generate a fully clickable GFM TOC using standard GitHub Markdown heading slugs.
Two-level: top-level numbered sections as bullets (`-`), sub-sections indented two spaces.
Every line is an anchor link, never plain numbered text. The DOCX renderer replaces this block. -->

## 1. Executive Summary

<!-- Summarize functional scope, systems affected, requirement coverage, and the relationship to the BRD without duplicating later sections. -->

## 2. Scope and Boundaries

### 2.1 Functional Scope

| Capability | Description | Linked UC IDs | Included? | Evidence |
|---|---|---|---|---|

### 2.2 System Boundaries

| System/Boundary | In Scope/Out of Scope | Role | Evidence |
|---|---|---|---|

### 2.3 Integration Points

| Integration Point | Direction | Source/Target | Pattern/Frequency | Evidence |
|---|---|---|---|---|

### 2.4 Out of Scope

| Exclusion | Rationale | Evidence/Decision |
|---|---|---|

## 3. Functional Requirements by Capability

<!-- Repeat this capability block for every evidence-backed capability. -->

### 3.x Capability: <Capability Name>

#### Overview

#### Requirements Table

| FRD Req ID | Requirement | Priority | UC Ref | BRD Req Ref | Acceptance Criteria | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

#### Main Flow

| Step | Actor/System | Action | Expected Result | Evidence |
|---|---|---|---|---|

#### Exception Handling

| Exception | Trigger | Handling Requirement | User/System Response | Evidence |
|---|---|---|---|---|

#### Data Transformation Rules

| Rule ID | Input | Transformation/Derivation | Output | Evidence |
|---|---|---|---|---|

#### Validation Rules

| Rule ID | Validation | Severity | Failure Handling | Evidence |
|---|---|---|---|---|

## 4. Data Requirements

<!-- Absorbed from the former Data Requirements Document (DR). Contains the analytical
     depth previously in the standalone DR deliverable. Populate from applicable DR-* concepts. -->

### 4.1 Source Inventory

| Source ID | Source Name | Vendor/System | Data Type | Frequency | Format | Priority | Owner | Evidence |
|---|---|---|---|---|---|---|---|---|

### 4.2 Data Requirements by Layer

<!-- The subsections below are package examples. Rename or replace them when the
     linked knowledge establishes a different data or interface architecture,
     and record that evidence-backed adaptation in Open Items. -->

#### 4.2.1 Bronze / Raw Layer

| DR ID | Requirement | Source | Target Entity | DQ Rules | Retention | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

#### 4.2.2 Silver / Curated Layer

| DR ID | Requirement | Source Entity | Target Entity | Transformation | DQ Rules | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

#### 4.2.3 Gold / Mart Layer

| DR ID | Requirement | Source Entity | Target Entity | Business Logic | DQ Rules | Evidence | Confidence |
|---|---|---|---|---|---|---|---|

### 4.3 Data Quality Requirements

| DQ ID | Rule | Target Entity | Column(s) | Check Type | Threshold | Evidence |
|---|---|---|---|---|---|---|

### 4.4 Data Lineage Summary

<!-- High-level lineage from source to mart. Detailed lineage in traceability.yaml. -->

### 4.5 Privacy, Security & Compliance

| Requirement | Classification | Handling Rule | Regulation | Evidence |
|---|---|---|---|---|

### 4.6 Data Retention & Archival

| Data Category | Retention Period | Archival Strategy | Regulation | Evidence |
|---|---|---|---|---|

## 5. Non-Functional Requirements

| NFR ID | Category | Requirement | Target/Threshold | Priority | Evidence | Confidence |
|---|---|---|---|---|---|---|

## 6. Integration Requirements

### 6.1 Inbound Interfaces

| Interface ID | Source | Payload/Data | Frequency | Protocol/Format | Requirement | Evidence |
|---|---|---|---|---|---|---|

### 6.2 Outbound Interfaces

| Interface ID | Target | Payload/Data | Frequency | Protocol/Format | Requirement | Evidence |
|---|---|---|---|---|---|---|

### 6.3 Integration Level Definitions

| Level | Name | ETL/Processing Activity | DQ Gates | Evidence |
|---|---|---|---|---|

## 7. Traceability Matrix

| UC ID | BRD Req IDs | FRD Req IDs | KBQ IDs | KPI/Metric IDs | DR IDs |
|---|---|---|---|---|---|

## 8. Assumptions, Constraints, and Dependencies

| ID | Type | Description | Impact | Validation Needed | Evidence |
|---|---|---|---|---|---|

## 9. Terms and Definitions

| Term | Definition | Source |
|---|---|---|

## 10. Referenced Documents

| Document | Version/Date | Location | Relevance |
|---|---|---|---|

## 11. Open Items

| ID | Section | Type | Description | Impact | Owner/Validation Needed |
|---|---|---|---|---|---|
