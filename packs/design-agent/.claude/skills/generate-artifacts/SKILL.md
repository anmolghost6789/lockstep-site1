---
name: generate-artifacts
description: >-
  Generate the STTM, Data Model, DQ, and ER Diagram Excel artifacts for the planned design.
argument-hint: "[optional context]"
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(cat:*)
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(grep:*)
  - Bash(mkdir:*)
  - Bash(cp:*)
  - Bash(mv:*)
  - Bash(rm:*)
  - Bash(python:*)
  - Bash(python3:*)
  - Bash(py:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# Generate Artifacts

Purpose: generate STTM, Data Model, DQ, and ER Diagram workbooks from the approved design and execution plan.

This phase optimizes for wall-clock time and consistency. Two variability sources have historically made this phase swing from 40 to 80 minutes: (a) sequential per-layer writers with cold-start each time, and (b) per-layer regeneration of runtime scripts. The rules below eliminate both: **the writer is a shipped, canonical Python script — nobody writes a generator during the run.**

## Required Reads
- CLAUDE.md
- config/project_config.json
- .claude/skills/design-agent/SKILL.md
- outputs/00_state/run_state.json when continuing an existing run

## Rules
- Run only this phase.
- Stop at the phase boundary and return control to the user.
- Do not auto-invoke the next slash skill, even if the user previously asked to do everything.
- Update outputs/00_state/run_state.json and root progress.json at most twice per phase: once at phase start and once at phase completion (fold human-wait status into those two writes). The phase-completion rewrite of root progress.json is MANDATORY before the final reply of the phase. See CLAUDE.md principle 14.
- Keep chat concise; summarize and link to files rather than pasting report or artifact bodies.

## Steps

1. Verify the active output folder is `outputs/05_artifacts/` and matches the `file_plan` block of `outputs/00_state/execution_plan/plan.json`. Per-layer workbooks must be written under `outputs/05_artifacts/{layer}/`.
2. If unexpected files exist there, stop and ask before removing or overwriting.
3. **Run the shipped canonical generator.** Do NOT write a new Excel generation script (not inline, not in `runtime_scratch/`, not via a subagent). The package ships the writer at `.claude/skills/design-agent/scripts/generate_workbooks.py`; it consumes `outputs/00_state/design/column_mappings.json` (columns plus the per-layer/per-table metadata blocks) and `outputs/00_state/design/dq_rules_design.json` — the rendered `target_model_design.md` is never read — and is deterministic:

   ```
   python .claude/skills/design-agent/scripts/generate_workbooks.py \
     --layer all \
     --design-dir outputs/00_state/design \
     --out-root outputs/05_artifacts \
     --templates-dir .claude/skills/design-agent/templates/workbooks
   ```

   `--layer all` generates every layer in one invocation (per-layer workbooks + `ER_DIAGRAM.xlsx` + the two Mermaid markdown flavors). To regenerate a single layer on resume, pass `--layer L0` etc. Dependencies are in `.claude/skills/design-agent/scripts/requirements.txt` (`pip install -r` it once if `openpyxl` is missing).
4. The shipped generator already enforces the template contract; know it so you can diagnose failures:
   - It loads canonical templates via `load_workbook()` on `templates/workbooks/{TYPE}_TEMPLATE.xlsx`. Each STTM/DATA_MODEL/DQ template ships with exactly two sheets: `table_tracker` (index) and `_template_reference` (structural blueprint).
   - For each current-run table it copies the `_template_reference` sheet, renames the copy to the actual table name, and populates its cells with this run's values. Formatting (the default single-blue header theme) comes from the template copy — the script hardcodes no palette.
   - It rewrites the `table_tracker` sheet: row 1 headers kept (`S. No. | Table Name | Comments`), one body row per current-run table.
   - It deletes the `_template_reference` sheet before `workbook.save()` and fails fatally if any saved sheet starts with `_` or is not a planned table.
   - The ER_DIAGRAM template is different: its non-`table_tracker` sheets (`lineage_overview`, `table_relationships`, `layer_diagram_data`) are role-named structural sheets used as-is and never deleted; `ER_DIAGRAM.xlsx` covers ALL layers.
5. Because the writing is pure Python, run this phase inline by default. Spawn `artifact-writer` only when the run has more than 15 target tables AND generation demonstrably needs supervision per layer (script patch-and-rerun loops); even then the subagent INVOKES the shipped script — it never writes its own.
6. STTM `Filter Conditions` and `Join Conditions` come from `outputs/00_state/design/column_mappings.json`. Blank cells are not allowed for populated rows; the generator writes `-` when no filter or join applies.
7. DQ `DQ Rule Expression` comes from `outputs/00_state/design/dq_rules_design.json`. Blank is not allowed; custom rules use `[NEEDS_HUMAN_REVIEW]` with a reason in Comments. See "DQ expression cells are bare predicates" below.
8. Per-layer ER diagram markdown files (`outputs/05_artifacts/{layer}/ER_DIAGRAM_{layer}.md`) and the whole-flow file (`outputs/05_artifacts/ER_DIAGRAM_LINEAGE.md`) are produced by the shipped generator, deterministically derived from `column_mappings.json` — never written freehand by the model. See "Mermaid ER markdown outputs".
9. After generation, run the header verifier and treat any mismatch as fatal for this phase:
   - `python .claude/skills/design-agent/scripts/verify_workbook_headers.py --artifacts-dir outputs/05_artifacts --report outputs/00_state/evaluation/header_check.json`
   Optionally also run `verify_artifact_semantics.py` here for an early signal (it runs authoritatively in /evaluate-design).
10. Never redesign during generation. If the plan is impossible, stop and route back to the correct phase.
11. Update state/progress (the mandatory phase-completion write, including the run-root progress.json rewrite), publish `outputs/05_artifacts/`, recommend `/evaluate-design`, and stop.

## Shipped script, not runtime script

Historic behavior — the first artifact-writer authoring `outputs/00_state/runtime_scratch/generate_workbooks.py` and later writers reusing it — is retired. The canonical writer now ships with the package at `.claude/skills/design-agent/scripts/generate_workbooks.py`:

1. Nobody (orchestrator or subagent) writes, forks, or copies a generator during a run.
2. If the script fails, read its stderr: it distinguishes fatal design-contract errors (missing `column_mappings.json`, unknown layer, duplicate sheet names) from per-entry warnings (skipped malformed mapping entries, DQ rules pointing at unknown tables, tables below the R6 DQ floor). Fix the DESIGN ARTIFACTS (route back to /design-architecture if needed) — do not patch the script mid-run.
3. If the script itself has a genuine bug, that is a package defect: surface it to the user with the failing invocation and stderr; do not silently fork a modified copy under `runtime_scratch/`.
4. Record script invocations (start/end, layer, exit code) in `outputs/00_state/subagent_timings.json` so runtime execution time stays diagnosable.

## Prefer openpyxl, avoid Excel COM

The shipped generator uses `openpyxl.load_workbook(...)` for reading templates and writing outputs. Do not drive Excel via `pywin32` COM automation; per-cell COM roundtrips are 20-100x slower than openpyxl on Windows and were the dominant cause of the 40-80 min variability.

The generator:
- loads each workbook template once per workbook type,
- iterates design/mapping rows in memory, writing to sheet cells directly,
- inherits all formatting from the copied template sheets (the default single-blue theme lives in the templates; `verify_workbook_headers.py` enforces template fidelity),
- saves once per workbook,
- opens every text/JSON file with `encoding='utf-8'` on both read and write. Never rely on the platform default encoding — on Windows it is cp1252 and it silently corrupts UTF-8 bytes (§ → Â§-style mojibake). This is the sole reliable fix for the mojibake shipped in prior runs.
- never writes reason/audit text into workbook cells the schema does not expose. Any field ending in `_reason` (e.g., `threshold_value_reason`, `no_dq_reason`) is design-side rationale only; it must NOT appear as a workbook column. For `NO_DQ_APPLICABLE` / `[NEEDS_HUMAN_REVIEW]` rules, the generator folds the reason into the existing `Comments` column of the DQ sheet — no new `Reason` column.

### DQ expression cells are bare predicates (contract)

The workbook `DQ Rule Expression` cell holds the **bare boolean predicate** from `dq_rules_design.json` — verbatim, with no leading `WHERE`, no `SELECT`, and no filter composition baked in (/design-architecture rule R8). Exactly one downstream layer adds the wrapping: the verifier and the DQ runtime compose

```
SELECT 1 FROM {table} WHERE ({filter_conditions}) AND ({dq_rule_expression})
```

around the cell value. The generator defensively strips a leading `WHERE ` if a design slip-up left one in (belt + braces), but it never ADDS `WHERE` to a cell. This is what prevents the historic `WHERE ... WHERE ...` double-wrap: previously the generator baked `WHERE {filter} AND ({expr})` into the cell and the verifier wrapped it again into invalid SQL.

For `rule_type == "CUSTOM_SQL"` with `dq_rule_expression == "[CUSTOM_SQL]"`, the generator emits the `custom_sql` field verbatim to the cell (a full query, exempt from predicate wrapping). `[NEEDS_HUMAN_REVIEW]` and `[NO_DQ_APPLICABLE]` markers also pass through verbatim; the verifier skips them.

## Workbook formatting

Formatting comes from the canonical templates: the generator clones the formatted `_template_reference` sheet per table, so every generated sheet inherits the default theme (single-blue `#5B9BD5` header row, thin borders, white body rows, filters, freeze panes). The script hardcodes no palette. If `context/branding/branding_preferences.json` exists and demands a different theme, that is a template-swap decision for the human (replace the `templates/workbooks/*.xlsx` set) — not a reason to write a custom generator; `verify_workbook_headers.py` enforces whichever templates ship with the package.

## Mermaid ER markdown outputs

In addition to ER_DIAGRAM.xlsx:
- For each layer, the generator writes outputs/05_artifacts/{layer}/ER_DIAGRAM_{layer}.md.
- For the whole flow, it writes outputs/05_artifacts/ER_DIAGRAM_LINEAGE.md.

**Derivation contract (mandatory):** every Mermaid block in these files is derived programmatically from `outputs/00_state/design/column_mappings.json` (columns, PK markers, `join_conditions`-derived FK edges). The model MUST NOT hand-write or "touch up" these files. Every table's column set and PK/FK markers must be a subset of that table's columns in `column_mappings.json` — no invented columns, no generic-model boilerplate. This is an evaluator-enforced contract (see `verify_artifact_semantics.py`).

Each markdown file contains a short title and a fenced Mermaid block:

````
# ER Diagram - L0

```mermaid
erDiagram
  ...
```
````

Per-layer files:
- Use erDiagram.
- Include only tables for that layer.
- Include PK and FK markers when known.
- Include intra-layer semantic relationships where known (derived from `join_conditions`).

Whole-flow file:
- Use flowchart LR.
- One subgraph per layer plus a source-systems subgraph.
- Cross-layer lineage edges with short labels.
- Node ids copy/paste-safe for Mermaid.

If a diagram is incomplete because upstream design data is missing, the generator writes the best-derived diagram and appends a short "Known gaps" section below the Mermaid block for inferred relationships. Gaps are never papered over with invented columns.

## Header verification after generation

After generation, always run:

```
python .claude/skills/design-agent/scripts/verify_workbook_headers.py \
  --artifacts-dir outputs/05_artifacts \
  --report outputs/00_state/evaluation/header_check.json
```

Any header mismatch is fatal for this phase. Do not attempt to auto-fix headers by re-invoking the model; the script's report identifies the mismatched workbook and cell — fix the design artifacts (or report the package defect) and rerun the affected layer(s).

## Idempotent re-entry (resume on transient failure: Anthropic overload, stream timeout, tool error)

If the phase is interrupted mid-run (Anthropic 529 overloaded, stream timeout, network error), files on disk already reflect ground truth. Do NOT restart from scratch. When this skill is invoked again or the user asks to continue, detect existing valid artifacts and redo only what is missing or stale:

1. List `outputs/05_artifacts/**/*.xlsx` and record which per-layer workbooks already exist.
2. For each existing workbook, check its file size (`> 5 KB` is a good "non-trivial" threshold; smaller means a corrupt or aborted write and it should be regenerated).
3. Cross-reference each existing workbook's write time against the mtime of the canonical design sources (`column_mappings.json`, `dq_rules_design.json`). If either was modified AFTER the workbook was written, the workbook is stale and must be regenerated.
4. Regenerate ONLY the layers whose workbooks are missing, corrupt (size below threshold), or stale (design source newer) by re-invoking the shipped script with `--layer {layer}` sequentially. Skip layers whose workbooks are healthy. (The whole-flow `ER_DIAGRAM.xlsx` and `ER_DIAGRAM_LINEAGE.md` are rewritten identically on every invocation — that is expected and idempotent.)
5. Always re-run `verify_workbook_headers.py` at the end regardless of which layers were regenerated.

This mirrors the resume behavior already proven in `/design-architecture`, where per-table appends survived an Anthropic 529 mid-run and the model continued from disk state without restarting the phase.

## End Of Turn
Recommend /evaluate-design. Stop. Do not auto-invoke the next phase, even if the user previously said to do everything.

Additional context from user invocation: $ARGUMENTS
