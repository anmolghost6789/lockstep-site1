# Human Gates and In-Phase Questions

## Two kinds of human touchpoint

1. **Gates (G1–G6)** end every phase. Each is a pull request containing the phase artifact. CODEOWNERS routes it to the role's GitHub team (synced from the identity provider), branch protection requires that team's approval before merging, and the next phase checks the merge. In local mode the same rules are applied by `adlc_gate.py` and `/approve-gate`. A chat message saying "approved" is not an approval.
2. **In-phase questions** (clarifications, blocker resolution) use `AskUserQuestion` and are recorded in the phase artifact with who answered.

## Why gates are not "run the next command"

Single-user skill packs treat invoking the next command as approval. That is fine for a solo engineer and fails an enterprise audit: it does not prove *who* approved, whether they had authority, whether they were independent of the author, or *what exact version* they approved. ADLC gates answer all four.

## Pull request gates: required repository settings

Run `scripts/setup_codeowners.py` once, then enable for the default branch: require a pull request, require review from Code Owners, dismiss stale approvals on new commits, require approval of the most recent push, and no bypassing.

High-risk releases also add the security officer team as a reviewer on the G5 pull request. CODEOWNERS can't make that conditional, so the orchestrator confirms an approving review from that team before recommending release, and the release checklist records it.

## Asking well

- One decision per question, 2–4 options, a recommended default, and the consequence of each option.
- Show the same options as plain text beside the picker, so the user can type an answer if the picker does not render.
- Before asking, `state.py wait --phase <id> --action <clarification|blocker_resolution>`.
- Only the orchestrator asks. Subagents return questions to the orchestrator.
- Link to evidence; never paste artifact bodies.

## Allowed in-phase questions

| Phase | Question | Options |
|---|---|---|
| 01 | Clarifying questions on intent | per question |
| 02 | Unlisted MCP server or model needed | RAISE WITH PLATFORM TEAM · DESIGN WITHOUT IT |
| 03 | Unit acceptance tests cannot pass as specified | ROUTE BACK TO 02 · ADJUST TESTS (needs architect) |
| 04 | Missing threshold in AIPRS | ROUTE BACK TO 01 · SKIP METRIC (recorded as gap) |
| 05 | Risk level disagreement | ACCEPT HIGHER LEVEL · ESCALATE |
| any | Blocker | RESOLVE · PROCEED WITH DOCUMENTED RISK (needs waiver at gate) |
