# Running in Claude Code

Claude Code is the canonical, direct execution surface for this package. This
page covers opening the package correctly, setting up local configuration, the
normal day-to-day operating loop, and how to resume a run safely.

## Open the package root

```powershell
Set-Location .\skill-packages\requirements-skill-package
claude
```

Opening the package root matters: Claude Code discovers `CLAUDE.md` and
`.claude/` from the current project folder. Opening a parent folder (the
`skill-packages/` folder or the repository root) or a random subfolder can
prevent the right rules, phase skills, agent definitions, and hooks from
loading at all. If you use the VS Code or Cursor integration instead of a bare
terminal, the same rule applies — the active workspace folder must be this
package root.

## `settings.json` and `settings.local.json`

Both files are gitignored once created; only their `.template.json` sources
are versioned.

```powershell
Copy-Item .claude\settings.template.json .claude\settings.json
```

`settings.json` wires up:

- **Bash/stream timeouts** (`CLAUDE_STREAM_IDLE_TIMEOUT_MS`,
  `BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_TIMEOUT_MS`) so long knowledge/document
  operations don't time out early.
- **A `SessionStart` hook** (`.claude/hooks/load-run-state.sh`) that prints the
  active run's current step, selected outputs, completed steps, and next
  command, plus a memory-entry count, at the start of every session.
- **A `PostToolUse` hook** (`.claude/hooks/lint-output.py`) that scans any
  Markdown file written under `outputs/` and flags obvious template residue —
  stray `TODO`/`TBD` markers or unresolved `<Placeholder>` tokens — as a
  non-blocking reminder to review `quality_checks.md` before treating a
  deliverable as final.
- **A narrow allowed-command list**: `git status`/`diff` (read-only), the
  package's own `md_to_docx.py`/`validate_requirements.py` invocations, `pip
  install` of the package's own `requirements.txt`, and a `deny` list that
  blocks reading `.env`, `secrets/**`, `credentials/**`, and key/cert files
  outright.

If this run needs Jira publication, additionally:

```powershell
Copy-Item .claude\settings.local.template.json .claude\settings.local.json
```

and fill in `JIRA_PROJECT_KEY`, `JIRA_EMAIL`, `JIRA_API_TOKEN` there (or supply
them through approved environment variables instead). See
[Jira integration](../integrations/jira.md).

## Install dependencies

```powershell
python -m pip install -r .claude\skills\requirements-agent\scripts\requirements.txt
```

Do this once per environment; see [Prerequisites](../getting-started/prerequisites.md)
for what each dependency supports.

## Daily operating loop

1. Add new evidence to the correct `inputs/` category (see
   [Inputs and outputs](../workflow/inputs-and-outputs.md)).
2. Run `/start-run` when the input set or output selection changed. It
   re-ingests, re-assesses readiness, and reports what changed.
3. Read the input evaluation report. Fix blocking gaps before extraction;
   non-blocking gaps can proceed to extraction and remain visible later.
4. Run `/extract-requirements`; review reported contradictions, assumptions,
   and open items.
5. Generate only the outputs you selected — either `/generate-deliverables`
   for all of them in the preferred order, or a single `/generate-brd`,
   `/generate-frd`, `/generate-urs`, or `/generate-jira-stories` — then review
   the document(s).
6. Run `/evaluate-run` and address its findings.
7. Use `/revise-run <specific feedback>` for a reviewer change. Never hand-edit
   a generated deliverable's `RA-BLOCK` content directly; a targeted revision
   preserves everything the feedback doesn't touch, including your own manual
   edits outside a block.

Each of these commands is an explicit checkpoint — it writes state, reports
results, recommends the next command, and stops. Running the next command is
your approval to continue; the package never quietly chains phases on its
own.

## Resume without losing traceability

Use `/status` for a short answer (current phase, selected outputs, source
change counts, next command) or `/inspect-run` for a full filesystem
reconstruction when you need more detail or are recovering after an
interruption. Leave `outputs/00_state/`, `progress.json`, and the input
manifest intact between sessions — they are how the package knows what
already happened and what changed. Re-ingestion and the knowledge layer use
content hashes to identify exactly what changed and limit work to the
affected material, so resuming a stale run is cheap; deleting state to "start
fresh" is not supported and destroys the ability to do targeted, incremental
work.

## When to stop and ask for a decision

Stop and obtain a human decision when: evidence conflicts and no source
outranks the other, a source lacks an owner who can resolve an open item, a
run-local template conflicts with a required fact, or a request would publish
to Jira without explicit approval. In every one of these cases the correct
output is an open item or a blocked checkpoint — never a polished guess.
