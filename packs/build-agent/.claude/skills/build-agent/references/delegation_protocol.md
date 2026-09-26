# Delegation Protocol

## Purpose

For runs above the mandatory thresholds, the orchestrator delegates phase work to sub-agents. Each sub-agent runs in its own context window, reads from disk, writes to disk, and returns a compressed handoff summary. This keeps the supervisor context lean and enables parallel execution.

## Mandatory Delegation Thresholds

| Phase | Delegate when | Threshold rationale |
|---|---|---|
| `/analyze-inputs` | total input words > 5,000 OR > 3 files OR any STTM > 100 rows OR complexity = moderate/high | Input volume drives context bloat, not STTM row count alone |
| `/plan-build` | total tables > 20 OR complexity = high | Canonical model reads (100–500 KB) belong in sub-agent, not supervisor |
| `/generate-*` | tables in run > 5 | Wave-by-wave delegation |
| `/evaluate-build` | always | Evaluation reads ALL artifacts — always isolate |
| `/revise-build` (broad) | affected tables > 3 OR cross-cutting convention change | Broad revision reads many artifacts — delegate to prevent context bloat and hallucination |

Below thresholds: delegation is recommended but not required. Even small runs benefit from sub-agent context isolation.

## Pre-Configured Sub-Agents

The package ships pre-configured sub-agent definitions in `.claude/agents/`:

| Agent | Role | When Used |
|---|---|---|
| `input-analyzer` | Normalize inputs, resolve conventions, build canonical model | `/analyze-inputs` — above threshold |
| `plan-generator` | Derive dependencies, assign waves, write per-table plans + compact table_index | `/plan-build` — above threshold |
| `artifact-writer` | Generate artifacts for a wave of tables (artifact-family mode: DDL / DML / DQ / tests / revision) | `/generate-*` and `/revise-build` (broad) |
| `build-evaluator` | Score generated artifacts against rubric | `/evaluate-build` — always |

## Supervisor Responsibilities

The supervisor (main context window):
- Holds run-level context only: session.json summary, phase_handoff.json, user decisions
- Delegates phase work by spawning sub-agents with structured prompts
- **Pre-sizes expected output before delegation** and tells sub-agents which write strategy to use — do not let agents discover this themselves
- Receives handoff summaries (under 500 words each)
- Makes routing decisions based on summaries
- Manages user interaction at phase boundary checkpoints
- **NEVER reads full input files, discovery JSONs (canonical model, source registry, derivation catalog), or generated artifacts directly** — these are sub-agent responsibilities
- **Passes file paths, not file contents** in delegation prompts
- **Uses Bash filesystem checks** (`test -f`, `wc -c`, `ls | wc -l`) to validate outputs — not content reads

## Supervisor Context Budget

The supervisor context must stay below 30% utilization. It should contain:
- CLAUDE.md / AGENTS.md (auto-loaded)
- User messages and decisions
- Phase handoff summaries
- Sub-agent handoff summaries
- Current routing decision context

If the supervisor finds itself reading a full input file or generated artifact, it is violating the context budget. Delegate instead.

## Sub-Agent Prompt Format

When spawning a sub-agent, provide:

```
## Task
[Phase-specific task description]

## Run Context
- run_id: {run_id}
- session summary: {compressed summary}
- conventions summary: {key resolved conventions}

## Input File Paths (read from disk)
- {path1}
- {path2}

## Output Location
Write all outputs to: {output_path}

## References to Read First
- {skill_path}/references/{relevant_reference}.md

## Write Strategy
Estimated output size: {estimated_kb} KB
Strategy: {single_write | section_streaming | part_file (N parts)}

## Constraints
- {user decisions and accepted assumptions}

## Handoff
When done, return a JSON object with these fields:
- completion_status: complete | partial | blocked
- outputs_written: [list of file paths]
- decisions_made: [list of decisions with rationale]
- issues_found: [list with severity]
- assumptions_made: [list with risk level]
- chunked_write_used: {true|false per artifact}
- recommended_next_action: string
Keep the entire handoff under 500 words.
```

## Sub-Agent Execution Rules

Every sub-agent must:
- Read its assigned input files from disk (not from the prompt)
- Read the relevant phase SKILL.md and references from disk
- Write all outputs to disk per the runtime contract
- **Use the `Write` tool (never Bash) for content writes.** Bash is restricted to read-only ops: `ls`, `mkdir -p`, `test -f`, `wc -c`, and post-write `cat` concatenation. Reason: Windows Git Bash quoting fails on SQL/JSON content containing `"`, `$`, `--` comments, or backticks; documented past failures wasted entire sub-agent turn budgets on `echo`/`printf`/heredoc retries.
- Update session.json with its progress
- Never ask the user questions — make safe assumptions and document them
- Return a structured handoff summary as its final message

## Sub-Agent Constraints

- Sub-agents CANNOT spawn other sub-agents (flat delegation only)
- Maximum 8 concurrent sub-agents
- Each sub-agent should complete within 50 turns (`maxTurns: 50`); artifact-writer is `maxTurns: 120` due to chunked writes across multiple tables
- Sub-agents use `sonnet` model by default

