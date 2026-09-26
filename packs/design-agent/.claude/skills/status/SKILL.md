---
name: status
description: "Show current run state, phase state, important links, blockers, and next safe action. User-invoked only."
disable-model-invocation: true
allowed-tools:
  - AskUserQuestion
  - Agent
  - Read
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
  - Bash(python3:*)
  - Bash(unzip:*)
  - Bash(zip:*)
  - Bash(head:*)
  - Bash(tail:*)
  - Bash(sort:*)
---

# /status

Show the current run state and next safe action.

1. Read `CLAUDE.md` and `.claude/skills/design-agent/SKILL.md`.
2. Read `outputs/00_state/run_state.json`.
3. If `outputs/00_state/run_state.json` does not exist, say: `No active run found. Use /start-design-run to begin.`
4. Display:
   - Run ID, client name, domain, target platform if known.
   - Run status: `not_started | in_progress | waiting_for_user | changes_requested | rerun_required | completed | cancelled | error`.
   - Current stage with description.
   - Current phase and `awaiting_user_action` if any.
   - Stage history with IST timestamps.
   - Phase statuses from progress.json when available.
   - Input snapshot path.
   - Clickable link to `outputs/00_state/standard_input_set/input_set_evaluation_report.md` if created.
   - Clickable links to generated output Excel artifacts under `outputs/` if generated.
   - Active folder status for `outputs/00_state/` (agent state) and `outputs/` (deliverables).
   - Force-continue status and `outputs/RISK_MANIFEST.json` if active.
   - Layers identified and table counts.
   - Overall confidence score if computed.
   - Reference store enabled/disabled and patterns available.
   - Total human interactions count.
   - Runtime scratch cleanup status if known.
   - Whether any subagent is expected, currently running, or has recently completed according to `outputs/00_state/handoffs/`.
   - Whether terminal input cleanup has completed for this run.
5. Do not advance stages from `/status`.

Use clickable Markdown links for files, for example `[Open input set evaluation report](outputs/00_state/standard_input_set/input_set_evaluation_report.md)`.

Do not paste heavy report contents into chat from `/status`. Use concise summaries and clickable Markdown links only.

