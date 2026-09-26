---
name: evaluate-validate
description: >-
  Phase 04. Prove reliability, safety and business value: automated functional tests, LLM evals
  (accuracy, relevance, safety), RAG groundedness and citations, tool and orchestration tests,
  security, performance and regression checks. Scores against AIPRS thresholds in an Evaluation
  Scorecard. Ends with gate G4 from a QA lead.
argument-hint: "[optional: eval dataset path]"
disable-model-invocation: true
allowed-tools:
  - Agent
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(python3:*)
  - Bash(npm test:*)
  - Bash(pytest:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
---

# 04 Evaluate & Validate

Purpose: produce `adlc/04-scorecard.json`, an evidence-backed verdict on whether the build meets the thresholds the product owner approved in G1.

## Required Reads
- CLAUDE.md, config/project_config.json, .claude/skills/adlc/SKILL.md
- adlc/01-aiprs.md (thresholds), adlc/02-blueprint.md, adlc/03-units.yaml
- .claude/skills/adlc/templates/04-scorecard.schema.json

## Entry gate
`adlc_gate.py check --gate G3` must exit 0.

## Rules
- **Always spawn `adlc-evaluator`.** It must not be any agent listed in `built_by` in `03-units.yaml`. Record it in `scorecard.evaluator`.
- Thresholds come only from AIPRS NFRs and success criteria. Every metric carries a `trace` to at least one `NFR-` or `SC-` ID. If the AIPRS lacks a threshold you need, stop and route back to /discover-define; do not invent one.
- Use at least `evaluation.min_eval_cases` cases. Record dataset path, version and sha256. Eval datasets must not contain restricted data.
- A metric passes only on measured evidence. Record `evidence` paths for every metric.
- The verdict is `pass` only if every metric passes. Otherwise `fail`, with the phase to route back to (03 for defects, 02 for design flaws, 01 for wrong thresholds).
- Human review is part of evaluation: sample failed and borderline cases into `adlc/.state/eval/human_review.jsonl` for the QA lead.

## Idempotent re-entry
- Scorecard exists for the current `03-units.yaml` sha256 and validation passes → skip to Human Gate.
- Build changed since scoring → re-run the full suite; never merge old and new results.

## Steps
1. `state.py start --phase evaluate-validate`.
2. Build the metric list from the AIPRS: functional, LLM (accuracy, relevance, safety), RAG (groundedness, citation precision), tool and orchestration, security and non-functional, performance (latency, cost), regression.
3. Choose the evaluator with `python3 .claude/skills/adlc/scripts/route.py phase --phase evaluate-validate --data-level <level>`; the router excludes any agent that built the code. Spawn `adlc-evaluator` on that agent.
4. The evaluator writes the suite to `adlc/evals/suite.json` (dataset, system under test, metrics each with a `trace` to an NFR or SC; never a threshold) and runs it:
   ```
   python3 .claude/skills/adlc/scripts/eval_run.py thresholds   # confirm every metric's threshold is in the approved AIPRS
   python3 .claude/skills/adlc/scripts/eval_run.py run          # writes adlc/04-scorecard.json and the human-review sample
   ```
   To show the effect of a pack or change, run the same cases with and without it: `eval_run.py compare --suite <with>.json --against <without>.json`.
5. `validate_artifact.py --phase evaluate-validate`, then `policy_check.py --phase evaluate-validate` (evaluator_independence, thresholds_from_aiprs, min_eval_cases).

## Human Gate G4
- Approver: the **QA lead** team, via CODEOWNERS for `adlc/04-scorecard.json`. The author cannot approve (GitHub blocks self-approval).
- Request (github mode): `python3 .claude/skills/adlc/scripts/gate_github.py request --gate G4 --intent <intent id>`. This opens a pull request labelled `adlc-gate-G4`.
- The approver reviews the pull request and approves it; merging passes the gate. Any later change to the artifact needs a new pull request and a new approval.
- Local mode: `adlc_gate.py request --gate G4 --summary "..."`, and the approver runs `/approve-gate G4`.

## Phase completion
6. `state.py complete --phase evaluate-validate`.
7. Summary: verdict, pass/fail per category, worst metric against threshold, route-back if failing, links.

## End Of Turn
G4 is waiting for a QA lead in the gate pull request; give its link. Recommend `/release-operate` if the verdict is pass and G4 is approved; otherwise recommend the route-back phase. Stop.

Additional context from user invocation: $ARGUMENTS
