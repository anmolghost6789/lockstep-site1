# Input Evaluation Report

**Generated** <UTC YYYY-MM-DD HH:MM>  ·  **Project** <name or "—">

<!--
Render this report per references/report_grammar.md (the input evaluation report
spine, §4). The grammar owns the verdict banner, status tokens, the 10-cell meter,
the callout skeleton, and the fixed section order. This template is the filled
skeleton; keep the section order and primitives exactly. The Requirements §1 module
is "selected-output readiness". Replace every <...> placeholder; delete rows/sections
that do not apply, but keep empty in-scope sections with an explicit "*None.*".
-->

> ## <✅ PASS | ⚠️ WARN | ⛔ ERROR> — <one-line decision, e.g. "ready to extract" / "proceed with assumptions" / "resolve blockers first">
> **Readiness** `<meter NN%>`  ·  **Selected** <BRD/FRD/URS/JIRA>  ·  **Inputs** <N files>  ·  <X blockers · Y major>
> <Why this verdict; no hedging or recap of sections below.>

---

## §1 · Can we deliver?

*Selected-output readiness — one row per selected deliverable only.*

| Output | Status | Required evidence present | Required evidence missing | Confidence |
|---|---|---|---|---|
| BRD | <✅ full / ◐ partial / ✕ not possible> | <key evidence found> | <gaps or "—"> | <high/med/low `meter`> |
| FRD | … | … | … | … |
| URS | … | … | … | … |
| JIRA | … | … | … | … |

## §2 · What we evaluated

**<N> input files**  ·  **Domain** <profile>  ·  **Jira** <project_key or "none">  ·  **Personas** <source>  ·  **Branding** <detected? y/n>  ·  **Compliance** <regimes or "—">

| Category | Files | Notes |
|---|---|---|
| Requirements / scope | <N> | <one line> |
| Context / standards | <N> | <one line> |
| Reference / supporting | <N> | <one line> |
| Branding / preferences | <N> | <one line> |

## §3 · Findings

| ID | Severity | Finding |
|---|---|---|
| BLK-001 | ⛔ blocker | <one line> |
| MAJ-001 | 🟠 major | <one line> |
| MIN-001 | 🟡 minor | <one line> |

<!-- Full callout for every blocker/critical/major, worst-first (grammar §3.5).
Minor/info stay as index rows above; their assumption (if any) goes in §5; append a
single "→ Fix:" line via <br> only when the fix is non-obvious. -->

> **[CRITICAL] <ID> — <short title>** · <affected scope>
> <Explain the finding and cite specifics; no hedging or duplicated detail.>
> **Evidence:** <source file · section · field>
> **→ Resolution:** <concrete action>

**Open questions**

| ID | Question | Blocking? | Applies to | Suggested owner |
|---|---|---|---|---|
| Q-001 | <question> | yes/no | <output/section> | <role> |

## §4 · Checks run

*Cross-document and compliance checks.*

| Check | Type | Result |
|---|---|---|
| Source contradictions | consistency | <✅ pass / ⚠️ flagged → ID> |
| Compliance flags (<regime>) | compliance | <✅ pass / ⚠️ flagged → ID / – n/a> |

## §5 · Assumptions if proceeding

| ID | Risk | Assumption |
|---|---|---|
| ASS-001 | <🟢 low / 🟡 medium / 🔴 high> | <assumption> |

## §6 · What to do next

1. <concrete imperative action>
2. <next action>

*Re-evaluation: ⛔ error → fix & re-run `/start-run` · ⚠️ warn → accept assumptions or fix · ✅ pass → proceed. Then `/extract-requirements`.*

---

## Appendix

### A1 · Canonical source inventory

[Open the Requirements Knowledge Index](../00_state/knowledge/index.md). Do not
copy its per-file source manifest into this report.

### A2 · Scoring rubric

| Dimension | Weight | Score | Basis | Evidence |
|---|---:|---:|---|---|
| Source coverage | | | | |
| Evidence quality | | | | |
| Requirement clarity | | | | |
| Traceability readiness | | | | |

### A3 · Detected signals

- **Domain profile:** <profile> — matched signals: <list>
- **Persona pool:** <source + list>
- **Branding:** <summary or "none detected">
