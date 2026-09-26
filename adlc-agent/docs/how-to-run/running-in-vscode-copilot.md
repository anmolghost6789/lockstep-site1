# Running in VS Code with GitHub Copilot

## Setup

1. Install the Lockstep extension and sign in when prompted.
2. In the extension settings, set the registry URL and an API token from your registry admin. The extension installs approved packs from the registry into the workspace.
3. Open the repository. The gate panel shows each phase, its gate and who needs to approve it.

## Running phases

Use `@lockstep` in Copilot Chat:

| Chat command | Runs |
|---|---|
| `@lockstep discover` | 01 Discover & Define |
| `@lockstep architect` | 02 Architect & Design |
| `@lockstep build` | 03 Build & Orchestrate |
| `@lockstep evaluate` | 04 Evaluate & Validate |
| `@lockstep release` | 05 Release & Operate |
| `@lockstep observe` | 06 Observe & Evolve |
| `@lockstep status` | Current state and the next step |

The extension uses your Copilot models through VS Code, so there is no separate model key. Each phase shows the Copilot credits it used.

## Approving

Approvers don't need the extension. They review the gate pull request on GitHub like any other review. The extension's gate panel updates when the pull request is approved and merged.

## Limits

- Phases run one at a time per repository.
- Your Copilot admin policies apply, including which models and MCP servers are allowed.
