# Claude Code Hooks

Registered in `.claude/settings.template.json` (and enforced org-wide through `managed-settings.example.json`).

| Hook | Event | What it enforces |
|---|---|---|
| `pre_tool_guard.py` | PreToolUse | Blocks direct writes to `adlc/.gates/` and `adlc/.audit/`, secrets in written content, writes outside the project, and MCP calls that are not allow-listed for the current phase. Every block is written to the audit log as `policy.blocked`. |
| `post_tool_audit.py` | PostToolUse | Records every change to a lifecycle artifact under `adlc/` as `artifact.modified` with its sha256. |

Hooks exit 2 to block a tool call; Claude Code shows the stderr reason to the model, which must then change course rather than retry.

Do not place generated runtime code here.
