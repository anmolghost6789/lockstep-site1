# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Build Agent

STTM-to-ETL code generation agent. Turns source-to-target mappings, data models, DQ rules, and project context into production-ready DDL, DML, DQ checks, pipeline orchestration YAML, and test scripts.

## Before any work

- Read all files in `runs/_memory/` if they exist — active conventions and decisions override defaults.
- Inspect `runs/` for existing run folders (`run_id_*`). Ask the user: new run or continue?

## Workflow skills

Each skill is invocable by its explicit `/skill-name` slash command **or** by a
natural-language request that matches the skill's `description` (no skill carries
`disable-model-invocation`, so the model triggers them from intent). The two Jira skills
(`/fetch-jira-context`, `/publish-build-summary`) have irreversible side effects — their
descriptions require explicit intent, so the model only triggers them when the user clearly
asks to fetch from / publish to Jira.

Run `/compact focus on: run_id, phase status, user decisions, next steps` **before every phase** after `/start-build-run`. On a 20+ table run this is mandatory — context overflow mid-generation wastes the entire phase.

| Skill | Purpose |
|---|---|
| `/fetch-jira-context` | (Optional, before `/start-build-run`) Discover Jira config from inputs, download Design phase outputs (STTM, Data Model, DQ, prior deliverables) from the Jira Epic, populate inputs/, derive story-to-table mapping, transition stories to In Progress with `phase:build` |
| `/start-build-run` | Python dep check → scope selection (DDL/DML/DQ/Pipeline/Tests) → input evaluation report |
| `/analyze-inputs` | Resolve conventions, build canonical model, source column registry, derivation catalog |
| `/plan-build` | Dependency waves, per-table plans, write `lineage.json` |
| `/generate-ddl` | DDL only — CREATE TABLE statements |
| `/generate-dml` | DML only — lineage reconciliation runs as its final step |
| `/generate-dq` | DQ check scripts only (format driven by `dq_framework` convention) |
| `/generate-pipeline` | Pipeline orchestration YAML — asks platform: Databricks / Snowflake / Generic |
| `/generate-tests` | Data tests (SQL/dbt assertions per table) + pipeline tests (orchestration assertions) |
| `/evaluate-build` | Deterministic scoring, quality gate, remediation list (always delegated) |
| `/revise-build` | Targeted or broad fixes, max 2 cycles — patches `lineage.json` for changed tables |
| `/publish-build-summary` | (Optional, after `/evaluate-build`) Post per-story `[BUILD]` summary comments to Jira, transition stories to Done, post Epic rollup |
| `/inspect-build` | Recover run status from filesystem after context loss |
| `/status` | Quick orientation after context reset |

### Jira integration (optional)

If the project uses Jira for traceability:

1. Run `/fetch-jira-context` BEFORE `/start-build-run` to discover the Jira config, download Design outputs from the Epic, and populate `inputs/`. The skill caches discovered Jira config to `inputs/additional_documents/jira_context.json`.
2. Each generation skill (`/start-build-run` through `/evaluate-build`) automatically posts a `[BUILD]` traceability comment to the Jira Epic. These are write-only and skip silently if MCP is unavailable.
3. Run `/publish-build-summary` AFTER `/evaluate-build` to post per-story summaries and close stories.

If no Jira context is found (`inputs/additional_documents/jira_issue_mapping.json` missing), all Jira steps are silently skipped — Build never fails because of Jira. See `references/jira_integration.md` for the full spec.

Each skill lives at `.claude/skills/<skill-name>/SKILL.md`. The orchestrator skill is `.claude/skills/build-agent/SKILL.md`.

**Generation steps are split for human-in-the-loop review.** The user invokes
`/generate-ddl`, `/generate-dml`, `/generate-dq`, `/generate-pipeline`, and
`/generate-tests` one at a time so they can inspect artifacts between steps.
There is no `/generate-build` orchestrator and you MUST NOT auto-chain
generation steps from any single command. Recommend the next step at phase
end; do not invoke it.

### Scope selection (Step 0 of `/start-build-run`)

```
1. DDL       — CREATE TABLE statements
2. DML       — transformation/load scripts
3. DQ        — data quality check scripts
4. Pipeline  — orchestration YAML (Databricks / Snowflake / Generic)
5. Tests     — data tests + pipeline tests

Enter "all" to generate all five (recommended).
```

If `pipeline = true` and `dml = false` → DML is auto-enabled (pipeline requires DML).
`pipeline_platform` is asked inside `/generate-pipeline`, not here.

