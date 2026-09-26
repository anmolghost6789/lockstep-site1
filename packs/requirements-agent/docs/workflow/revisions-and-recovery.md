# Revisions and recovery

## How `/revise-run` works

`/revise-run <specific feedback>` applies concrete reviewer feedback without
re-running earlier phases or rewriting documents wholesale. The command:

1. Reads current state (`knowledge_layer.py status`) and searches the
   knowledge layer for entities the feedback concerns
   (`search-knowledge --query "<feedback>"`), retrieving only the exact
   concept sections implicated — never the whole knowledge corpus or a full
   deliverable.
2. Classifies the feedback:
   - **Semantic requirement/evidence/decision change** — a `knowledge-curator`
     patches only the returned concept files and their necessary one-hop
     relations, then the change is committed with `commit-extract`.
   - **Document-only wording/layout change** — the underlying knowledge is
     unchanged. The affected `RA-BLOCK` ownership blocks are identified with
     `document-blocks --deliverable <ID> --query "<section or entity>"`; no
     curator is delegated and `commit-extract` is not run, because neither
     operation could improve a wording-only correction. A public deliverable
     is never edited in place with Read/Grep/Edit directly.
3. Prepares generation for only the affected selected deliverable(s)/block(s)
   (`prepare-generation --deliverable <ID> --block <block-id> [--entity <ID>]`),
   then delegates one `deliverable-author` per affected document in a single
   parallel fan-out. Each author edits only its own blocks in its sibling
   pending document.
4. Validates and commits the affected document(s)' shared state, marks the
   evaluation stale, and recommends `/evaluate-run`.

If the requested semantic region is outside any existing ownership block, the
command stops with a marker-coverage conflict rather than guessing where to
apply the change — you may need to run a generation phase first so the
relevant block exists.

## RA-BLOCK managed ownership

Every generated document section carries a machine-checked ownership marker:

```markdown
<!-- RA-BLOCK START id="semantic-name" entities="FR-001,BR-002" -->
...dynamic template-shaped content...
<!-- RA-BLOCK END id="semantic-name" -->
```

The `entities` attribute lists exactly the canonical knowledge IDs that back
that block. This is what lets `/revise-run` (and `/generate-deliverables` in
targeted mode) change only the blocks a specific piece of feedback or a
specific changed knowledge entity actually affects — full regeneration exists,
but it is not the default path for an incremental correction. Content outside
any `RA-BLOCK`, including your own manual edits to a deliverable, is preserved
untouched by any targeted update. A commit that fails validation leaves the
last published document byte-identical; nothing is partially overwritten.

## Resuming via `/status` or `/inspect-run`

Use `/status` for a fast answer: selected outputs, source-change counts,
knowledge page/entity counts, generation status, evaluation status,
conflicts, and the next command — read entirely from `progress.json` and a
`knowledge_layer.py status` call, without rescanning inputs or deliverables.

Use `/inspect-run` when you need a full reconstruction — typically after an
interrupted session, or when you suspect state and artifacts disagree. It
runs `knowledge_layer.py status` and `knowledge_layer.py validate`, reads
`progress.json`, `outputs/00_state/state.json`, and
`outputs/00_state/knowledge/index.md`, and verifies that every deliverable and
evaluation artifact `state.json` claims is complete actually exists on disk.
It reports input changes, source/topic counts, broken links, changed
entities, dirty or conflicting deliverables, and evaluation staleness — but it
does **not** repair semantic content itself. If state and artifacts disagree,
it names the mismatch and recommends the owning phase (for example,
`/extract-requirements` to repair a broken knowledge link, or
`/generate-deliverables` to regenerate a deliverable state marks dirty) rather
than silently reconciling on its own.

After an interrupted or failed model turn, `progress.json` itself can be
resynchronized from durable state with:

```bash
python .claude/skills/requirements-agent/scripts/seed_progress.py --recover
```

## The "never hand-edit `outputs/00_state/`" rule

`outputs/00_state/` (hashes, ownership, impact analysis, the knowledge graph)
and `progress.json` are machine-owned. They are written exclusively through
`knowledge_layer.py` and `seed_progress.py` inside a phase's transaction —
never by a direct `Read`/`Write`/`Edit` from the agent, and never by a human
editing the files by hand to "fix" or "reset" a run. Re-ingestion and the
knowledge layer identify exactly what changed using content hashes recorded in
this state; hand-editing or deleting it breaks that comparison and forces a
full, un-targeted re-derivation the next time any phase runs — or, worse,
silently produces an inconsistent run. If a run looks wrong, the correct tools
are `/inspect-run` to diagnose, `/status` for a quick check, and a targeted
`/revise-run` or the owning phase command to fix it — never a manual filesystem
edit under `outputs/00_state/`.
