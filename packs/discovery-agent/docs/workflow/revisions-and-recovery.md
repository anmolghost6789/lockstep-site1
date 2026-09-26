# Revisions and recovery

## Evidence is versioned, never silently overwritten

When a registered source changes, Discovery retains the new revision instead of replacing the old evidence. Re-running `ingest` on the same path re-hashes the bytes: unchanged inputs are skipped, and changed bytes create a new immutable source revision under `.de-discovery/evidence/sha256/<digest>/`. Old evidence is never deleted or overwritten.

## Refreshing discovery after evidence changes

To re-run or refresh discovery once new or changed evidence is available:

1. Re-run `ingest --path <path>` for every changed file or directory. The result lists concepts linked to the previous revision.
2. Reconsider only those concepts and their explicit dependents — the whole bundle is not regenerated from a single changed input (see [change impact](../../skills/discover-project/references/discovery-method.md#change-impact)).
3. Assess each pending revision's impact, then record its disposition:

   ```powershell
   python skills\discover-project\scripts\de_discovery.py review-source `
     --project-root PROJECT_ROOT `
     --revision-id <id> `
     --disposition <applied|reviewed-no-change|out-of-scope> `
     --reason "<evidence-based reason>"
   ```

4. Resolve any newly recorded questions with `resolve-question`.
5. Rebuild the knowledge index and re-validate:

   ```powershell
   python skills\discover-project\scripts\de_discovery.py rebuild-index --project-root PROJECT_ROOT
   python skills\discover-project\scripts\de_discovery.py validate --project-root PROJECT_ROOT --profile
   ```

6. Add the newest dated entry at the top of `knowledge/log.md` describing what changed, mirroring accepted, rejected, and deferred changes.

Completion is refused while any source revision remains unreviewed or any blocking question remains open — this is a deliberate gate, not a bug.

## Safe recovery after an interruption

Use `status` first to reconstruct where a run stands:

```powershell
python skills\discover-project\scripts\de_discovery.py status --project-root PROJECT_ROOT
```

This reports resumable phase state, changed sources, pending revisions, and open questions. Then resume the unfinished phase — do not restart discovery from scratch.

## What not to do

- Do not delete `.de-discovery/state.yaml` to "start over." It is the resumable project state; deleting it discards phase progress and evidence linkage, not just a cache.
- Do not overwrite an evidence snapshot under `.de-discovery/evidence/sha256/`. Snapshots are content-addressed and immutable by design — a changed file always produces a new digest and a new revision, never an in-place edit.
- Do not mark a run complete while `validate --profile` fails or a requested readiness blocker remains; repair the bundle and re-validate instead.

## A clean completion requires

- no pending, unreviewed source revisions;
- no open blocking questions;
- a valid OKF profile;
- an unblocked readiness result for the requested target.

See [Workflow phases](phases.md) for how these gates fit into the full seven-phase method, and [Evidence and readiness](../../skills/discover-project/references/evidence-and-readiness.md) for the exact readiness criteria per target.
