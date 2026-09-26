# ADLC Agent: skill package for the Agentic Development Lifecycle

A skill pack that runs the six-phase ADLC in GitHub Copilot (through the Lockstep extension) and in Claude Code, with enterprise controls: named-role approval gates, separation of duties, a hash-chained audit log, policy hooks, and model and MCP allow-lists.

It follows the same package layout as the Design Agent reference (hidden shared-protocol skill, self-contained phase skills, contracts, templates, scripts, thresholded subagents, context tiers, governed memory), and adds the governance layer an enterprise client will ask for.

## Commands

| Command | What it does |
|---|---|
| `/discover-define` | Intent → AI Product Requirement Spec (AIPRS) |
| `/architect-design` | AIPRS → Agentic Solution Blueprint + Level-1 plan + ADRs |
| `/build-orchestrate` | Blueprint → working product, built unit by unit in bolts |
| `/evaluate-validate` | Product → Evaluation Scorecard against AIPRS thresholds |
| `/release-operate` | Scorecard → governed production release with runbook |
| `/observe-evolve` | Production telemetry → improvement backlog and next intent |
| `/approve-gate` | Local gate mode only: record an approve, reject or waiver decision |
| `/refresh-reference-store` | Rebuild governed reusable patterns from past approved runs |
| `/status` | Current phase, gate states, blockers, next safe action |
| `/cancel` | Stop the run, preserving the audit trail |

## Quick start

1. Copy this folder into the root of your repository.
2. Copy `.claude/settings.template.json` to `.claude/settings.json`. Platform teams can push `.claude/managed-settings.example.json` through their device management so users cannot relax it.
3. Edit `config/project_config.json` (gateway, model pins, thresholds) and `config/governance/*.json` (who can approve which gate, which MCP servers are allowed).
4. Put the business intent in `inputs/instructions/intent.md`.
5. In Claude Code, run `/discover-define`.

Requires Python 3.10+ (standard library only) for scripts and hooks.

## Documentation

- Getting started: [overview](docs/getting-started/overview.md), [prerequisites](docs/getting-started/prerequisites.md), [quick start](docs/getting-started/quick-start.md)
- How to run: [VS Code with Copilot](docs/how-to-run/running-in-vscode-copilot.md), [Claude Code](docs/how-to-run/running-in-claude-code.md), [command reference](docs/how-to-run/command-reference.md)
- Workflow: [phases](docs/workflow/phases.md), [inputs and outputs](docs/workflow/inputs-and-outputs.md), [revisions and recovery](docs/workflow/revisions-and-recovery.md)
- Reference: [configuration](docs/reference/configuration.md), [troubleshooting](docs/reference/troubleshooting-faq.md)
- Rollout: [pilot playbook](docs/pilot-playbook.md), [changelog](CHANGELOG.md)

## Enterprise readiness

See [docs/enterprise-readiness.md](docs/enterprise-readiness.md) for the control-by-control mapping a security review will want.
