# Pilot playbook

One team, one real intent, four to six weeks. The goal is a go / no-go decision on wider rollout, backed by evidence, and a set of learnings that make the next pilot faster.

## Before week 1: agree the basics

| Item | Owner | Done when |
|---|---|---|
| Pick the intent | Client product owner | One real backlog item, sized for four to six weeks, with a measurable outcome |
| Name the approvers | Client engineering lead | A person for each gate role: product owner, architect, engineer, QA lead, release manager, security officer |
| Record the baseline | Client + Lockstep | Current cycle time, review effort and defect rate for similar work, written down |
| Agree data capture | Client security + Lockstep | Signed note covering what metrics are shared (see below) and where they're stored |
| Access | Client platform team | GitHub admin for CODEOWNERS and branch protection, Copilot Business or Enterprise, registry token |

## Week 1: set up

1. Install the pack: `pack.py install --registry <url> --token <token> --pack adlc`.
2. Map roles to GitHub teams in `config/governance/gate_roles.json`, then `setup_codeowners.py` and apply branch protection.
3. Approve agents and models in `config/governance/agent_catalog.json` with the platform team.
4. Put the intent in `inputs/instructions/intent.md`; classify inputs in `inputs/classification.json`.
5. Dry run: `recover.py diagnose` should report a consistent, empty run.

## Weeks 2 to 4: phases 01 to 04

- Run one phase at a time. Approvers review in the pull request, never in chat.
- Write the evaluation suite during phase 01, alongside the thresholds, so phase 04 can't move the goalposts.
- Every change request goes through `recover.py change`, so rework is measured, not hidden.
- Weekly 30-minute check-in: `metrics.py show`, open gates, blockers.

## Weeks 5 to 6: release, observe, read out

- Release to a small cohort behind a flag with numeric rollback triggers; rehearse the rollback once.
- Observe for at least a week; write `06-backlog.md` against the success criteria.
- Readout with engineering and security together, using the template below.

## What to capture (with the client's written agreement)

This is how the platform gets better with every deployment. Capture only what the data-capture note allows.

| Captured | Why | Never captured |
|---|---|---|
| Phase times, approval waits, rejections, reworks (`metrics.py`) | Benchmarks across teams and clients | Artifact text, code, prompts |
| Evaluation results per metric, pass or fail | Which thresholds are realistic | Case content or client data |
| Agents and models used per phase and unit | Agent-performance data | Personal data about developers or reviewers |
| Change types and where they re-entered | Failure and recovery patterns | Anything above `internal` classification |
| Controls that caught real problems (policy blocks, rejected gates) | Proven control patterns | |
| Anonymised lessons, approved by the client | Pattern library and future domain packs | |

Push metrics with `metrics.py push` only when `config/project_config.json > telemetry.push` is true.

## Readout template

1. **Outcome:** success criteria met vs target, with the baseline.
2. **Delivery:** cycle time per phase vs baseline; approval wait; rework.
3. **Quality:** evaluation results; defects found after release.
4. **Control:** gates exercised, rejections and why, policy blocks, audit export accepted by risk?
5. **Cost:** Copilot usage per phase; people time for reviews.
6. **Decision:** go / no-go on controlled rollout, and the next two teams.
7. **Learnings:** what goes into the pattern library, with the client's approval.

## Exit criteria

- All six gates exercised by named approvers.
- Approval history exported for the risk team.
- At least one rollback rehearsed.
- Cycle time and review effort compared with the baseline.
- A written go / no-go decision.
