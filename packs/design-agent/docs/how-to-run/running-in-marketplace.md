# Running via the marketplace (Guided UI)

Claude Code is the canonical, direct execution surface for this package — you may launch
it from a terminal or use its VS Code/Cursor integration, as long as the active workspace
is the package root (see [Running in Claude Code](running-in-claude-code.md)).

The **Guided UI** is a separate, hosted convenience layer offered through the internal
marketplace app. It is not a different workflow: it creates an isolated run workspace,
supplies project context, streams progress, and reads the same package files that a local
Claude Code session would. It does not change the package workflow, and it does not make a
later phase run automatically — the same phase-boundary, no-auto-chaining behavior applies
whether you drive the package from a terminal or from the Guided UI.

Use the Guided UI when a non-technical user needs project/session management and
controlled handoffs between agents. Use direct Claude Code when you need local file
control, an existing repository checkout, or to inspect and adapt the package itself.

This page intentionally documents only what the shared cross-package guide
([`../../../README.md`](../../../README.md)) states about the Guided UI. If your
organization's marketplace app adds package-specific screens or controls beyond what is
described there, treat those as an operational detail of that hosted app rather than a
change to this package's commands, folder contract, or phase behavior.
