# Package Memory

This folder stores durable Data Artifact Generation Agent knowledge that persists across runs. It is read once at the start of a run and written back only at phase boundaries when a durable, reusable learning is confirmed.

## Files

- `MEMORY.md` — reusable facts, project-agnostic conventions, and durable learnings.
- `CONVENTIONS.md` — writing, naming, formatting, and delivery conventions.
- `DECISIONS.md` — decisions that should persist across runs unless superseded.
- `PATTERN_LIBRARY.md` — high-value reusable section or artifact patterns.

Seed copies of the four files live in `.claude/skills/design-agent/templates/memory/`. If the files are empty at the start of a run, use those as the expected format before writing the first entries.

## Promotion rules

Promote only information that is reusable, safe, concise, and validated by a run or user feedback.

Do not promote raw notes, transcripts, secrets, copied client content, PII/PHI, one-off assumptions, temporary observations, large dumps, or unverified guesses.
