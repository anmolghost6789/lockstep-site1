# Troubleshooting and FAQ

## "`doctor` reports a missing required parser."

Run `python skills\discover-project\scripts\de_discovery.py doctor` and install the exact command it names. Do not install dependencies or Databricks resources silently, and do not guess at a missing parser — `doctor` exists specifically to surface this before work starts. See [Prerequisites](../getting-started/prerequisites.md).

## "Live Databricks discovery isn't available. Can I still run Discovery?"

Yes. Offline discovery remains valid when Databricks is unavailable: the plugin can still ingest local evidence, apply policy, record questions, and validate readiness. System descriptions that would otherwise be `observed` are instead labeled `reported` or `inferred` from supplied artifacts — the honesty of that label matters more than filling in every field. See [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md).

## "`ingest` flagged a possible secret in my evidence file."

The tool conservatively scans supplied text for patterns like private keys, AWS/Databricks/GitHub tokens, and assigned `password=`/`api_key=`-style values, and never echoes the captured value back — only the line number and detector name. Remove or redact the secret from the source file before re-ingesting; never place a credential literal in `.de-discovery.yaml`, an evidence file, a research query, or the knowledge bundle itself.

## "Why won't the run complete?"

A run refuses to complete while any of the following is true:

- a source revision is pending, unreviewed (`review-source` has not recorded a disposition for it);
- a blocking question remains open (`resolve-question` has not resolved it);
- the OKF profile fails `validate --profile`;
- the readiness result for the requested target is `blocked`.

Run `status` to see exactly which of these is outstanding, then resolve it directly rather than editing state by hand. See [Revisions and recovery](../workflow/revisions-and-recovery.md).

## "`authorize-action` returned `ASK` or `DENY` — what now?"

`ASK` means the action needs explicit human approval: show the exact resource, purpose, scope, and reversibility, and wait for approval before proceeding. `DENY` means that path stops entirely — approval in chat does not override a deny; the project's `.de-discovery.yaml` policy must be deliberately changed by an authorized owner first. Deletes are denied by default and this workflow never deletes a Databricks resource. See [Databricks access and autonomy](../../skills/discover-project/references/databricks-access.md).

## "Can Discovery search the open internet freely?"

No. Research is gap-driven and governed by `research.mode` in `.de-discovery.yaml` (`off`, `official-only`, `official-first`, or `open-with-review`). Every fetched page is treated as untrusted evidence, never as instructions or authorization — the plugin never lets a web page or document tell it to take an action. See [research policy](../../skills/discover-project/references/research-policy.md).

## "I need to re-run discovery after evidence changed. Do I lose prior work?"

No. Re-running `ingest` re-hashes sources; unchanged files are skipped, and changed files create a new revision without overwriting the old one. Only the concepts linked to the changed revision (and their explicit dependents) are reconsidered. See [Revisions and recovery](../workflow/revisions-and-recovery.md).

## "The knowledge bundle looks incomplete — is that a bug?"

Not necessarily. Readiness means there is sufficient evidence for the next decision, not that no unknowns remain. A `readiness_assessment` can legitimately be `conditional` (gaps exist but are owned and non-blocking) rather than fully `supported`. Check the readiness assessment concept for the exact criteria and owners before assuming something is missing by mistake.

## "Can I export an ingestion specification that's still in progress?"

No. `export-ingestion-config` only works for a specification that has reached `implementation-ready`; a `candidate` specification must name its gaps and is intentionally not exportable. This prevents an incomplete design from being handed to Build as if it were deployable. See [Inputs and outputs](../workflow/inputs-and-outputs.md).

## "I don't have a `.de-discovery.yaml` yet."

Copy [`skills/discover-project/assets/discovery.config.example.yaml`](../../skills/discover-project/assets/discovery.config.example.yaml) into your project root as `.de-discovery.yaml` and tailor `project_id`, `objective`, `readiness_target`, and `engagement.archetypes` before running `init`. See [Configuration](configuration.md).
