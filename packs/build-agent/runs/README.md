# `runs/`

Runtime workspaces, one folder per Build Agent run. Each run is self-contained:

```
runs/run_<TIMESTAMP>/
├── .claude/            # link back to the canonical skill .claude/
├── CLAUDE.md           # per-run agent rules (snapshot)
├── README.md
├── inputs/             # snapshot of inputs at run start
├── context/            # snapshot of context/ at run start
├── state/              # session.json, phase_handoff.json, plans/, discovery/
├── outputs/            # generated DDL/DML/DQ/pipeline/tests artifacts
└── memory/             # per-run scratch memory
```

## Tracked vs ignored

- **`runs/run_<TS>/`** — gitignored. Each run can be tens of MB after deliverables; checking them in pollutes the repo.
- **`runs/_memory/`** — tracked. Durable cross-run memory the agent reads on every run: `MEMORY.md`, `CONVENTIONS.md`, `DECISIONS.md`, `PATTERN_LIBRARY.md`.
- **`runs/README.md`** — tracked (this file).

## Cleanup

There is no automatic cleanup. Delete old `run_<TS>/` folders manually when you no longer need the artifacts.
