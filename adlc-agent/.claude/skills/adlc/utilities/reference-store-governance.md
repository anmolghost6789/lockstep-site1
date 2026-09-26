# REFERENCE STORE GOVERNANCE

## Purpose

`context/reference/` lets teams reuse proven material across runs: blueprint fragments, agent topologies, evaluation suites, prompt patterns, runbook sections. Reuse outside its valid context amplifies mistakes, so every item is tagged, and anything unapproved is advisory only.

## Layout

```text
context/reference/
  raw/                 # material dropped in for processing (organisational, past runs, explicit)
  processed/           # governed patterns, one JSON file per pattern type
```

## Required metadata per pattern

```json
{
  "pattern_id": "string",
  "pattern_type": "blueprint_fragment | agent_topology | eval_suite | prompt_pattern | runbook_section | policy_check | requirement_pattern",
  "domain": "string | unknown",
  "industry": "string | unknown",
  "client": "string | unknown",
  "reuse_scope": "global | industry | client | project | do_not_reuse_directly",
  "approval_status": "approved | provisional | rejected | deprecated",
  "sensitivity": "internal_standard | public_pattern | client_specific | restricted",
  "human_approved": false,
  "approved_for_cross_client_reuse": false,
  "created_from_run_id": "string | null",
  "last_validated_at": "ISO timestamp | null",
  "known_limitations": [],
  "do_not_apply_when": []
}
```

## Conservative defaults

Missing metadata defaults to `reuse_scope: client`, `approval_status: provisional`, `sensitivity: client_specific`, `human_approved: false`, `approved_for_cross_client_reuse: false`. Patterns built into this pack may be `global` and `approved`.

## Reuse rules

1. Current inputs, human decisions and approved upstream artifacts always win over reference material.
2. Provisional or client-specific patterns are advisory; they cannot be the only basis for a design decision.
3. Never apply a pattern across clients unless `approved_for_cross_client_reuse` is true.
4. Respect `do_not_apply_when`.
5. Deprecated and rejected patterns are never used.

## Filtering order

Filter by approval status, then sensitivity and client, then reuse scope, then industry and domain, then `do_not_apply_when`. Use what is left as suggestions, with its pattern ID cited.

## When the reference store is used

Record each consultation in `adlc/.state/reference_use.json`: pattern IDs considered, used, rejected and why. Cite used pattern IDs in the artifact's `Trace:` lines as `REF:{pattern_id}`.

## Adding material

Only /refresh-reference-store rebuilds `processed/`. New material from a run is proposed at /observe-evolve and added only after the user approves it.
