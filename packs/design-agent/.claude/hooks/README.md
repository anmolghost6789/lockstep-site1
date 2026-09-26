# Claude Code Hooks

This folder is reserved for project-scoped Claude Code hook scripts or hook-supporting files.

Initial v4.7 package state intentionally ships with no active hook scripts. Add hook scripts here only when they are required by project governance, and register them through `.claude/settings.json` or component frontmatter using Claude Code hook configuration.

Do not place generated runtime code here. Runtime scratch code belongs only under `outputs/00_state/runtime_scratch/` and must be cleaned in 09 - Close_Run.
