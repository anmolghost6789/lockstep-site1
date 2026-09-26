# Report Grammar — Evaluation Reports

Single source of truth for the **content format** of every evaluation report the data
agents produce: the **input evaluation report** (`/start-run`, `/start-build-run`,
`/evaluate-inputs`, Design Gate 1) and the **output evaluation report** (`/evaluate-run`,
`/evaluate-build`, Design 08 - Evaluate, Test `/generate-report`).

The section *headers* of these reports were already defined per agent. This file defines
the part that kept drifting run to run: **which visual primitive renders which kind of
content, in what order, at what depth.** Follow it literally. The same input produces the
same report shape every time.

This grammar is **identical across the Requirements, Build, Test, and Design packages**
(copied verbatim into each package's references). The Deploy agent is out of scope — it
produces a change manifest, not an evidence evaluation, and keeps its own
`02-presentation-style.md`.

> This is a formatting contract, not a content contract. It never tells you *what* to
> find or *how* to score — the agent's own evaluation rules own that. It tells you how to
> present what you found.

---

## 1. Rendering reality (why the palette is what it is)

These reports render in exactly two targets, both narrow. Author for the intersection.

**UI** — `react-markdown` + GFM (`playground/frontend/src/shared/ui/Markdown.tsx`). Raw HTML
is **stripped on purpose**. So: **no HTML, no Mermaid, no SVG, no embedded charts/images.**
GFM tables, task lists, emoji, and Unicode all render.

**DOCX export** — a custom line parser (`scripts/md_to_docx.py`), not a full markdown engine.
It supports: tables (styled header, zebra rows, repeating header across pages), headings
(page break before each H1), bullet/ordered lists, code blocks, horizontal rules, inline
`**bold**`/`*italic*`/`` `code` ``/links, `<br>` inside table cells — and, most usefully,
**blockquotes become colored callout boxes** whose color is keyed off a severity word in
the text (see §3.4).

**Hard don'ts** (they silently degrade in one target or the other):
- ❌ Raw HTML of any kind, including `<details>`/`<summary>` (UI may render it; DOCX flattens
  it to literal text). Use a plain `## Appendix` heading instead.
- ❌ Mermaid / fenced ` ```mermaid ` blocks — render as raw code in both targets.
- ❌ Images or HTML-based bars/badges.
- ❌ Nested tables, or tables whose cells contain block elements other than `<br>`.

Everything below is built only from primitives that survive **both** targets.

---

## 2. Detail policy — detailed, not verbose

The reports must stay **detailed**. The fix for "long wall of text" is **layering and
de-duplication**, never deletion. No substantive fact (input, finding, check, assumption,
evidence ref, score) is dropped relative to the prior reports. Canonical linked
inventories are not copied into a report: the link preserves access without
creating a second representation that can drift.

Three tiers, by reading need:

| Tier | What lives here | Form |
|---|---|---|
| **1 — Decision** | Verdict, readiness/score, "can we deliver?", findings index | Banner + meters + compact tables. Answers "do I proceed?" in ~10 seconds. |
| **2 — Evidence** | Every input, every check, every assumption; a full callout per **blocker/critical/major** finding | Tables + callouts. Same depth as the prior reports. |
| **3 — Appendix** | Supporting inventories not already canonical elsewhere (for example per-table scores) | Tables under a plain `## Appendix` heading, out of the decision path. |

**What you cut** is only: the same fact stated twice (prose paragraph *and* a table row),
filler sentences, and hedging ("hopefully", "should be", "it seems"). **What you keep** is
all of the evidence.

**Finding depth is gated by severity** (see §4.4):
- `blocker` / `critical` / `major` → **full callout** (skeleton in §3.5).
- `minor` / `info` → **one-line row** in the findings index; any assumption it implies goes
  in full into the Assumptions table; add a single `→ Fix:` line **only if the fix is
  non-obvious**. No four-part callout.

---

## 3. The visual lexicon

One primitive per kind of content. Do not substitute (this is the anti-drift rule):

| Content kind | Primitive | Never render as |
|---|---|---|
| Verdict / gate decision | Verdict banner callout (§3.3) | a heading, a sentence, a table cell |
| Any 0–100 score or % readiness | Meter (§3.2) | stars, "High/Med/Low" alone, raw number alone |
| Status of an item (output, input, check) | Status token (§3.1) | freeform adjectives |
| Any list/matrix (inputs, outputs, checks, assumptions, scores, inventory) | Table | prose, bullet lists |
| A blocker/critical/major finding | Callout (§3.5) | a table row, a paragraph |
| A minor/info finding | Index-table row (§4.4) | a callout |
| Step-by-step next actions | Ordered list (§4) | prose |

### 3.1 Status tokens (emoji **always** paired with a word)

DOCX may render color emoji as monochrome glyphs, so the **word** always carries the
meaning; the emoji is a scannable hint, never the sole signal. Use these exact tokens:

```
Verdict:        ✅ PASS    ⚠️ WARN    ⛔ ERROR
Output/sufficiency: ✅ full   ◐ partial   ✕ not possible
Presence:       ✅ present  △ partial   ✕ missing
Check result:   ✅ pass    ⚠️ flagged  – n/a
Confidence:     high · medium · low      (always next to a meter)
Risk:           🟢 low     🟡 medium    🔴 high
Severity:       ⛔ blocker  🔴 critical  🟠 major  🟡 minor  ⚪ info
```

Output-report verdicts reuse the verdict row vocabulary mapped to each agent's rule
(e.g. Build: `✅ PASS` / `⚠️ PASS WITH ACTIONS` / `⛔ FAIL`).

### 3.2 Meter — the only way to show a 0–100 value

Fixed **10-cell** Unicode bar, deterministic, **always followed by the exact number**:

- Cell = `█` (filled) or `░` (empty). `filled = round(value / 10)`.
- Always append the precise value so rounding never loses information:
  `` `█████████░ 90%` `` or `` `█████████░ 9/10` `` or `` `████████▊░ 88/100` ``.
- Wrap the meter in backticks so the monospace run keeps the cells aligned in both targets.
- Optional finer last cell (eighths `▏▎▍▌▋▊▉`) is allowed for cosmetics **only because the
  number follows** — the number, not the glyph, is authoritative.

Use a meter for: readiness %, overall score, per-dimension score (`/10`), per-table score,
coverage %, confidence (paired with the word). Never show a bare number where a meter belongs.

### 3.3 Verdict banner (top of every report)

A single blockquote callout, immediately after the metadata line. Exactly:

```markdown
> ## ⛔ ERROR — <one-line decision>
> **Readiness** `███░░░░░░░ 30%`  ·  **Complexity** HIGH  ·  <key counts>
> <Why this verdict, with no hedging or repeated detail.>
```

- Line 1: `## <verdict token> — <imperative decision>` (e.g. "proceed after 1 acknowledgement",
  "fix blockers before continuing", "ready to package").
- Line 2: the headline metrics for this agent — readiness/score meter + the 2–4 numbers that
  matter (blocker/critical/major counts; table/complexity for input, must-fix counts for output).
- Line 3: decision-relevant rationale without repeating the metrics.

Use the severity word that matches the verdict so the DOCX box colors correctly (§3.4):
ERROR/blocker banners contain `ERROR`/`blocker`; WARN banners contain `WARN`/`warning`.

### 3.4 Callout coloring (DOCX) — drive it with the keyword

`md_to_docx.py::_blockquote_palette` colors a blockquote box by scanning its text for a
keyword. Put the right tag in the callout's first line so the color matches the severity:

| Tag in first line | DOCX box color | Use for |
|---|---|---|
| `[BLOCKER]` (or word "blocker") | amber/orange | blocker findings, ERROR verdict |
| `[CRITICAL]` (or "critical") | red | critical findings |
| `[MAJOR]` | amber *(renderer extended to recognize this — see §7)* | major findings, WARN verdict |
| `[WARNING]` / "assumption" | yellow | assumptions, soft warnings |
| *(none of the above)* | slate | neutral notes, info |

In the UI all blockquotes render the same (a left rule); the color is a DOCX nicety. The
**word** in the tag is what the reader relies on either way.

### 3.5 Callout skeleton (blocker/critical/major findings)

Fixed four-part shape. This fixed skeleton is what stops finding-format from drifting:

```markdown
> **[SEVERITY] <ID> · <rule_id if any> — <short title>** · <affected scope>
> <Explain the fact and cite specifics; no hedging or duplicated detail.>
> **Evidence:** <source file · sheet/section · row/field>  ·  **Check:** <check_id if any>
> **→ Resolution:** <concrete action the user can take>
```

Order is fixed: title line → explanation → `Evidence:` line → `→ Resolution:` line. Omit the
`Check:` fragment only when no check applies; never omit Evidence or Resolution.

### 3.6 Tables

- GFM pipe tables only. Header row + separator row. Fixed column set per section (§4/§5).
- Right-align numeric columns (`---:`); left-align text.
- In-cell line breaks use `<br>` (supported by both targets). No other block markup in cells.
- Long inventories go in the Appendix, not inline.

---

## 4. Input evaluation report — the spine

Fixed section order. `§3` is the **agent module** (the one section that differs per agent).
Sections with no content for a given run still appear, with an explicit empty state
("*None.*"), so the shape is constant.

```
# Input Evaluation Report
<metadata line: Run · Generated · Project>

<verdict banner>                         ← §3.3

## §1 · Can we deliver?                  ← AGENT MODULE (see §6)
## §2 · What we evaluated                ← input inventory table + conformance
## §3 · Findings                         ← index table + callouts (§4.4)
## §4 · Checks run                       ← semantic/quality checks table (where applicable)
## §5 · Assumptions if proceeding        ← risk-rated table
## §6 · What to do next                  ← ordered actions + re-eval loop line
## Appendix                              ← supporting detail and canonical inventory links
```

Metadata line (single line, no table):
`**Generated** <UTC, YYYY-MM-DD HH:MM>  ·  **Project** <name>`

### §2 column set (input inventory)
`| Category | Files | Notes |` for the grouped view. Link the canonical Requirements
Knowledge Index in the Appendix instead of copying the per-file manifest.
Conformance is shown as a one-line token row above the table.

### §4.4 Findings
A severity-grouped **index table** first:

```markdown
| ID | Severity | Finding |
|---|---|---|
| BLK-001 | ⛔ blocker | <one line> |
| MAJ-001 | 🟠 major | <one line> |
| MIN-001 | 🟡 minor | <one line> |
```

Then a **callout (§3.5) for every blocker/critical/major row, worst-first**. Minor/info get
no callout (their assumption, if any, appears in §5; a non-obvious fix gets one `→ Fix:` line
appended to their index row via `<br>`). Empty severities are omitted from the index.

### §5 column set
`| ID | Risk | Assumption |` — risk uses the 🟢/🟡/🔴 token. Every assumption implied by any
finding (including minors) appears here in full.

### §6
Numbered, concrete, imperative. End with the one-line re-eval loop:
`*Re-evaluation: ⛔ error → fix & re-run · ⚠️ warn → accept assumptions or fix · ✅ pass → proceed. Max 3 cycles.*`

---

## 5. Output evaluation report — the spine

Same lexicon, parallel spine. A **pre-score disclosure module** slot (`§1`) accommodates
agents (e.g. Build) whose rules require input-quality disclosure *before* scores.

```
# <Agent> Evaluation Report
<metadata line: Run · Evaluated · Project>

<verdict banner with overall-score meter>   ← §3.3

## §1 · Input quality                        ← PRE-SCORE MODULE (callout/table; required by Build, optional elsewhere)
## §2 · Scorecard                            ← dimension table with score meters + overall row
## §3 · Coverage & traceability              ← AGENT MODULE (see §6)
## §4 · Defects                              ← index table + callouts (same rule as §4.4)
## §5 · What to do next                      ← remediation grouped by class, ordered
## Appendix                                  ← per-item detail (per-table scores worst-first, etc.)
```

### §2 Scorecard column set
`| Dimension | Weight | Score | |` — Score column is a `/10` meter; final `|` column carries
the status token. Last row is the bold **Overall** with the `/100` meter and the verdict token.
Dynamic/conditional dimensions listed as a one-line token row beneath the table.

### §4 Defects
Same two-tier rule as §4.4. Defect classes use the agent's vocabulary mapped to severity
tokens (Build: `blocker` → ⛔, `must_fix` → 🔴, `should_fix` → 🟡). Full callout for
blocker/must-fix; index row for should-fix.

### §5 Remediation
Grouped by class (blockers first), numbered within each group, each item a concrete action.
End with the one-line gate rule:
`*Gate: ✅ pass → <next> · ⚠️ pass-with-actions → fix must-fix or accept risk · ⛔ fail → revise. <packaging/proceed condition>.*`

---

## 6. The agent module (`§3`) — what each package defines

Everything above is shared verbatim. Each agent defines **only** its `§3` matrix — the
"can we deliver?" view for input, and the "coverage" view for output — in its own report
spec, using the lexicon above. The module declares its **columns** and its **status
vocabulary**; nothing else varies.

| Agent | Input `§1 · Can we deliver?` | Output `§3 · Coverage` |
|---|---|---|
| Requirements | Selected-output readiness per BRD/FRD/URS/JIRA (`Output · Status · Required evidence present/missing · Confidence`) | Requirement → evidence traceability coverage |
| Build | Producible-outputs matrix (`DDL/DML/DQ/Pipeline/Tests · Status · Confidence · Basis`) | Per-table coverage; lineage consistency |
| Test | Testability matrix (`Business rule · Status · Confidence · Missing inputs · Expected test categories`) | Test coverage by rule/table |
| Design | Confidence by context tier + critical-element readiness (grain/PK/KPI/join) | KPI/KBQ/business-rule coverage |

A module spec must state: section title, column headers (in order), which columns use a
meter vs. a status token, and the agent's status vocabulary mapped to the §3.1 tokens.

---

## 7. Renderer change this grammar assumes

`md_to_docx.py::_blockquote_palette` currently recognizes `[blocker]`, `[critical]`,
`[warning]`, and `assumption`. To color **major** callouts distinctly (amber) and keep
**minor/info** neutral, extend it to also recognize `[major]` (→ amber, reuse the
warning/yellow or blocker/amber palette) and treat `[minor]`/`[info]` as neutral (slate).
This is additive — it does not change coloring for existing deliverables (BRD/FRD/URS),
which don't use those tags. Until that change ships, major callouts render slate in DOCX
(the word `[MAJOR]` still carries the meaning); the UI is unaffected.

---

## 8. Authoring checklist (run before emitting any report)

- [ ] Verdict banner present, immediately after the metadata line, with a meter and the
      matching severity word.
- [ ] Every 0–100 value is a 10-cell meter followed by its exact number — no bare numbers,
      no stars, no lone "High/Med/Low".
- [ ] Every list/matrix is a table with the section's fixed columns. No prose lists of facts.
- [ ] Every blocker/critical/major finding is a full §3.5 callout, worst-first; minor/info
      are index rows only (+ assumption in §5, + one `→ Fix:` line if non-obvious).
- [ ] Every emoji is paired with its word token.
- [ ] No raw HTML, no `<details>`, no Mermaid, no images.
- [ ] Exhaustive inventories are in `## Appendix`, not in the decision path.
- [ ] Sections appear in the fixed spine order; empty sections show an explicit empty state.
- [ ] No fact from the agent's evaluation is missing — detail is layered, not dropped.
```
