# Quick start

The fastest concrete path from a clean checkout to a readiness assessment.

## 1. Install dependencies and enable the plugin

```powershell
Set-Location .\skill-packages\de-discovery
python -m pip install -r skills\discover-project\scripts\requirements.txt
claude plugin validate . --strict
claude --plugin-dir .
```

See [Prerequisites](prerequisites.md) if any of these steps fail.

## 2. Configure the project boundary

Copy and tailor the example configuration if `.de-discovery.yaml` does not already exist in your project root:

```powershell
Copy-Item skills\discover-project\assets\discovery.config.example.yaml .de-discovery.yaml
```

Edit it to set a real `project_id`, a stated `objective`, the `readiness_target` you want (`discovery-only`, `requirements-ready`, or `design-ready`), and the applicable `engagement.archetypes`. See [Configuration](../reference/configuration.md) for the full field reference.

## 3. Run `/de-discovery:discover-project`

Inside the Claude Code session started above:

```text
/de-discovery:discover-project
```

This runs the guided discovery workflow: it inspects local capability, initializes state, ingests any evidence you point it at, plans and runs a bounded investigation (including Databricks when configured), synthesizes the OKF knowledge layer, and assesses readiness against your configured target. See [Command reference](../how-to-run/command-reference.md) and [Workflow phases](../workflow/phases.md) for what happens at each step.

## 4. Review the readiness assessment

The run finishes by reporting:

- the absolute path to `knowledge/index.md` (the entrypoint for downstream agents);
- the readiness target and result (`supported`, `blocked`, or `conditional`);
- concepts changed because of new evidence;
- unresolved blockers or contradictions;
- any Databricks resources created or approvals still required;
- the research mode used and any material web evidence;
- the validation result.

Open `knowledge/index.md` to review the current-state map, the discovery boundary, and the readiness assessment before treating discovery as complete. If the result is `blocked`, resolve the named gaps and re-run `/de-discovery:discover-project` — see [Revisions and recovery](../workflow/revisions-and-recovery.md).
