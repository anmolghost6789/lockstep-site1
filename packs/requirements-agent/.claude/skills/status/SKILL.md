---
name: status
description: Show the current requirements run status and recommended next command from deterministic state.
---

# Requirements run status

Run:

```bash
python .claude/skills/requirements-agent/scripts/knowledge_layer.py --run-dir . status
```

Read root `progress.json` for the UI recommendation. Report selected outputs,
source-change counts, knowledge page/entity counts, generation status,
evaluation status, conflicts, and the next command. Do not rescan inputs,
knowledge bodies, or deliverables for a quick status request.