## Architecture

### Supervisor / sub-agent pattern

The supervisor (the main Claude session) holds only run-level context. Heavy work is delegated:

| Sub-agent | When spawned | What it does |
|---|---|---|
| `input-analyzer` | >100 STTM rows or high complexity | Builds canonical model, source registry, derivation catalog |
| `plan-generator` | >20 tables or high complexity | Derives dependency graph, assigns waves, writes per-table plans |
| `artifact-writer` | >5 tables (always for generate phases) | Generates DDL/DML/DQ/pipeline/tests for a wave of tables |
| `build-evaluator` | Always | Scores all artifacts against evaluation rubric |
| `learnings-curator` | Stop / phase end | Promotes durable lessons into `runs/_memory/` and `.claude/agent-memory/<subagent>/` |

Subagents with `memory: project` use `.claude/agent-memory/<subagent>/`. Do not move that folder into `runs/_memory/`.

**Supervisor context discipline:** never read `canonical_build_model.json`, `source_column_registry.json`, `derivation_catalog.json`, or generated artifact files directly. Read only compact index files (`table_index.json`, `build_blueprint.json`) and handoff summaries.

### Filesystem layout

```text
context/branding/                       # docx render preferences (durable)
context/guidance/                       # enterprise / domain / project context (durable)
context/reference/                      # vendor patterns, style guides (durable)
context/<user-custom-subfolder>/        # any custom subfolder — also scanned

inputs/sttm/                            # source-to-target mappings (active)
inputs/data_model/                      # canonical / layer-N data models (active)
inputs/dq_rules/                        # data-quality rule workbooks (active)
inputs/business_rules/                  # business-rule narratives (active)
inputs/legacy_code/                     # legacy SQL/ETL patterns to mirror (active)
inputs/known_gaps/                      # gaps the agent should respect (active)
inputs/additional_documents/            # user instructions, supporting docs (active)
inputs/<user-custom-subfolder>/         # any custom subfolder — also scanned

runs/_memory/                           # durable cross-run memory (MEMORY/CONVENTIONS/DECISIONS/PATTERN_LIBRARY)
runs/run_id_<ID>/                       # active run workspace (see below)
outputs/run_id_<ID>/                    # synced user-facing artifacts (mirrors run dir's outputs/)

.claude/skills/                         # slash-invoked skills + build-agent orchestrator
.claude/skills/build-agent/             # orchestrator: SKILL.md, workflow_manifest.json, assets/, references/, scripts/
.claude/agents/                         # subagent profiles
.claude/agent-memory/                   # project-scoped subagent memory
.claude/hooks/                          # SessionStart, PreToolUse, PostToolUse, Stop hooks
```

The default subfolder names under `inputs/` and `context/` are semantic hints, not a closed list. Users may create any custom subfolder; the agent walks the trees recursively and classifies by content. Supported extensions: `.md`, `.markdown`, `.txt`, `.docx`, `.pdf`, `.csv`, `.xlsx`, `.xls`, `.json`, `.yaml`, `.yml`.

### Per-run workspace shape

```text
runs/run_id_<ID>/
  session.json            ← run ledger; updated after every significant step (internal — never synced)
  phase_handoff.json      ← cross-phase continuity (internal — never synced)
  progress.json           ← UI progress: done / current / next steps (auto-derived from session.json by sync_outputs.py; internal — never synced)
  discovery/              ← canonical_build_model, effective_conventions, relationships, etc.
  plans/
    table_index.json      ← compact wave index (supervisor reads this)
    build_blueprint.json  ← dependency graph (supervisor reads this)
    lineage.json          ← source-to-target graph, platform-neutral (written by /plan-build)
    <table>_plan.json     ← per-table plan (sub-agents read these)
  generated/
    ddl/                  ← CREATE TABLE statements
    dml/                  ← load scripts
    dq/                   ← DQ check scripts
    pipeline/             ← workflow_master.yml + wave files (Databricks/Generic)
                          ← pipeline_tasks.sql + activate/suspend (Snowflake)
    tests_data/           ← SQL/dbt assertions per table
    tests_pipeline/       ← pipeline orchestration test suite
    _validation/          ← prevalidation_dml.json (contains dml_corrections[] for lineage reconciliation)
  evaluation/
  revision_notes/
  logs/logs.md            ← append-only wall-clock log per phase
  inputs/                 ← snapshot of inputs/ at run start
  context/                ← snapshot of context/ at run start
  outputs/                ← synced copies at phase boundaries (mirrors top-level outputs/run_id_<ID>/)
```

