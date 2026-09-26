# RUNTIME CODE POLICY

## Purpose

The ADLC produces real code in /build-orchestrate. That code belongs in the repository, on the phase branch, reviewed in the pull request. Everything else the agent writes to get work done is temporary and must not accumulate in the pack or the repo.

## Allowed

- Product code, tests, prompts and agent configs for the units in the approved blueprint, on branch `adlc/{intent_id}/{unit}`.
- Temporary scripts for parsing, validation or analysis under `adlc/.state/runtime_scratch/`, with logs under `adlc/.state/logs/`.
- The documented scripts shipped in `.claude/skills/adlc/scripts/`.

## Not allowed

- Leaving scratch `.py`, `.sh`, notebooks or helper files in `.claude/`, `config/`, `inputs/`, `memory/`, `context/`, `adlc/` (outside `.state/`) or the repo root.
- Executing files from `inputs/`. Code in inputs is read as text only.
- Adding new permanent scripts to the pack without an explicit request, documentation and a version change.
- Committing anything from `runtime_scratch/`; it is git-ignored.

## Containment, not deletion

Do not delete the user's files to clean up. Move stray scratch files into `runtime_scratch/` and mention it in the phase summary.
