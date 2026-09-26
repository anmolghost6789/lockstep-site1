# Inputs and outputs

## Inputs

Put run inputs in `inputs/` (see `.claude/skills/adlc/utilities/input-folder-contract.md`):

- `instructions/intent.md`: the business goal. Required.
- `requirements/`: BRDs, process documents, acceptance criteria.
- `sources/`: system descriptions, API specs, schemas, non-production sample data.

Mark sensitive files in `inputs/classification.json`. Anything above `internal` is referenced by path only and never copied into artifacts, prompts or memory.

Durable guidance goes in `context/guidance/` (enterprise, domain and project tiers), not in `inputs/`.

## Outputs

| Output | Where |
|---|---|
| Phase artifacts | `adlc/01-aiprs.md` … `adlc/06-backlog.md`, plus `adlc/adr/` |
| Product code | Your normal source folders, via unit pull requests |
| Run state | `adlc/.state/run_state.json`, projected to `progress.json` |
| Validation and policy results | `adlc/.state/validation/`, `adlc/.state/policy/` |
| Summaries for resuming | `adlc/.state/context_packets/` |
| Audit trail | Pull request history, GitHub audit log, `adlc/.audit/audit.jsonl` |

## IDs and traceability

Each phase has ID prefixes (`FR-001`, `UNIT-003`, `EVAL-012` and so on). Every item traces upstream with a `Trace:` line. `validate_artifact.py` rejects references that don't resolve.
