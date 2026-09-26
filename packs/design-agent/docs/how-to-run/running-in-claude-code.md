# Running in Claude Code

## Local installation

```powershell
Set-Location .\skill-packages\design-skill-package
Copy-Item .claude\settings.template.json .claude\settings.json
python -m pip install -r .claude\skills\design-agent\scripts\requirements.txt
claude
```

Run Claude Code from the package root. The package rules, phase skills, generators, and
templates are discovered through `CLAUDE.md` and `.claude/`; opening a subfolder can cause
an incomplete workflow (missing slash commands or rules).

## Local settings

`.claude/settings.template.json` is the versioned template; `.claude/settings.json` is your
local, ignored copy (see `.gitignore`: `.claude/settings.local.json` and `CLAUDE.local.md`
are also ignored, for any future local overrides). It controls Bash command permissions and
runtime limits, and contains no client credential — see
[Prerequisites](../getting-started/prerequisites.md) for the full list of env vars and
permissions it sets.

## Input and state discipline

Keep current-run evidence under `inputs/` and durable policy/reference material under
`context/`. `outputs/00_state/` is agent control state; it is not a user deliverable and
must not be cleared to restart a phase. If `progress.json` is missing in a standalone run,
seed it once with:

```powershell
python .claude\skills\design-agent\scripts\seed_progress.py --seed
```

## Daily operating loop

1. Run `/start-design-run`. Resolve any blocking readiness findings before continuing.
2. Run `/design-architecture`. Review the canonical mappings, DQ rules, lineage, and design
   brief — this is the principal review gate before anything is rendered.
3. Run `/generate-artifacts`. Open the generated STTM and data model workbooks; they are
   the clearest handoff to Build.
4. Run `/evaluate-design`. Resolve any material findings; on `APPROVE` or
   `APPROVE_WITH_NOTES` the run closes itself (learnings captured, reference-store decision
   resolved, runtime scratch cleaned, run marked completed).

A re-run should correct the canonical design fact and regenerate the derived workbook —
never hand-patch a workbook until it disagrees with the stated design.

## Resuming an interrupted run

Every phase is idempotent on re-entry: re-invoking a phase detects existing valid artifacts
and continues from the first missing or stale step rather than restarting.

- `/start-design-run` re-entered after an interruption skips a snapshot/ingest that already
  matches current `inputs/`, and skips source discovery if `source_decisions.json` and
  `source_gap_report.md` already exist and are current.
- `/design-architecture` re-entered mid-run reads `column_mappings.json`, finds which
  tables are already written, and continues the per-table loop from the next planned
  table — it does not restart tables already fully written.
- `/generate-artifacts` re-entered after a transient failure regenerates only the
  per-layer workbooks that are missing, corrupt (below a 5 KB size threshold), or stale
  (their design source was modified after they were written).

Use `/status` first when you are not sure what state a run is in — it reads
`outputs/00_state/run_state.json` and reports the current stage, `awaiting_user_action`,
and recommended next action without changing anything.

## Reference and branding changes

Use `/refresh-reference-store` only when the governed reference material under
`context/reference/raw/` changes — it is user-invoked only because it mutates persistent
governed knowledge. Put project-specific design conventions in `context/guidance/` and
branding assets in `context/branding/`. A logo or workbook style can change presentation;
it must never alter an unconfirmed mapping or rule.

## Recovery

Use `/status` after a pause. Use `/cancel` only when you intend to stop the active
workflow — it preserves `outputs/` (deliverables and agent state) and clears only
user-provided files from `inputs/` (README.md files are preserved) after explicit
confirmation. When the source inventory changes, return to the earliest affected phase (see
[Revisions and recovery](../workflow/revisions-and-recovery.md)) and re-review the
downstream artifacts.

## Next

See [Command reference](command-reference.md) for the full command table, or
[Running via the marketplace](running-in-marketplace.md) for the hosted alternative.
