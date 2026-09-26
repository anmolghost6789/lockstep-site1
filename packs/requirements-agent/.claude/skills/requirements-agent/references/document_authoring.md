# Transactional dynamic document authoring

## Calling phase

1. Run `knowledge_layer.py prepare-generation --deliverable <ID>`. If multiple
   templates are returned, inspect their content and rerun with `--template`.
2. Return on `no_op`; stop on a manual-edit conflict.
3. Delegate the prepared transaction to the document author.
4. After the author returns valid local checks, run `commit-generation
   --deliverable <ID> --template <path>` and update progress. For a selected
   batch, wait for every author and use `finalize-generation` once instead.

## Document author

1. Run `generation-context`, read the selected dynamic template, and execute
   the exact retrieval and validation commands returned by that interface.
2. Full, targeted, and marker-migration modes all edit only the hidden sibling
   `.pending` document returned as `author_path`. Never edit the public document or
   create a work folder, plan file, candidate directory, block file, or shard.
3. On a full render, retrieve every ordered batch, then synthesize the complete
   template-shaped pending file in one model-authored `Write`; use sectional
   continuation only when the actual tool rejects that write at an output
   boundary, never from a predicted context threshold. Group repeated
   items by their natural template section, capability, epic, or graph route;
   do not use one model/tool round trip per row, story, or template section. Run
   `validate_requirements.py --file <validation_path> --json` once, repair every
   error through direct edits by the same author without creating a rewrite
   script or looping on warnings, then run `check-generation` once.
4. Return after local lint and `check-generation` pass. Never commit state,
   finalize a batch, or update progress; the calling phase owns that serial step.

The actual template selected from the user/run defines the document. Deterministic code validates
ownership, coverage, and transaction boundaries; it never defines prose or a
static document shape. Full renders cover all applicable entities. Targeted
updates may change only the returned target blocks. Marker migration may add
`RA-BLOCK` markers but may not change visible prose.

`generation-context.authoring_contract` is the marker authority for the active
transaction. Its canonical pre-commit shape is:

```markdown
<!-- RA-BLOCK START id="semantic-name" entities="FR-001,BR-002" -->
...dynamic template-shaped content...
<!-- RA-BLOCK END id="semantic-name" -->
```

Use the same unique ID in both markers. The `entities` value contains only
applicable canonical knowledge IDs. Do not add `deliverable`, `owned`, or
custom end-marker attributes; commit adds the body hash after validation.

Commit verifies that the public baseline did not change, validates the pending
document, adds block-body hashes to ownership markers, and atomically replaces
the final file. A failed author or validation leaves the last published
document byte-identical.

For speed without quality loss, synthesize related facts into the template's
required section and use one canonical representation per fact. Preserve exact
thresholds, decisions, evidence IDs, conflicts, and gaps; avoid restating the
same fact in narrative, tables, and traceability text unless the template
explicitly requires it. Summaries and traceability matrices should use stable
IDs and relationship/status fields rather than copied requirement prose.

The knowledge graph retains comprehensive context. A deliverable projects the
subset and representation its audience needs. Entity coverage requires a
correct primary representation and ownership marker, not copied entity prose or
metadata. Keep source-by-source narratives, evidence inventories, definitions,
and implementation explanations in knowledge unless the active template makes
them a required output field. Cross-references carry stable IDs instead of
duplicating the primary statement.

FRD and URS requirement rows are atomic: one independently testable obligation
and one normative `SHALL`/`SHALL NOT` clause per document-local ID. Acceptance
criteria describe observable outcomes without introducing another normative
clause. Split independently failing obligations into separate IDs while keeping
their shared graph trace.
