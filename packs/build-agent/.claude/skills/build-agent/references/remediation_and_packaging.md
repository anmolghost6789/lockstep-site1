# Remediation And Packaging

Read this before `/revise-build`. Packaging policy below documents how the assumptions register is structured for downstream handoff (the run no longer ends in a dedicated packaging phase — `/revise-build` is terminal once remediation is resolved).

## Remediation policy

Evaluation should produce remediation items that are concrete enough to act on directly. Each item should include:
- id
- priority: `blocker`, `must_fix`, or `should_fix`
- description
- affected tables or files
- reason
- recommended fix
- status: `open`, `in_progress`, `resolved`, or `waived`

## Revision scope policy

### Targeted revision
Use when three tables or fewer need changes.

### Broad revision
Use when more than three tables, a shared convention, or a cross-cutting pattern must change.

Broad revision requires a fresh checkpoint approval before changes begin.

## Revision iteration limit

Maximum 2 revise-evaluate cycles per run. After 2 cycles, if unresolved blockers remain, escalate to the user with a summary of what is not converging and why. The user can then waive, override, provide new guidance, or accept the current state. A third cycle requires explicit checkpoint approval.

## Packaging policy

Packaging is allowed when:
- the run has been evaluated
- blockers are resolved or explicitly waived
- the current filesystem matches the latest evaluation or revision state

Packaging must clearly state:
- what is ready
- what is still risky
- what was waived
- what assumptions remain unresolved

The assumptions register must include:
- every resolved cross-document conflict with resolution rationale — source **programmatically** from the top-level `conflicts_resolved` array in `effective_conventions.json` (written by `/analyze-inputs` Step 5). Do not recompute conflicts from memory; iterate the array.
- every instruction deviation waiver with the instruction deviated from, the source document, the rationale, and the alternative applied
- every resolved input anomaly or bug annotation with resolution reasoning — source from flagged entries in `semantic_checks.json` with `check_id` in (`M-AB-01`, `C-XDC-01`, `C-QSV-01`) and their recorded resolutions

Each conflict entry copied from `conflicts_resolved` must include: `conflict_id`, `conflicting_source_a`, `conflicting_source_b`, `conflict_description`, `resolution`, `rationale`, `priority_level_applied`. If the assumptions register entry count for conflicts does not match the length of the `conflicts_resolved` array, packaging is blocked — the mismatch indicates silent drop of a conflict finding.

Packaging with undocumented instruction deviations is blocked.

## Packaging readiness statement

Every package should end with one of:
- `ready_for_delivery`
- `ready_with_waivers`
- `not_ready`

The statement must match the evaluation verdict and any unresolved blockers.
