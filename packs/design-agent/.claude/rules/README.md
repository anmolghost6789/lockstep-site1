# Claude Code Rules

This folder is reserved for project-scoped Claude Code rule files.

Initial v4.7 package state intentionally keeps workflow procedures inside `.claude/skills/design-agent/` so they load on demand through the skill. Add `.md` rule files here only for always-on project instructions that should load independently of the workflow skill.

Do not duplicate stage, gate, utility, or template instructions from the skill package here unless the team intentionally promotes a rule to always-on behavior.
