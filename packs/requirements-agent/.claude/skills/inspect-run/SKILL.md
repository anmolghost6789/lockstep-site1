---
name: inspect-run
description: Inspect and reconcile a requirements run from state, linked knowledge, final artifacts, and progress.
---

# Inspect requirements run

1. Run `knowledge_layer.py status` and `knowledge_layer.py validate`.
2. Read `progress.json`, `outputs/00_state/state.json`, and
   `outputs/00_state/knowledge/index.md`.
3. Verify selected final deliverables and the three final evaluation artifacts
   exist when state marks them complete.
4. Report input changes, source/topic counts, broken links, changed entities,
   dirty or conflicting deliverables, evaluation staleness, and the exact next
   command.

Do not repair semantic content during inspection. If deterministic state and
artifacts disagree, identify the mismatch and recommend the owning phase.
