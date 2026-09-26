# Inputs

Per-intent inputs. Cleared between cycles; artifacts under `adlc/` are kept.

| Folder | Put here |
|---|---|
| instructions/ | `intent.md` (the business goal) and any run-specific directives |
| requirements/ | BRDs, process docs, acceptance criteria |
| sources/ | System descriptions, API specs, schema docs, sample data (non-production) |

Mark each file's classification in its first line or in `inputs/classification.json` (`{"path": "confidential"}`). Unmarked files are treated as `internal`.
