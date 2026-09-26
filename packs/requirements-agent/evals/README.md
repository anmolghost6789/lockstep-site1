# Requirements Agent — Evaluations

Gap-first eval scenarios for the Requirements Agent skills. Each scenario is tied
to a **real failure mode** the bare model exhibits without the skill (a hallucinated
KPI target, a vague requirement laundered into the doc, a story decomposed by
pipeline stage, a revision that doesn't cascade). This is the **regression suite**:
re-run it after any change to a `SKILL.md` or reference and confirm behavior held.

This follows Anthropic's agent-skill evaluation guidance ("build evaluations first;
evaluations are your source of truth"). Anthropic ships the *format and method*, not
a runner — so the agent run is a deliberate step, and `run_evals.py` automates only
the deterministic scoring.

> **These never run during a real client run.** Nothing here is loaded by the agent
> at runtime; `evals/` is a workshop asset. Real-run performance and cost are unaffected.

## Files

- `evals.json` — the scenarios. Each has a `prompt`, input `files`, human-readable
  `expected_behavior`, machine-checkable `deterministic` assertions, and
  `qualitative_review` items (judged by `/evaluate-run` or a human).
- `fixtures/corpus/` — one small synthetic input corpus shared by all scenarios. It
  deliberately contains the failure-mode triggers: a vague "should be fast", a KPI
  named with **no** target, a 5y-vs-7y retention contradiction, PII fields, and a
  missing-feed failure path.
- `run_evals.py` — scores the `deterministic` assertions against a produced run
  output tree. Reuses `scripts/validate_requirements.py` for the `lint_clean` check.

## How to run one scenario

1. **Run the agent** on the fixture corpus (manually, or in CI with the SDK). Copy
   `fixtures/corpus/*` into a fresh run's `inputs/`, then invoke the scenario's
   `prompt` (e.g. `/start-run` then `/generate-brd`). This produces an
   `outputs/` tree.
2. **Score the deterministic checks:**
   ```bash
   python evals/run_evals.py --output-dir <path/to/outputs> --skill generate-brd
   ```
   It reports each assertion pass/fail and lists the `qualitative_review` items.
3. **Judge the qualitative items** with `/evaluate-run` (its `validator` is an
   LLM-as-judge) or a human — these are the subjective "is this actually good"
   checks that shouldn't be forced into mechanical assertions.

Validate the suite itself (no agent run needed):
```bash
python evals/run_evals.py --selftest
```

## How it serves as a regression suite

When you change a `SKILL.md` or reference:
1. Snapshot the current skill (`cp -r` the skill dir) as the baseline.
2. Re-run the affected scenarios on the fixture corpus with the new version.
3. Compare deterministic pass-rate against the baseline; re-judge the qualitative
   items. A drop is a regression — fix before merging.

Run across models (Haiku / Sonnet / Opus) when upgrading the model, per Anthropic's
guidance.

## Coverage

Scenarios target the value-producing skills (`start-run`, `extract-requirements`,
`generate-brd/frd/urs/jira-stories`, `revise-run`) where output-quality failure
modes are real. `status`/`inspect-run` are read-only orientation skills covered by
the backend contract tests; `publish-to-jira` mutates live Jira and is exercised
manually, not in the offline eval suite.
