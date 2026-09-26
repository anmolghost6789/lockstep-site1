# Claude Code Rules

Path-scoped rules for Claude Code live here as markdown files with `paths:` frontmatter. The ADLC pack ships none by default; its always-on instructions are in `CLAUDE.md` and its enforcement is in `.claude/hooks/`.

Add a rule when a folder needs its own conventions, for example `adlc-artifacts.md` with `paths: ["adlc/**"]` to remind agents to edit one section at a time and keep IDs stable.

Do not put secrets, client data or runtime code here.
