# Revisions and recovery

## Changing something

Tell the agent every change at once. It routes the batch to the earliest phase that owns the decision (see `.claude/skills/adlc/utilities/change-impact-routing.md`). For example, a new threshold goes back to phase 01, a new unit to phase 02, and a failing test to phase 03. Every later phase built on the changed artifact is re-run and needs a fresh approval.

## When a gate is rejected

The reviewer's comments on the pull request are the change list. Re-run the phase; it revises only the affected sections and opens a new pull request.

## Resuming after an interruption

Network errors, timeouts or restarts lose nothing that was written to disk. Run `/status` to see where the run is, then re-run the current phase. Each phase skips work that is already complete and still valid.

## Safe recovery

| Situation | Do this |
|---|---|
| Phase interrupted mid-way | `/status`, then re-run the phase |
| Upstream artifact edited after approval | Re-run that phase and request its gate again |
| Gate pull request merged without the right reviewer | Fix branch protection, revert, re-request |
| Audit chain reported broken | Stop gate decisions; contact the platform team |
| Evaluation verdict is fail | Follow the scorecard's `route_back` phase |

## Cancelling

`/cancel` stops the run and keeps every artifact, gate record and audit entry. Start again with a new intent at phase 01.