## Chunked-Write Policy (MANDATORY for all sub-agents writing > 30 KB files)

Claude Code has a stream idle timeout (default 5 min, hard watchdog at ~10 min). A single Write call carrying 100KB+ of generated content streams tokens for several minutes with no intervening tool activity, which trips the watchdog and silently kills the sub-agent's turn. This caused a 9-hour wall-clock blowup on a prior run before this policy was instituted.

**Hard rule for every sub-agent:**
- No single `Write` or `Edit` call may carry > 30 KB or ~600 lines of payload
- If output > 50 KB, the sub-agent uses the **part-file strategy**: write `<name>_part1.sql` (or `.json`), `<name>_part2.sql`, etc. (each ≤ 30 KB), then concatenate via `cat` in a Bash call

**Pre-sizing methodology:** the supervisor estimates each artifact's expected output BEFORE delegation and tells the sub-agent which strategy to use. Two methods:
1. **Line-count method (SQL artifacts):** count mapped columns × lines per column by artifact type (DDL: 3–5 lines/col, DML: 5–15 lines/col) + structural overhead
2. **Record-count method (JSON artifacts):** count records × KB per record + structural overhead

**Routing decision (size-driven, not type-driven):**
- ≤ 30 KB → single Write
- 30–50 KB → section-streaming (Write Part 1, then Edit append)
- > 50 KB → part-file strategy with `parts = ceil(estimated_kb / 25)` (no upper bound on part count)

A simple staging table DML might be 5 KB (single Write); a complex SCD2 dimension DML might be 80 KB (~4 parts); a mega-enterprise multi-source fact DML might be 200 KB (~8 parts). Never assume part count from table type.

**Watchdog safety net (Claude Code only):** `.claude/settings.json` sets `CLAUDE_STREAM_IDLE_TIMEOUT_MS=600000` (10 min). This matches Claude Code's default sub-agent kill threshold so failures surface promptly and Claude Code's automatic non-streaming retry kicks in fast — it does NOT replace the chunked-write policy.

## Parallel Execution

### Within a wave
Tables within a wave CAN run in parallel (independent work units). Waves are sequential (dependency order).

### Across artifact families (generate-build orchestrator)
The four artifact families have a partial dependency order. Exploit it:

```
DDL (must complete first — all others depend on it for column ref validation)
 ├──→ DML  ─┐  (independent of each other — run in parallel)
 └──→ DQ   ─┴──→ Tests  (can reference DML for assertion targets)
```

**DML and DQ run in parallel** after DDL completes. Each has its own output folder (`generated/dml/`, `generated/dq/`) and its own prevalidation file (`prevalidation_dml.json`, `prevalidation_dq.json`). There is no write conflict. On a high-complexity run this saves 25–40% of total generation wall-clock.

**Tests run after both DML and DQ complete** — not because tests depend on DQ, but because tests can optionally read DML artifacts to inform assertion targets.

### Broad revision
When `/revise-build` delegates broad revision, one `artifact-writer` per artifact family runs concurrently (up to 4 parallel: DDL-revision, DML-revision, DQ-revision, tests-revision). Each sub-agent owns only its family's files — no write conflicts.

### Analysis and evaluation
Single-sub-agent tasks — no parallelism within the phase.

## Cache-Warming Launch Order (when spawning 3+ artifact-writer instances)

Anthropic's prompt-caching docs are explicit: for concurrent requests, a cache entry only becomes available after the first response begins. If you fire all artifact-writer instances in parallel, the 2nd through Nth all miss the cache on the same large system prompt and references.

The fix when spawning **3+ instances of the same sub-agent type**:

1. **Launch the first instance alone** in its own supervisor message.
2. **Wait for its first tool result** (typically the first Read of a reference file — that's enough to confirm the system prompt has streamed and is now cacheable).
3. **Then launch the remaining N-1 instances in parallel** in a single supervisor message — they all hit the warmed cache.

For 1–2 instances of a given type, just launch them in parallel — the staggering overhead isn't worth the small cache win.

This typically saves **30–60%** on per-instance latency for the warmed instances on large reference docs.

## Handoff Summary Validation

Before using a sub-agent handoff summary, the supervisor validates:
- `completion_status` is present and valid
- `outputs_written` lists files that actually exist on disk
- `issues_found` are properly severity-classified
- Summary is under 500 words

If validation fails, the supervisor re-delegates or reports the failure at the checkpoint.

## Platform Execution

### Claude Code
Sub-agents spawned via Task tool. Pre-configured definitions in `.claude/agents/` are auto-discovered.

Filesystem is shared state. Handoff summary is the interface.

## Phase Handoff Between Phases

At the end of each phase, write `state/run_id_<ID>/phase_handoff.json`:

```json
{
  "completed_phase": "generate-build",
  "completed_at": "ISO timestamp",
  "next_recommended_phase": "evaluate-build",
  "next_command": "/evaluate-build",
  "summary": "Generated artifacts for 12 tables across 3 waves.",
  "user_decisions": [],
  "key_artifacts": []
}
```

The next phase reads this file in Step 1 to understand what happened previously.
