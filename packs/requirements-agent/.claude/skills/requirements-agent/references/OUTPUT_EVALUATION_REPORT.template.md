# <Agent> Evaluation Report

**Evaluated** <UTC YYYY-MM-DD HH:MM>  ·  **Project** <name or "—">

<!--
Render per references/report_grammar.md (output evaluation report spine, §5). The
grammar owns the verdict banner, status tokens, the 10-cell meter, the callout
skeleton, and the fixed section order — don't restate the lexicon here. This is the
filled skeleton: keep the section order and primitives, replace every <...>, and
delete rows that don't apply (keep in-scope-but-empty sections with "*None.*").

Readability first, no duplication:
- State each fact ONCE — a table row OR a sentence, never both.
- No executive-summary paragraph. The banner's one-liner is the summary.
- Prefer a meter or a status token over a sentence when it says the same thing.
- §2 dimensions and the §3 module are agent-specific (see grammar §6); the shape stays fixed.
- Requirements-specific: §2 and §3 group rows under the three lenses defined in
  references/quality_checks.md (input → output fidelity, output sufficiency,
  best-practice / standards conformance) using a bold, blank-score group-header
  row. This is additive to the grammar's fixed columns, not a schema change.
-->

> ## <✅ PASS | ⚠️ PASS WITH ACTIONS | ⛔ FAIL> — <one-line decision, e.g. "ready to package" / "fix must-fix items first">
> **Overall** `<meter NN/100>`  ·  **Scope** <what was scored>  ·  <X blockers · Y must-fix>
> <Why this verdict. No hedging or recap of the sections below.>

---

## §1 · Input quality

*Any input-quality caveat that bounds the scores below. Required for Build; optional elsewhere.*

<one-line note or a single callout — or "*None.*">

## §2 · Scorecard

*One row per dimension, grouped under its lens (quality_checks.md). Score is a `/10` meter;
the last column is the status token. Bold **Overall** closes it. Add a `Basis` column giving
the one-line reason each score isn't higher/lower — this is the score's explanation, not a
duplicate of the Defects section.*

| Dimension | Weight | Score | | Basis |
|---|---:|---|---|---|
| **Lens: Input → output fidelity** | | | | |
| <dimension> | <w> | `<meter n/10>` | <✅/⚠️/⛔> | <why this score> |
| … | … | … | … | … |
| **Lens: Output sufficiency** | | | | |
| <dimension> | <w> | `<meter n/10>` | <✅/⚠️/⛔> | <why this score> |
| … | … | … | … | … |
| **Lens: Best-practice / standards conformance** | | | | |
| <dimension> | <w> | `<meter n/10>` | <✅/⚠️/⛔> | <why this score> |
| **Overall** | | `<meter NN/100>` | <verdict token> | <weighted-average basis + why the gate landed here> |

<Any conditional / dynamic dimensions as a single token row under the applicable lens — otherwise omit this line.>

## §3 · Coverage & traceability

*The agent's §3 module (grammar §6). One coverage row per lens, as meters, then the
traceability mapping. Call out anything below 80%.*

| Coverage dimension | Lens | Covered |
|---|---|---|
| <source → deliverable chain coverage> | Input → output fidelity | `<meter NN%>` |
| <deliverable self-sufficiency: structure, clarity, consistency read alone> | Output sufficiency | `<meter NN%>` |
| <standards/guidance concepts applied as captured> | Best-practice / standards conformance | `<meter NN%>` |

| Reference | Linked items | Status |
|---|---|---|
| <source · id> | <ids> | <✅/⚠️/⛔> |

## §4 · Defects

*Index table first. Then a full callout only for each blocker / must-fix, worst-first. Should-fix stays an index row.*

| ID | Severity | Defect |
|---|---|---|
| <ID> | ⛔ blocker / 🔴 must-fix / 🟡 should-fix | <one line> |

> **[<SEVERITY>] <ID> — <short title>** · <affected scope>
> <What's wrong, actual vs expected. No hedging or duplicated detail.>
> **Evidence:** <file · section / id>
> **→ Resolution:** <concrete action>

## §5 · What to do next

*Grouped by class (blockers first), numbered within each group. Close with the gate line.*

1. <concrete imperative action>
2. <next action>

*Gate: ✅ pass → <next step> · ⚠️ pass-with-actions → fix must-fix or accept risk · ⛔ fail → revise & re-run. <packaging / proceed condition>.*

---

## Appendix

*Detail only — nothing here is needed to read the verdict. Per-item scores worst-first, the full traceability matrix, raw SQL / queries, and cross-cycle detail live here.*
