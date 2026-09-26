# Running in Claude Code

## Setup

1. Copy `.claude/settings.template.json` to `.claude/settings.json`. It registers the policy hooks and permissions.
2. For org-wide enforcement, deploy `.claude/managed-settings.example.json` through device management.
3. Check `config/project_config.json > gate_mode`: `github` (default) needs the GitHub CLI; `local` records gates with `adlc_gate.py`.

## Commands

See [Command reference](command-reference.md). Each phase command runs one phase and stops; it never starts the next phase on its own.

## Hooks

`pre_tool_guard.py` runs before every tool call. It blocks writes to gate and audit records, secrets in written content, writes outside the project, and MCP calls that aren't allow-listed for the current phase. `post_tool_audit.py` records every change to a lifecycle artifact.

If a tool call is blocked, the agent sees the reason and must change course. Blocks are written to the audit log.

## Local gate mode

With `gate_mode: local`, the author requests a gate with the phase command, and the approver runs `/approve-gate <gate>` in their own session. Roles come from `ADLC_GROUPS` (set from your identity provider) or the static list in `gate_roles.json`.