`sync_outputs.py` mirrors only user-facing artifacts into an ordered, numbered
`outputs/<run_id>/` tree — internal machinery (`session.json`, `phase_handoff.json`,
`progress.json`, per-table `*_plan.json`, `plan_handoff_summary.json`,
`generated/_validation/prevalidation_*.json`, `scratch/`) is never synced:

```text
outputs/run_id_<ID>/
  01_input_evaluation/  input_evaluation_report.md
  02_analysis/          canonical_build_model, effective_conventions, relationships,
                        dq_catalog, source_column_registry, derivation_catalog,
                        semantic_checks, lineage.json, build_blueprint, table_index
  03_generated/         ddl/ dml/ dq/ pipeline/ tests_data/ tests_pipeline/
  04_evaluation/        evaluation report + scores
  logs.md
```

The legacy layout used top-level `state/run_id_*/` and `outputs/run_id_*/`. The package now consolidates everything into `runs/run_id_<ID>/`. `inspect-build` trusts the run dir's `state/`-equivalent paths over `outputs/` for recency.

### Lineage system

`plans/lineage.json` is written by `/plan-build` Step 3 and is the single source of truth for pipeline generation and pipeline tests. It is platform-neutral.

**Lifecycle:**
1. `/plan-build` writes it from `canonical_build_model` + `relationships` + `build_blueprint` + `context/guidance/domain_context.*` — all entries `lineage_source: "planned"`
2. `/generate-dml` reconciles it — artifact-writer writes corrections to `prevalidation_dml.json::dml_corrections[]`; supervisor patches `lineage.json` entries to `lineage_source: "reconciled"`
3. `/revise-build` patches it for any tables in the revision scope
4. `/generate-pipeline` reads it (never re-derives transformation logic from SQL)
5. `/generate-tests` reads it for pipeline test assertions

`session.json` tracks: `planning_summary.lineage_generated`, `planning_summary.lineage_reconciled`.

**Lineage.json contract (schema-locked):**
- Field names in `lineage.json` are locked. Any rename is a breaking change requiring updates to all consuming phases.
- **Capture-or-lose:** Any source-column metadata, transformation rule, or DQ binding that is not written to `lineage.json` at the moment it is decided in `/plan-build` CANNOT be recovered by downstream phases without re-reasoning from scratch. Write it immediately.
- **Fail-loudly in consumers:** `/generate-pipeline` and `/generate-tests` load `lineage.json` once as read-only. If a required field is missing, STOP and report. Do NOT invent column names, transformation logic, or dependency edges.

### Generation execution order

```
DDL
 ├──→ DML (→ lineage reconciliation at end) ─┐
 └──→ DQ ────────────────────────────────────┴──→ Pipeline → Tests
```

DML and DQ run in parallel (both depend only on DDL). Pipeline runs after both complete (needs reconciled lineage). Tests run last (pipeline tests need pipeline artifacts).

### Convention priority chain

`user_instructions > runs/_memory > project_context > domain_context > enterprise_context > input_pattern > default`

Conflicts are recorded in `effective_conventions.json::conflicts_resolved[]` — this array is required for packaging.

## Core rules

- **No mid-phase questions.** Make safe assumptions, document them, surface at phase end only.
- **Produce everything.** No scope exclusion. Thin-evidence tables get `[ASSUMPTION]` / `[INSUFFICIENT INPUT]` notices, not omission.
- **Filesystem is truth.** Never evaluate from conversation memory — re-read from disk.
- **Stable IDs.** Convention decisions, table IDs, and entity IDs do not change mid-run.
- **No silent instruction overrides.** Record deviations as waivers in the assumptions register.
- **Do not reuse SQL from prior runs.** Every artifact is composed from the current run's canonical model.
- **STOP at phase boundaries.** After completing the requested slash-command, you MUST stop and return control to the user. Do not auto-invoke the next phase. Recommend the next step at the end; do not run it.

## JSON output discipline (mandatory)

Any artifact written with a `.json` extension MUST be syntactically valid JSON.
Before every `Write` of a JSON file:

1. Build the value as a Python or JS object first (not by string concatenation).
2. Serialize with `json.dumps(value, indent=2, ensure_ascii=False)` (Python) or
   `JSON.stringify(value, null, 2)` (JS) — never hand-write JSON braces, commas,
   or escape sequences.
