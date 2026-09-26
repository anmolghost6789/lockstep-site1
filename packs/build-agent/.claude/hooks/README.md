# Hooks

Lifecycle hooks are optional safety rails for Claude Code.

| Hook | Purpose |
|---|---|
| `load-run-state.sh` | Injects latest run status and package-memory summary at session start. |
| `lint-output.py` | Gives a non-blocking reminder when build artifacts (DDL/DML/DQ/pipeline/tests) under `runs/` or `outputs/` appear to contain template residue or unresolved markers. |
| `quality-gate.py` | Blocks writes of generated build artifacts that still contain template tokens or `<TABLE_NAME>`-style placeholders. |
| `verify-completeness.py` | Stop-hook: checks that every selected build scope marked complete in `session.json` has at least one artifact on disk before the turn ends. |

Full quality review lives in `.claude/skills/build-agent/references/quality_standards.md` and is enforced by the `build-evaluator` subagent. These hooks are only fast, cheap pre-flight checks.
