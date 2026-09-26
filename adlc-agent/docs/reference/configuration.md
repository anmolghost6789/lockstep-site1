# Configuration

## `config/project_config.json`

| Key | What it controls |
|---|---|
| `gate_mode.value` | `github` (pull-request gates, default) or `local` (script gates) |
| `github` | Default branch, branch prefix, CODEOWNERS path, gate label prefix |
| `models` | Model per phase; must be in `model_policy.json` |
| `subagent_thresholds` | When each subagent is spawned |
| `bolts` | Maximum files and minutes per bolt; tests required |
| `evaluation` | Default thresholds, minimum case count, evaluator independence |
| `release` | Initial rollout %, rollback rehearsal, risk levels |
| `data_classification` | Levels and the highest level allowed in artifacts |
| `policy_packs` | Checks run before each gate |
| `audit` | Retention and export formats |

## `config/governance/gate_roles.json`

Gate approver roles, the GitHub team for each role, IdP group mapping, separation of duties, risk-based extra approvers, and waiver rules. After editing, run `setup_codeowners.py`.

## `config/governance/mcp_allowlist.json`

Each allowed MCP server, its tools and the phases it may be used in. `pre_tool_guard.py` blocks anything else in Claude Code; in Copilot, mirror this list in your Copilot MCP registry.

## `config/governance/model_policy.json`

Models approved by your AI governance board, and data levels each model may not see.

## `lockstep-pack.json`

The pack's name and description in the Lockstep registry.
