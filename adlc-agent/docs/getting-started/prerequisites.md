# Prerequisites

## Everyone

- A GitHub repository for the product, with branch protection available.
- Python 3.10 or later, for the pack's scripts. No extra packages are needed.
- The approver teams in GitHub, ideally synced from your identity provider: product owners, architects, engineers, QA leads, release managers, security officers and waiver approvers.

## For GitHub Copilot in VS Code

- A paid GitHub Copilot plan (Business or Enterprise for teams).
- VS Code with GitHub Copilot Chat and the Lockstep extension.
- The GitHub CLI (`gh`), signed in with `gh auth login`, for opening and checking gate pull requests.

## For Claude Code

- Claude Code, in the terminal or the VS Code extension.
- The GitHub CLI as above, or `gate_mode: local` if you are not using GitHub.

## For enterprise rollout

See [Enterprise readiness](../enterprise-readiness.md): model gateway, managed settings, CI evidence for licence scans and SBOMs, log shipping and branch protection.

Next: [Quick start](quick-start.md).
