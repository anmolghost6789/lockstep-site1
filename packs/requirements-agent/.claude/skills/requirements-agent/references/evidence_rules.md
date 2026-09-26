# Evidence Rules

Consolidated reference for inline markers, confidence levels, and ambiguity discipline. Applies to every generation and evaluation task.

## Table of contents

1. The three inline markers (`[INSUFFICIENT INPUT]`, `[ASSUMPTION]`, `[INFERRED FROM DOMAIN KNOWLEDGE]`)
2. Confidence scale
3. Ambiguity terms
4. Open Items ledger
5. Anti-patterns

---

## 1. Inline markers

The agent has three inline markers for missing or weakly-supported content. Use exactly one. Every row carrying a marker MUST have a matching entry in the deliverable's Open Items section.

### Decision rule

```
Is there ANY user-supplied evidence in inputs/ or context/ for this claim?
├── No, and a safe industry default exists                → [ASSUMPTION]
├── No, and the answer requires user/business judgement   → [INSUFFICIENT INPUT]
├── No, but domain knowledge (regulation / common pattern)
│      supports a reasonable answer                       → [INFERRED FROM DOMAIN KNOWLEDGE]
└── Yes (any pointer in inputs/ or context/)              → Do NOT use a marker.
                                                            Cite the evidence and set confidence.
```

### `[INSUFFICIENT INPUT]`

Use when the deliverable cannot be completed without explicit user/business input AND no safe assumption can be made.

Examples: Jira project key, business thresholds, SLAs, retention windows, owner names, escalation paths, join keys, filter criteria, aggregation rules.

```markdown
[INSUFFICIENT INPUT] <specific missing detail and what content the user should provide>.
```

**Never demand a specific filename.** Describe the content needed — the agent discovers files by content scan, not by name.

### `[ASSUMPTION]`

Use when a safe, widely-accepted industry default exists and you apply it pending user validation. Must pass the "senior-engineer reasonable" test.

Examples: SCD Type 2 for SCDs when no policy supplied, OAuth 2.0 authorization-code flow, 99.9% internal-API SLO, ISO-8601 timestamps.

```markdown
[ASSUMPTION] <assumption>. Confidence: <Low|Medium>. Validation needed from <role/source>. Risk if wrong: <impact>.
```

### `[INFERRED FROM DOMAIN KNOWLEDGE]`

Use when there is no user evidence, but a regulation, compliance regime, or domain convention dictates the answer. Cite the source.

Examples: "PCI-DSS requires PAN encrypted at rest" (PCI-DSS §3.5), "HIPAA Safe Harbor requires date-of-service below year-level granularity" (45 CFR §164.514), "GDPR Art. 6 requires named lawful basis".

```markdown
[INFERRED FROM DOMAIN KNOWLEDGE] <claim>. Source: <regulation/standard>. Confidence: Low. Validation needed from <subject-matter expert>.
```

---

## 2. Confidence scale

Every generated requirement, KBQ, KPI, data requirement, URS row, FRD row, and Jira story carries a `confidence` value.

| Level | Definition | Required basis |
|---|---|---|
| **High** | Explicitly stated in an authoritative source, OR corroborated by two or more independent primary sources. | A quote/section pointer from `primary_scope`, `primary_data_contract`, or `run_instruction`; OR two consistent quotes from any primary roles. |
| **Medium** | Explicitly stated in a single transcript / additional document / stakeholder note, OR a clean synthesis where no source disagrees. | One quote/pointer from `primary_transcript` or `additional_document` (when promoted by run instructions); OR a documented synthesis. |
| **Low** | Reasonable inference, supported by incomplete evidence, or grounded only in reference/context material. Low entries MUST set `assumption_flag: true`. | At minimum, a `reference_context` pointer OR an explicit `[ASSUMPTION]` note. |

### Mapping to numeric scoring

- Single independent source → cap at **65%** (Medium).
- Two independent sources → cap at **80%**.
- Three+ independent sources → up to **95%** (High).
- Any entity touched by an unresolved contradiction → cap at **60%**.

### Authoring rules

- Never write `Confidence: TBD`. If a level cannot be assigned, the row is `[INSUFFICIENT INPUT]` and removed from the body until evidence arrives.
- Never inflate confidence. A weak source with one quote is Medium at most.
- A confidence value without `evidence_refs` is invalid.

---

## 3. Ambiguity terms

Review checklist, not a blind blocker.

| Category | Examples |
|---|---|
| Vague quality | robust, scalable, seamless, intuitive, user-friendly, flexible |
| Vague speed | fast, quickly, promptly, near real-time, timely |
| Vague quantity | several, many, sufficient, appropriate, adequate, minimal |
| Optionality | may, might, should, could, as needed, where possible |
| Undefined comparison | better, improved, optimized, high quality |
| Undefined ownership | stakeholders, users, admins, business, operations |

### Review rule

Flag ambiguity only when it appears in generated requirement prose, acceptance criteria, assumptions, or open items.

Do NOT penalize:

- Direct evidence quotes copied from source documents.
- MoSCoW labels or priority names used as labels.
- Narrative executive summaries.
- Identifier strings such as `BR-001-01`.
- Open questions that intentionally preserve user wording.

For every real ambiguity finding: either rewrite the statement to be measurable, OR add an open item explaining what must be clarified.

---

## 4. Open Items ledger

Every inline marker has exactly one Open Items row with:

- Marker type (`[INSUFFICIENT INPUT]` / `[ASSUMPTION]` / `[INFERRED FROM DOMAIN KNOWLEDGE]` / contradiction / decision-needed)
- Section or claim reference
- Validating role/source needed
- Risk if the marker is not resolved
- Recommended action (describe content needed, NEVER a specific filename)

---

## 5. Anti-patterns

- Mixing two marker types in one statement.
- Writing `[ASSUMPTION]` for a business-specific claim — use `[INSUFFICIENT INPUT]` instead.
- Writing `[INSUFFICIENT INPUT]` and then silently filling in a guess on the same line.
- Demanding a specific filename in the resolution hint.
- Omitting the Open Items row.
- Inflating confidence beyond the source-count cap.
- Using ambiguous quality / speed / quantity terms in formal requirements without resolution.

---

## 6. Source requirement IDs

`/extract-requirements` preserves pre-existing client requirement IDs directly
in linked first-class concept files. These IDs take precedence over agent-generated IDs in
every downstream deliverable. Do not create a duplicate registry file.

### What to look for

Pattern families (anchored by source-document context):

- Generic shapes: `FRS-*`, `URS-*`, `REQ-*`, `FR-*`, `NFR-*`, `R-*-*`
- Site / system / domain-prefixed shapes the source documents use locally (e.g. `<DOMAIN>-*-*`, `<SYSTEM>SCHED-*`)
- Any alphanumeric ID that appears immediately next to requirement-shaped prose in source documents (`shall`, `must`, `should`)
- IDs that user instructions explicitly flag as mandatory traceability anchors

### Confirmation status

For each discovered ID, classify against transcripts / acceptance notes:

- `confirmed` — explicitly accepted by the client in a transcript or formal acceptance note (cite source + date).
- `proposed` — appears in a source document but no confirmation found.
- `mandatory_from_instructions` — user instructions name the ID as mandatory.

### Graph representation

Record the ID, exact source-page link and anchor, and confirmation status in the
requirement concept. If no client IDs exist in a greenfield project, use
stable agent IDs for graph traversal and the documented new-requirements marker
in Jira stories.

**Never invent fake source IDs.** Validation checks source-page links and final
traceability against the graph. When the graph contains no client IDs, Jira
stories carry `Source Requirements: N/A — new requirements`.
