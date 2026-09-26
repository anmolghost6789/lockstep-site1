---
name: revise-run
description: >-
  Apply inline user feedback to linked requirements knowledge and only the
  affected generated document blocks while preserving stable IDs and manual edits.
---

# Revise requirements run

Use `$ARGUMENTS` as the complete feedback. If the SDK invocation expanded it to
an empty value but the current user message contains text after `/revise-run`,
use that text unchanged. Do not ask for a second feedback channel when either
location contains feedback, and do not regenerate every selected document.

1. Run `knowledge_layer.py status`, then seed relevant entities with
   `knowledge_layer.py search-knowledge --query "$ARGUMENTS"`. Retrieve exact
   concept sections through `retrieve-context`. When feedback explicitly adds an
   existing entity to a deliverable that is not yet in its `Deliverables` field,
   call `retrieve-context --entity <ID>` without `--deliverable`, patch that
   entity's applicability through the curator, and commit extraction before
   preparing document edits. Never Read a whole topic page, the full state file,
   or the knowledge corpus.
2. Classify the feedback:
   - Semantic requirement/evidence/decision change: delegate one
   `knowledge-curator` to patch only the returned concept files and their
   necessary one-hop relations, then run
     `knowledge_layer.py commit-extract`.
   - Document-only wording/layout change: keep the knowledge unchanged. Use
     `document-blocks --deliverable <ID> --query "<section or entity>"` to
     identify only affected ownership blocks; never read the whole deliverable.
     Do not delegate a curator or run `commit-extract`: neither operation can
     improve a document-only correction, and both add avoidable work.
     Never use Read, Grep, or Edit directly on a public deliverable. Never edit a
   public deliverable in place. If the requested semantic region is outside an
   ownership block, stop with a marker-coverage conflict; do not bypass the
   pending-document transaction.
3. Run `prepare-generation --deliverable <ID> --block <block-id>` only for
   affected selected deliverables, adding `--entity <graph-id>` for the exact
   entities that authorize the correction. Stop on a manual-edit conflict.
   Use one prepare call per document with repeated `--block` / `--entity`
   arguments, and run those prepare calls serially because they update one
   shared state file. As soon as those calls return, delegate one `deliverable-author`
   per affected document in one parallel fan-out. Emit every Agent tool call in
   the same assistant turn before waiting for results. Give each author only its
   deliverable ID and the unchanged `$ARGUMENTS`; its agent contract,
   `generation-context`, and `retrieve-context` provide everything else. After
   prepare, the parent must not call `retrieve-context`, inspect or grep public
   or pending documents, restate graph content, derive replacement prose, or
   perform author work. Every author edits only its sibling pending document.
4. Validate final documents and commit their shared state serially. Mark the
   evaluation dirty and recommend `/evaluate-run`. `commit-generation` performs
   that invalidation; never call `prepare-evaluation`, invent `mark-dirty`, or
   use `invalidate-evaluation` during a normal revision. Reconcile `progress.json`
   only with `seed_progress.py --from-state --run-dir .`; never Read, Write, or
   Edit `progress.json` directly and never invent timestamps.

   If an author returns a retrieval, lint, or coverage failure, resume that same
   author once with the exact error. The parent must not retrieve context, inspect
   pending/state/script internals, or perform the repair. If the resumed author
   still fails, stop with public documents unchanged.

Never reread the whole raw corpus, create packets, or rebuild an unaffected
document. Render the revision result using
`requirements-agent/references/phase_completion.md`; then stop.
