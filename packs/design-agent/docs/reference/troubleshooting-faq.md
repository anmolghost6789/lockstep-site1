# Troubleshooting FAQ

## "I can't start the run without any input" — what does this mean?

`/start-design-run` applies an empty-input guard before creating any run files. Meaningful
input is a user-provided file under `inputs/<category>/`; `README.md`, `.gitkeep`, `.keep`,
and `.DS_Store` never count. If every category folder holds only those, the agent explains
where to place files and stops rather than creating an empty run. Add at least one real
file under `inputs/requirements/`, `inputs/source_inventory/`, `inputs/additional_documents/`,
or `inputs/instructions/`, then re-run `/start-design-run`.

## The agent says my inputs look identical to a previous completed run

`/start-design-run` hashes every meaningful input file and compares the set against the
last completed run's snapshot. An identical set means the same design would result — the
agent warns you and requires explicit confirmation (replace inputs, or confirm you
intentionally want to re-run with the same evidence) before it will start a duplicate run.

## Source discovery rejected or flagged a gap in a source I need

Resolve it at the source-decision level, not downstream. Either add the missing source
evidence to `inputs/source_inventory/` and re-run `/start-design-run`'s source-discovery
step, or, if the gap is acceptable, record an explicit waiver before `/design-architecture`
proceeds. `/design-architecture` designs only from `source_decisions.json` entries marked
`status: "selected"` plus explicit waivers — it will not silently substitute a rejected or
missing source.

## Two context guidance files (or a user instruction) disagree with each other

The agent asks for explicit confirmation before applying a lower-tier override — it never
silently resolves a conflict between `enterprise_context`, `domain_context`,
`project_context`, and `inputs/instructions/` user instructions. Answer the prompt (apply
the lower-tier value, keep the higher-tier value, or provide a different resolution) and
the decision is recorded so future phases stay consistent.

## A generated workbook looks wrong — how do I fix it?

Never hand-edit the workbook, `target_model_design.md`, or `plan.json` — they are
deterministic, generated views. Fix the underlying canonical fact instead:

1. Identify whether the wrong value lives in `column_mappings.json` (a mapping, grain, key
   strategy, or table metadata) or `dq_rules_design.json` (a DQ rule).
2. Correct it during `/design-architecture` (or re-enter that phase for a targeted fix).
3. Re-run `render_design_md.py` (via re-entering `/design-architecture`) if the review
   markdown needs to reflect it, then re-run `/generate-artifacts` to regenerate the
   affected layer's workbooks.
4. Re-run `/evaluate-design`.

See [Revisions and recovery](../workflow/revisions-and-recovery.md) for the full routing
table by change type.

## A run was interrupted mid-phase (network error, stream timeout, Anthropic overload)

Do not delete anything and do not restart from scratch. Run `/status` first to see the
current stage and `awaiting_user_action`. Every phase is idempotent on re-entry:

- `/start-design-run` re-entered will skip a snapshot/ingest that still matches current
  `inputs/`, and skip source discovery if it already completed.
- `/design-architecture` re-entered will read `column_mappings.json`, see which tables are
  already fully written, and continue the per-table loop from the next planned table.
- `/generate-artifacts` re-entered will regenerate only workbooks that are missing,
  corrupt, or stale relative to the design source — healthy layers are left alone.

A 32k output-token error mid-phase is a phase execution failure, not data loss — the files
already on disk are ground truth; simply re-invoke the same phase command.

## When do I need to run `/refresh-reference-store`?

Only when the governed raw reference material under `context/reference/raw/` changes (new
approved patterns added, or existing ones updated/retired). It is user-invoked only because
it mutates persistent governed knowledge shared across runs — routine design work never
triggers it implicitly. If your package instance has no `context/reference/` folder at
all, the reference-store step is simply skipped everywhere it would otherwise apply
(including the `/evaluate-design` closure-tail inclusion question).

## `/evaluate-design` came back with `NEEDS_REVISION` — what now?

The evaluation report lists concrete fixes and names the phase/file to revise (for example,
"regenerate `dq_rules_design.json` for tables X, Y — expression contains a leading `WHERE`,
then re-render and regenerate the affected layers"). The run stays open; the closure tail
(memory promotion, reference-store decision, runtime-scratch cleanup, marking the run
completed) does not run until a later `/evaluate-design` pass returns `APPROVE` or
`APPROVE_WITH_NOTES`.

## A DQ rule's SQL fails to parse

`dq_rule_expression` must be a **bare boolean predicate** — no leading `WHERE`, `SELECT`,
or `FROM`. The verifier and DQ runtime compose
`SELECT 1 FROM {table} WHERE ({filter_conditions}) AND ({dq_rule_expression})` around the
cell value themselves; a predicate that already contains `WHERE` produces a
`WHERE ... WHERE ...` syntax error downstream. Fix the expression in `dq_rules_design.json`
during `/design-architecture` and regenerate.

## Missing dependency error running a script (`openpyxl` / `sqlglot` not found)

Install the package's script dependencies from the package root:

```powershell
python -m pip install -r .claude\skills\design-agent\scripts\requirements.txt
```

`verify_artifact_semantics.py` exits with code 2 (rather than a pass/fail result) when a
dependency is missing — install and re-run rather than treating it as an evaluation
failure.

## I opened Claude Code but slash commands or rules are missing

You likely opened the wrong project root. Claude Code discovers `CLAUDE.md` and
`.claude/` from the current project folder — open `design-skill-package/` itself, not
`skill-packages/` and not a subfolder. See
[Running in Claude Code](../how-to-run/running-in-claude-code.md).

## Next

If your situation isn't covered here, run `/status` for a state-accurate summary, or see
[Revisions and recovery](../workflow/revisions-and-recovery.md) for the general recovery
rules.
