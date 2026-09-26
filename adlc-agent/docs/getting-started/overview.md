# Overview

The ADLC pack runs software delivery as six phases, from a business intent to a governed production release and back to the next intent. AI agents do the planning, writing, building and testing. Named people approve each phase before the next one starts.

| Phase | Produces | Approved by |
|---|---|---|
| 01 Discover & Define | AI Product Requirement Spec (`adlc/01-aiprs.md`) | Product owner |
| 02 Architect & Design | Agentic Solution Blueprint (`adlc/02-blueprint.md`) and ADRs | Architect |
| 03 Build & Orchestrate | Working product and build ledger (`adlc/03-units.yaml`) | Engineer |
| 04 Evaluate & Validate | Evaluation Scorecard (`adlc/04-scorecard.json`) | QA lead |
| 05 Release & Operate | Governed Production Release (`adlc/05-release.md`) | Release manager (+ security officer if high risk) |
| 06 Observe & Evolve | Improvement Backlog (`adlc/06-backlog.md`) | Product owner |

## What makes it different

- **Gates are real approvals.** Each phase ends with a pull request that only the right team can approve, and the author can't approve their own work.
- **Artifacts, not chat.** Every phase writes one artifact to the repo. The next phase reads that artifact, never the conversation.
- **Everything traces.** Requirements, units, tests, metrics and backlog items carry IDs that link back to what they satisfy.
- **Governed learning.** Memory and the reference store only take in material that was approved, and never client data.

## Where it runs

- **GitHub Copilot in VS Code**, through the Lockstep extension: `@lockstep discover`, `@lockstep architect`, and so on. See [Running in VS Code with Copilot](../how-to-run/running-in-vscode-copilot.md).
- **Claude Code**, as slash commands: `/discover-define`, `/architect-design`, and so on. See [Running in Claude Code](../how-to-run/running-in-claude-code.md).

Next: [Prerequisites](prerequisites.md).
