# Running DE Discovery in Claude Code

Claude Code is the canonical execution surface for this plugin. This page walks through installing, validating, running, and safely recovering a discovery session end to end.

## Install and validate the plugin

```powershell
Set-Location .\skill-packages\de-discovery
python -m pip install -r skills\discover-project\scripts\requirements.txt
claude plugin validate . --strict
claude --plugin-dir .
```

`claude plugin validate . --strict` checks the plugin manifest ([`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json)) and package structure. `claude --plugin-dir .` loads this directory as a plugin for the session, making the `de-discovery:discovery-agent` agent and the `de-discovery:discover-project` skill/command available.

Start the guided workflow with:

```text
/de-discovery:discover-project
```

You can also start the dedicated agent directly instead of the slash command:

```powershell
claude --plugin-dir . --agent de-discovery:discovery-agent
```

Run the utility's `doctor` command whenever you need to inspect parser dependencies, CLI availability, and the active configuration before starting work:

```powershell
python skills\discover-project\scripts\de_discovery.py doctor
```

## Establish the policy boundary first

Create `.de-discovery.yaml` with a real project ID, objective, readiness target, and engagement archetypes before initialization — see [Configuration](../reference/configuration.md). For restrictive environments, set `research.mode` to `official-only` with an explicit `allowed_domains` list, or to `off` to keep discovery fully offline. Do not enter client secrets in the objective, configuration, a web query, or an evidence file — the `ingest` command scans supplied text for common secret patterns, but the boundary is your responsibility going in.

## Evidence lifecycle

1. Initialize the workspace (state, evidence folders, knowledge navigation).
2. Ingest each user-provided file or input directory. The tool hashes exact bytes, scans for likely secrets, snapshots the content immutably, and extracts supported text. Unchanged inputs are skipped; changed bytes create a new source revision rather than overwriting evidence.
3. Register observations (Databricks, interview, web, decision, or other) with provenance via `register-observation`.
4. Review each changed source revision's impact with `review-source`, recording an evidence-based disposition (`applied`, `reviewed-no-change`, or `out-of-scope`).
5. Record questions with an owner and blocking status via `record-question`; resolve them with evidence via `resolve-question`.
6. Rebuild the knowledge index and run profile validation before declaring discovery complete or exporting an ingestion configuration.

See [Workflow phases](../workflow/phases.md) for the full seven-phase method and [Command reference](command-reference.md) for every underlying CLI subcommand.

## Safe recovery

Use `status` to identify changed sources, pending revisions, and open questions:

```powershell
python skills\discover-project\scripts\de_discovery.py status
```

Do not delete `.de-discovery/state.yaml` or overwrite evidence snapshots to "start over" — resume from state instead. A clean completion requires:

- no pending, unreviewed source revisions;
- no open blocking questions;
- a valid OKF profile (`validate --profile` passes);
- an unblocked readiness result for the requested target.

See [Revisions and recovery](../workflow/revisions-and-recovery.md) for the full recovery model.

## Validating changes to the plugin itself

If you are modifying this plugin (not just running a discovery engagement with it), validate both the packaging and the deterministic utility before relying on the result:

```powershell
claude plugin validate . --strict
python -m unittest discover -s tests -v
```