3. If you have to compose a JSON file in chunks (>30 KB part-file strategy),
   build all parts as objects, concatenate the objects in memory, then serialize
   ONCE to JSON. Do not concatenate JSON-text fragments — that is how trailing
   commas, duplicate top-level objects, and orphan brackets get produced.
4. Before reporting a JSON file as written, validate by re-reading and parsing:
   `python -c "import json,sys; json.load(open(sys.argv[1]))" <path>`. If it
   fails, regenerate the file from the in-memory object — do not patch the
   bytes.

This applies to every JSON artifact: `session.json`, `phase_handoff.json`,
`canonical_build_model.json`, `lineage.json`, `dq_catalog.json`,
`build_blueprint.json`, `table_index.json`, `_validation/*.json`,
evaluation score files, and any per-table plan files.

## Memory — read per-phase, write at every boundary (mandatory)

Two memory tiers:

1. **Package memory** at `runs/_memory/` — shared across all runs. Seed files: `MEMORY.md`, `CONVENTIONS.md`, `DECISIONS.md`, `PATTERN_LIBRARY.md`.
2. **Per-run scratch memory** inside the run dir at `runs/run_id_<ID>/memory/` — promoted into package memory by `learnings-curator` at run end.

**Read all four `runs/_memory/` files at the start of every slash-command phase** (not every turn — between turns within a phase, memory is already in context). Apply what you find — learned conventions override defaults, prior decisions stay honored unless superseded.

**Write at every phase boundary**, before the handoff summary. Examples:
- User convention → `CONVENTIONS.md` (e.g., "VARCHAR(20) for NPI everywhere")
- Platform choice → `DECISIONS.md` (e.g., "Databricks over Snowflake")
- Reusable pattern → `PATTERN_LIBRARY.md` (e.g., "SCD2 MERGE clause that works well")
- Data quirk → `MEMORY.md` (e.g., "IQVIA LAAD has trailing nulls in prescriber_npi")
- User correction → `MEMORY.md` (e.g., "prescriber_npi is a business key, not surrogate")

Rules: use template format, append only, mark superseded entries, one decision per entry, keep entries short.

## Drift detection & change propagation (mandatory)

Artifacts in this workflow drift when:
- the user manually edits a generated file (DDL, DML, pipeline YAML, etc.)
- the user asks the agent to ad-hoc edit a generated file
- a `/revise-build` cycle changes one artifact family but the JSONs that
  drive other families still reflect the old state

If you proceed to the next phase using stale discovery JSONs, downstream
artifacts will reproduce the old, wrong state and the user has to redo work.
This rule prevents that.

**At the start of every `/generate-*` command (Step 0), and any turn where
the user mentions edits ("I changed X", "I made some changes"), run drift
detection BEFORE doing any new generation:**

1. **Read the upstream-of-this-phase artifacts from disk** (not from
   conversation memory). Each phase has a fixed upstream set:

   | Phase | Upstream artifacts to re-read |
   |---|---|
   | `/generate-ddl` | canonical_build_model.json, effective_conventions.json, all `<table>_plan.json` |
   | `/generate-dml` | DDL files in `runs/<run>/generated/ddl/`, canonical_build_model.json, derivation_catalog.json, lineage.json, effective_conventions.json |
   | `/generate-dq` | DDL files, dq_catalog.json, effective_conventions.json |
   | `/generate-pipeline` | DDL files, DML files, lineage.json (reconciled), effective_conventions.json |
   | `/generate-tests` | DDL, DML, DQ, pipeline YAML, lineage.json |
   | `/evaluate-build` | All generated artifacts + their backing JSONs |

2. **Reconcile** — for each entity referenced in a generated file (table
   names, columns, types, conventions, lineage edges), compare the file
   against the corresponding discovery JSON. The **generated file is the
   newer source of truth** when there is conflict (the user touched it
   most recently). Update the JSON to match. Specifically:
   - DDL has a column the canonical model lacks → add to canonical model
     (with a `[USER_EDITED]` provenance tag and run id).
   - DDL drops a column the canonical model still has → remove from
     canonical model AND patch lineage.json edges referencing that column.
   - Table renamed in DDL → cascade-rename in canonical_build_model,
     lineage.json, derivation_catalog (entity table_id stays stable; only
     `physical_name` changes — see stable-ID rule).
   - Convention drift (e.g., user lower-cased table names in DDL) →
     update `effective_conventions.json::naming.table_case` AND record a
     waiver in the assumptions register if it conflicts with prior decisions.
3. **Memorize the change** — every reconciliation writes a one-line entry
   to `runs/_memory/MEMORY.md` so you don't re-derive it next time and the user
   doesn't have to repeat themselves.
