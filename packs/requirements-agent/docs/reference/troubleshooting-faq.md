# Troubleshooting and FAQ

## Quick table

| Situation | What to do |
|---|---|
| The agent says inputs are insufficient. | Add the missing evidence to the correct input category, then re-run `/start-run` or the recommended phase. |
| A document has an open item. | Resolve it with evidence or leave it visible for a human owner; do not replace it with a guess. |
| A reviewer wants a change. | Use `/revise-run <specific feedback>` and inspect the targeted result. |
| The session was interrupted. | Run `/inspect-run`; do not recreate the output folders manually. |
| Jira is unavailable. | Continue locally. Publication is optional and must not block document generation. |
| A template changed during the run. | Review its effect before regeneration; templates shape documents but do not override evidence. |

## Insufficient inputs

**"`/start-run` reports the input evaluation as not ready" — what now?**

Read `outputs/01_input_evaluation/input_evaluation.md`. It states a verdict,
what changed, and which gaps are blocking versus non-blocking for your
selected outputs. Add the missing evidence to the folder that matches its
meaning (see [Inputs and outputs](../workflow/inputs-and-outputs.md)) — most
often `inputs/scope_and_requirements/`, `inputs/transcripts/`, or
`inputs/data_contracts/` — then re-run `/start-run`. It will re-ingest only
what changed (by content hash) and refresh the report rather than starting
over. You do not need to resolve every gap: non-blocking gaps are fine to
proceed past and will simply remain visible as open items later.

**Can I proceed with only some evidence available?**

Yes. Selecting an output is not a promise the evidence is sufficient for it —
the package will still generate the document, but with visible open items
wherever a required fact is missing, rather than inventing one.

## Open items

**A generated document has an "Open Item." Is that a bug?**

No — it is the package doing its job correctly. An open item means the
selected template requires a fact the evidence does not support. The
alternative would be inventing a business decision to make the document look
complete, which this package deliberately never does. Resolve it by adding
the missing evidence and regenerating (or running a targeted `/revise-run`),
or leave it visible for a human owner to decide.

**Why does an open item keep reappearing after I thought I fixed it?**

Confirm the new evidence actually landed in an `inputs/` category the
relevant phase reads, and that you re-ran `/extract-requirements` (not just
`/generate-*`) if the fix is a new fact rather than a wording change — new
facts must reach the knowledge layer before a document can cite them.

## Contradictions and assumptions

**The agent reports a contradiction between two sources. Why doesn't it just
pick one?**

Because picking silently would be an invented decision, and this package's
job is to surface disagreement, not resolve it on your behalf. Contradictions
and assumptions stay visible and explicit through knowledge, deliverables,
and evaluation so a reviewer can resolve them before Design turns them into a
technical decision that is much harder to unwind. Resolve it by adding an
authoritative source, editing `context/guidance/` if it is a standards
question, or explicitly instructing the run in `inputs/instructions/`.

**What's the difference between an assumption and an open item?**

An assumption is content the agent inferred (`source_role: agent_inference`)
and marked as such because it was reasonable but not directly evidenced. An
open item is a required fact the evidence simply does not supply at all.
Both must be reviewed before handoff; neither should be treated as final
without a human decision.

## Interrupted sessions

**Claude Code closed / the run was interrupted mid-phase. What do I do?**

Run `/inspect-run`. It reconstructs status from
`outputs/00_state/state.json`, the knowledge layer, `progress.json`, and the
actual deliverable/evaluation files on disk, and tells you whether anything
is inconsistent and which phase should run next. Do not manually recreate,
move, or delete anything under `outputs/00_state/` or `outputs/02_deliverables/`
to "start clean" — every in-flight write uses one hidden `.pending` sibling
file that is only swapped in atomically after validation passes, so an
interrupted phase should not have corrupted the last published artifact. If
`progress.json` itself looks stale, it can be resynchronized directly:

```bash
python .claude/skills/requirements-agent/scripts/seed_progress.py --recover
```

**`/inspect-run` says state and artifacts disagree. Is that fixable?**

Yes — it names the exact mismatch and recommends the owning phase to correct
it (for example, re-running `/extract-requirements` if a knowledge link is
broken, or `/generate-deliverables` if state marks a deliverable dirty but
the file wasn't rewritten). `/inspect-run` diagnoses; it deliberately does not
repair semantic content itself.

## Jira unavailable

**Jira credentials aren't configured yet, but I want to keep working. Can I?**

Yes. Every phase up through generating a full Jira Story Pack works with zero
Jira access — Jira is only contacted by `/publish-to-jira`, and only after
your explicit confirmation. See [Jira integration](../integrations/jira.md).

**`/publish-to-jira` fails partway through. Did it leave a mess?**

No — partial failure is always reported, never hidden.
`outputs/04_publish_handoff/jira_issue_mapping.json` records a per-story
action (`created`, `updated`, `skipped`, `failed`) with error detail. A retry
reuses the mappings that already succeeded and acts only on the unresolved
rows, so re-running `/publish-to-jira` after fixing the underlying issue does
not duplicate already-created issues.

## Templates changed mid-run

**I replaced the template in `inputs/templates/` partway through a run — what
happens?**

The next `/generate-*` (or `/generate-deliverables`) run detects more than
one template candidate or a changed one, and if it's ambiguous, asks you to
confirm which one via `--template <path>` rather than silently guessing.
Review the new template's effect — its structure, required sections, and
terminology — before regenerating: templates shape how the document is
organized, but they never override the underlying evidence. Facts already
captured in the knowledge layer are unaffected by a template change; only the
document's shape and section requirements are.

**Does changing a template invalidate the whole document?**

Only the affected deliverable is marked dirty for regeneration —
`/generate-deliverables` performs a full render or a targeted update as
appropriate, and unrelated selected outputs are untouched.

## Still stuck?

If none of the above resolves it, run `/status` for a compact orientation or
`/inspect-run` for full detail, and check the recommended next command
against [Phases](../workflow/phases.md) and
[Command reference](../how-to-run/command-reference.md). When in doubt, the
run filesystem — not the chat history — is always the source of truth.
