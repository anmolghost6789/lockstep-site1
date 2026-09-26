# Progress contract

`progress.json` is the run-root UI projection. The agent never hand-writes it.
`seed_progress.py` derives it from `outputs/00_state/state.json` and the static
workflow manifest.

At run creation:

```bash
python .claude/skills/requirements-agent/scripts/seed_progress.py --seed
```

At phase start:

```bash
python .claude/skills/requirements-agent/scripts/seed_progress.py \
  --from-state --running <step-id>
```

At phase completion, after state and required final artifacts commit:

```bash
python .claude/skills/requirements-agent/scripts/seed_progress.py \
  --from-state --completed <step-id> \
  --next-command-name <command-without-leading-slash> \
  --next-why "<one-line recommendation>"
```

After an interrupted or failed model turn:

```bash
python .claude/skills/requirements-agent/scripts/seed_progress.py --recover
```

The script owns step status and timestamps. The agent owns only the next-command
recommendation. For parallel generation, repeat `--running` for active output
step IDs, then commit each completed deliverable and project progress again.
