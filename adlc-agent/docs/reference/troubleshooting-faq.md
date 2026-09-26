# Troubleshooting FAQ

## The next phase says the previous gate isn't approved, but I approved it
The pull request must be approved **and merged**, with the `adlc-gate-G#` label. Check `gate_github.py status`. If it was approved but not merged, merge it.

## I can't approve the pull request
You are probably its author, or not in the CODEOWNERS team for that artifact. GitHub blocks both on purpose. Ask a teammate in the right team.

## The phase says an upstream artifact changed after approval
Someone edited an approved artifact on the default branch. Re-run that phase and request its gate again; later phases then need fresh approvals too.

## `gate_github.py` says gh isn't available
Install the GitHub CLI and run `gh auth login`, or set `gate_mode` to `local`.

## Validation fails with "unfilled placeholder"
A template section still has `{{...}}`, TBD or TODO. Fill it or remove the row.

## A trace reference "does not exist upstream"
The ID was mistyped, or the upstream item was removed. Withdraw rather than delete upstream items so their IDs stay valid.

## The policy pack says it's waiting for CI evidence
Licence scans and SBOMs come from your CI, not the agent. Add a CI job that writes `adlc/.state/evidence/<check>.json`.

## The evaluation verdict is fail
Follow the scorecard's `route_back`: phase 03 for defects, 02 for design flaws, 01 for wrong thresholds.

## Slash commands or `@lockstep` are missing
Claude Code: check the pack is at the repo root with `.claude/skills/`. Copilot: check the Lockstep extension is installed, signed in, and has installed the pack from the registry.
