# Running via the hosted Guided UI / marketplace app

Claude Code is the canonical direct execution surface for this package (see
[Running in Claude Code](running-in-claude-code.md)). The Guided UI — the
hosted playground/marketplace app this package is listed in — is a separate
convenience layer on top of the same package. It does not change the package
workflow, and it does not make a later phase run automatically.

## What the Guided UI does

- **Creates an isolated run workspace.** Each run gets its own directory
  containing `inputs/`, `outputs/`, `memory/`, and a `.claude` link back to
  this package's own `.claude/` folder, so the exact same phase skills, agent
  definitions, and hooks you would get running Claude Code directly are used —
  the package itself is never modified by a run.
- **Supplies project context.** A project stores reusable Enterprise, Domain,
  and Project context plus branding preferences. Creating a project-backed run
  snapshots that context into the run's `context/guidance/` (and
  `context/branding/`) folders so the run has a reproducible copy, independent
  of later edits to the project.
- **Streams progress.** The UI streams the agent's turn-by-turn activity —
  text, tool calls, results — over a live connection so a non-technical user
  can watch a phase run without a terminal.
- **Reads the same package files.** The artifact panel and file browser in the
  UI read directly from the run's `outputs/` tree and other run folders; it is
  not a separate copy of the data.

## What it does not do

- It does not change the command sequence, the checkpoint model, or the
  RA-BLOCK ownership rules described in
  [Phases](../workflow/phases.md) and
  [Revisions and recovery](../workflow/revisions-and-recovery.md).
- It does not auto-advance phases. After a phase completes, the run still
  waits for an explicit next command — sent as a slash command or a matching
  natural-language request — exactly as it would in a terminal.
- It does not expose or edit the run's private state
  (`outputs/00_state/`) through the artifact panel; only the public
  `outputs/` deliverable and evaluation folders are exposed as artifacts.
- It does not weaken the Jira publication gate: `/publish-to-jira` still
  requires the same explicit in-run confirmation before any external write.

## When to use which

Use the Guided UI when a non-technical user needs project- and session-level
management, durable project context reuse across multiple runs, or a
controlled handoff experience without local file or terminal access. Use
direct Claude Code (see [Running in Claude Code](running-in-claude-code.md))
when you need local file control, an existing repository checkout, or to
inspect and adapt the package itself — for example, changing a phase skill or
a template ahead of a new kind of run.

Both surfaces produce the same run artifacts, follow the same phase contract,
and are read by the same commands (`/status`, `/inspect-run`) for
orientation and recovery.
