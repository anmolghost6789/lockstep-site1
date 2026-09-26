# Build Agent

This project uses the Build Agent skill package for STTM-to-ETL code generation.

## Package assets
- `.claude/skills/` (orchestrator at `build-agent/`, per-phase skills as siblings)
- `.claude/agents/` (sub-agents)
- `.claude/agent-memory/` (project-scoped subagent memory)
- `.claude/hooks/` (SessionStart, PreToolUse, PostToolUse, Stop)
- `.claude/skills/build-agent/assets/templates/` — golden input templates
- `.claude/skills/build-agent/scripts/` — shared Python tools
- `CLAUDE.md` (Claude Code entry point)
- `AGENTS.md` (universal entry point)
- `README.md`
- `.mcp.json` (github + jira MCP)

## Runtime artifacts
- `inputs/` — active per-run inputs organized in subfolders (sttm, data_model, dq_rules, business_rules, legacy_code, known_gaps, additional_documents)
- `context/` — durable cross-run context (`branding/`, `guidance/`, `reference/`)
- `runs/run_id_<ID>/` — active run workspace (state, plans, generated, evaluation, outputs, memory)
- `runs/_memory/` — durable cross-run package memory (CONVENTIONS, DECISIONS, MEMORY, PATTERN_LIBRARY)
- `outputs/` — mirror of the active run's `outputs/` for download / handoff

## Before any work
- Read memory files in `runs/_memory/` if they exist.
- Inspect existing run folders under `runs/run_id_*/` if they exist.
- Ask whether the user wants a new run or to continue an existing one.

## Commands

| Command | Purpose |
|---|---|
| `/start-build-run` | Check Python deps, ask scope, inventory inputs, Input Evaluation Report |
| `/analyze-inputs` | Normalize inputs, resolve conventions, build canonical model |
| `/plan-build` | Derive dependencies, build waves, per-table plans |
| `/generate-ddl` | Generate DDL only |
| `/generate-dml` | Generate DML only (includes lineage reconciliation) |
| `/generate-dq` | Generate DQ check scripts only |
| `/generate-pipeline` | Generate pipeline orchestration YAML (asks platform: Databricks/Snowflake/Generic) |
| `/generate-tests` | Generate data tests + pipeline tests |
| `/evaluate-build` | Score deterministically, write remediation (always delegated) |
| `/revise-build` | Apply targeted or broad fixes (max 2 cycles) |
| `/inspect-build` | Reconstruct status from filesystem after context loss |
| `/status` | Quick orientation after context reset |

Each command is a skill at `.claude/skills/<command-name>/SKILL.md`. There is no separate `commands/` folder.

## Core rules
- **No mid-phase questions.** Make safe assumptions, document, present at phase end.
- **Produce everything you can.** No scope exclusion. Use inline notices for gaps.
- **Filesystem is the source of truth.**
- **Mandatory sub-agent delegation** above thresholds.
- **Context hygiene between phases.** Start new session (Cursor) or `/compact` (Claude Code).
- Convention priority: user instructions > runs/_memory > project > domain > enterprise > pattern > default.

## Performance guardrails
- **Pre-flight preview (mandatory):** Before any tool call in a heavy phase, print the pre-flight block from `references/checkpoint_format.md`.
- **Chunked-write policy:** No single `Write` or `Edit` call may exceed 30 KB / ~600 lines. SQL artifacts use part-file strategy (`parts = ceil(estimated_kb / 25)`), then `cat`-concatenate.
- **Tool discipline:** Use the `Write` tool for all content writes in sub-agents. Never use Bash `echo`/`printf`/heredoc for SQL or JSON — Windows Git Bash quoting fails on these.
- **Cache-warming:** when spawning 3+ artifact-writer instances, launch the first alone, wait for first tool result, then launch the rest in parallel.
- **Stream idle timeout:** `.claude/settings.json` sets `CLAUDE_STREAM_IDLE_TIMEOUT_MS=600000`.