4. **Note in the response** — start the response with a short
   "Reconciliation:" block listing what drift was detected and how it was
   patched. Then proceed with the requested work.
5. **If reconciliation is ambiguous** (e.g., user made conflicting edits
   to two DDL files), STOP and ask one short clarifying question. Do not
   silently pick a side.

**Cross-phase example (the user's pain point):**

After `/generate-ddl`, the user manually edits `prescriber_npi` from
`VARCHAR(10)` to `VARCHAR(20)` across all stg DDL files, then runs
`/generate-dml`. Step 0 of `/generate-dml` MUST:
- read all DDL files
- detect that `prescriber_npi` width changed
- update `canonical_build_model.json` to show width 20
- write `runs/_memory/CONVENTIONS.md` entry: *"prescriber_npi width = VARCHAR(20)
  per user edit on <date>"*
- generate DML using the corrected width — and any DQ / pipeline / tests
  generated next will read the same updated canonical model.

The user's edit propagates automatically through the rest of the build.

## Turn types — slash-command vs Q&A vs ad-hoc edit

Every user message falls into ONE of three turn types. Classify before responding.

**1. SLASH-COMMAND TURN** — input begins with `/<skill-name>`. Execute the phase per its SKILL.md and end with a handoff summary. Do NOT auto-invoke other slash-commands.

**2. FREE-FORM Q&A TURN** — user is asking a question. Answer it directly from filesystem and run state. Q&A turns DO NOT include:
- phase-handoff summaries or "Generation complete" / status tables
- "Run /compact ..." instructions
- "Next: /<command>" recommendations or auto-advance prompts
- re-explanation of what was just done unless the user asks

**3. AD-HOC EDIT TURN** — user is asking you to change something inside the current run ("fix the typo in this DDL", "patch lineage for table X", "remove this stub task"). This IS in scope — make the change, do not refuse. Rules:
- Edit only inside the active run dir (`runs/run_id_<ID>/`). Refuse only if outside the run dir or outside build-agent scope.
- Read the target file first. Make the smallest correct edit. Re-read after Edit to confirm.
- Update cross-references the edit touches (`lineage.json`, `session.json`, `phase_handoff.json`, etc.). Stable-ID rule still applies.
- If the edit invalidates evaluation/packaging artifacts, name which ones are stale and suggest re-running `/evaluate-build`. Do not auto-run.
- Sync touched files from the run dir's working area to its `outputs/`.
- End with a short summary of what changed (file paths + line ranges) and any downstream artifacts now stale. NO phase-handoff block.

If the input is ambiguous, default to Q&A — ask one short clarifying question, don't silently guess what to edit.

For broad / multi-table revisions, route the user to `/revise-build` (better traceability, lineage patching). Tell them once; do not refuse the immediate edit if they prefer ad-hoc.

## Performance guardrails

- **Chunked-write (mandatory for all sub-agents):** ≤ 30 KB / ~600 lines per `Write` or `Edit` call. Part-file strategy for larger artifacts: `parts = ceil(estimated_kb / 25)`, then `cat`-concatenate, verify master non-empty, delete parts.
- **Tool discipline:** Always use the `Write` tool for content — never Bash `echo`/`printf`/heredoc. Windows Git Bash quoting breaks on SQL/JSON with `"`, `$`, or `--`.
- **Supervisor on Sonnet:** Run `/model sonnet` at the start of `/analyze-inputs` and any `/generate-<artifact>` command.
- **Maximum parallelism for generation within a `/generate-<artifact>` command:** When generating a multi-wave artifact, launch ALL waves of that artifact simultaneously in one message (cache-warm first wave alone, then all remaining in one batch). Same pattern applies inside `/generate-tests`.
- **Plan-generator writes lineage.json:** The plan-generator sub-agent assembles lineage.json as its final step — the supervisor must NOT read plan files to re-assemble it. This saves ~9 minutes on a 22-table run.
- **Platform asked at Step 0:** When pipeline is selected at `/start-build-run`, the pipeline platform (Databricks / Snowflake / Generic) is asked immediately — not deferred to `/generate-pipeline`.
- **Cache-warming:** When spawning 3+ artifact-writer instances, launch the first alone, wait for its first tool result, then launch the rest in parallel.
- **Stream idle timeout:** Set to 600000 ms in `.claude/settings.json`.

## Shared Python scripts (use instead of inline code)

Four scripts in `.claude/skills/build-agent/scripts/` handle repeated operations:

| Script | When to use |
|---|---|
| `sync_outputs.py <run_id>` | At phase end — mirrors user-facing artifacts into the numbered `outputs/<run_id>/` tree (01_input_evaluation … 04_evaluation) and refreshes `progress.json`. Internal machinery is never synced. |
| `update_progress.py <run_id>` | Derives `state/<run_id>/progress.json` (UI done/current/next) from `session.json` + `workflow_manifest.json`. Called automatically by `sync_outputs.py` at every phase boundary, so skills do not invoke it directly. |
| `validate_artifacts.py <run_id> --all` | After generation — checks all family file counts against session.json |
| `patch_session.py <run_id> key=value …` | Update session.json fields without reading the full file |
| `append_log.py <run_id> <phase> <start> <end> --steps …` | Append timing section to logs/logs.md |

All use only Python stdlib. No extra packages.

## Execution plan

`/start-build-run` generates an Execution Plan alongside the Input Evaluation Report. Both are presented to the user before they decide to proceed. The plan shows: table inventory by layer, phase plan with dependencies, wave preview, convention preview, known gaps, and estimated effort. Template and schema in `references/execution_plan.md`.

## Lifecycle hooks

See `.claude/hooks/README.md`.

| Hook | Event | Purpose |
|---|---|---|
| `load-run-state.sh` | SessionStart | Prints run_id, current phase, scope, lineage status, last completed step. |
| `quality-gate.py` | PreToolUse (Write) | Blocks template residue from being written into `generated/{ddl,dml,dq,pipeline,tests_*}/`. |
| `lint-output.py` | PostToolUse (Write\|Edit) | Non-blocking nudge when a generated build artifact contains TODO/TBD/FIXME or `<TABLE_NAME>`-style placeholders. |
| `verify-completeness.py` | Stop | Confirms every selected scope item marked complete in `session.json` actually has at least one artifact on disk. |

## Reference index (read on demand only, NOT at startup)

| Reference | Read when |
|---|---|
| `references/checkpoint_format.md` | At phase start/end for display formatting |
| `references/delegation_protocol.md` | Before delegating to a sub-agent |
| `references/evaluation_rubric.md` | During `/evaluate-build` |
| `references/execution_plan.md` | During `/start-build-run` Step 3g |
| `references/hitl_protocol.md` | When presenting user-facing checkpoints |
| `references/input_validation.md` | During `/start-build-run` Step 3 |
| `references/jira_integration.md` | During `/fetch-jira-context`, `/publish-build-summary`, or any phase posting a `[BUILD]` traceability comment |
| `references/lineage_schema.md` | During `/plan-build` and `/generate-dml` |
| `references/pipeline_conventions/databricks.md` | During `/generate-pipeline` (Databricks) |
| `references/pipeline_conventions/snowflake.md` | During `/generate-pipeline` (Snowflake) |
| `references/quality_standards.md` | During `/analyze-inputs` and `/evaluate-build` |
| `references/remediation_and_packaging.md` | During `/revise-build` |
| `references/runtime_contract.md` | When checking folder/file conventions |
| `references/test_assertion_standards.md` | During `/generate-tests` — data + pipeline test minimum matrices |
| `references/pipeline_artifact_rules.md` | During `/generate-pipeline` — per-platform outputs + wave-generator rules |

References live under `.claude/skills/build-agent/references/`.

## Python dependencies

```bash
pip install -r .claude/skills/build-agent/scripts/requirements.txt
```

Auto-checked at `/start-build-run` Step -1. Run halts with install command if any package is missing.

## MCP integrations

`.mcp.json` registers:

- **`git` (GitHub Copilot MCP)** — for committing generated artifacts and reading repo state. Requires a fine-grained `GITHUB_PAT` in `.claude/settings.local.json`.
- **`jira` (Atlassian MCP)** — for posting `[BUILD]` traceability comments, transitioning stories, and per-story summaries. Uses API-token (PAT) auth via the `Authorization: Basic ${JIRA_BASIC_AUTH}` header in `.mcp.json` — never OAuth/SSO. Requires the Atlassian org admin to have enabled API-token auth for MCP at the org level. With PAT auth, `cloudId` is not implicit — resolve via `getAccessibleAtlassianResources` on first use and cache in `inputs/additional_documents/jira_context.json`. See `references/jira_integration.md`.

Copy `.claude/settings.template.json` → `settings.json` and `.claude/settings.local.template.json` → `settings.local.json`, then fill in tokens in `settings.local.json`.

