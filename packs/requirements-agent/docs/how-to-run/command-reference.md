# Command reference

Every command below is invocable two ways: the explicit slash command shown,
or a natural-language request that matches its purpose (for example, "write
the BRD" instead of `/generate-brd`, or "what's the status" instead of
`/status`). `/publish-to-jira` is the one command with real external side
effects — its natural-language trigger requires explicit publish intent, and
it still asks for in-run confirmation before writing anything to Jira.

Commands do not auto-chain. Each one is a checkpoint: it writes state, reports
what it completed or could not complete, recommends exactly one next command,
and stops. Running that next command (or asking for the equivalent in
natural language) is your approval to continue.

## `/start-run`

**Use it when:** starting a new run, or resuming after inputs or output
selection changed.

**Reads:** every file under `inputs/**` and `context/**` (via
`ingest_inputs.py`), the prior run's `inputs_manifest.json` and state if one
exists.

**Writes:**
- `inputs_manifest.json` at the run root (used by ingestion and the knowledge
  layer to detect what changed).
- `outputs/01_input_evaluation/input_evaluation.md` — the readiness report.
- Selected-output state (`outputs/00_state/state.json`'s `selected_outputs`
  field, set by `commit-start --selected <ID> [...]`) — BRD, FRD, URS, and/or
  JIRA, in any combination.
- `progress.json` projection with the recommended next command.

**What "done" looks like:** a rendered readiness report stating verdict,
changed inputs, selected outputs, and any blocking gaps, plus a recommendation
— normally `/extract-requirements`. If nothing changed since the last run
(same inputs, same selection, same report format), it commits a no-op
checkpoint instead of re-running analysis.

**Behind the scenes:** runs `ingest_inputs.py` then
`knowledge_layer.py plan-start`; if a report refresh is required, delegates a
`knowledge-curator` in "start mode" to update only
`outputs/01_input_evaluation/input_evaluation.md`, then commits with
`knowledge_layer.py commit-start --selected <ID> [...]` and projects progress
recommending `/extract-requirements`.

## `/extract-requirements`

**Use it when:** the selected evidence is ready for semantic analysis (after
a clean or acknowledged `/start-run`).

**Reads:** changed evidence (by content hash) plus only the graph
neighborhoods impacted by that change — not the whole prior knowledge layer.

**Writes:** the linked knowledge layer under `outputs/00_state/knowledge/` —
canonical concepts with stable IDs, evidence links, typed relationships,
source coverage/exception pages, and `log.md`'s human-readable change history.
This phase maintains knowledge; it does not author any deliverable.

**What "done" looks like:** a report of changed sources, concepts/pages
updated, coverage, and any contradictions or evidence gaps surfaced. If
nothing changed (`changed_sources` is empty), it is a no-op and skips
delegation entirely.

**Behind the scenes:** `knowledge_layer.py plan-extract`, then one
`knowledge-curator` performs full extraction and runs a read-only `validate`
preflight; if validation fails, the same curator is resumed once with the
exact errors. The parent commits once with `knowledge_layer.py commit-extract`
and projects progress recommending `/generate-deliverables`.

## `/generate-deliverables`

**Use it when:** you want every selected output regenerated or incrementally
updated together, in the preferred order.

**Reads:** the linked knowledge layer (not raw sources) plus each output's
run-local or package-default template.

**Writes:** every selected, currently-"dirty" deliverable under
`outputs/02_deliverables/` — any of `BRD.md`, `FRD.md`, `URS.md`, `JIRA.md`.

**What "done" looks like:** a per-output result of full render, targeted
update, or no-op, with links to the changed document(s) and areas to review.

**Behind the scenes:** `knowledge_layer.py prepare-generation --selected`
prepares all selected outputs at once; outputs marked `no_op` are skipped and
manual-edit conflicts stop that output. One `deliverable-author` per remaining
output is delegated in a single parallel fan-out. After every author passes
its local checks, the batch is validated and committed together with
`knowledge_layer.py finalize-generation`, then progress is re-seeded.

## `/generate-brd`

**Use it when:** you need only the Business Requirements Document, not a full
batch regeneration.

**Reads:** linked knowledge layer; the run's dynamic BRD template
(`inputs/templates/` if supplied, else the package default
`BRD.template.md`).

**Writes:** `outputs/02_deliverables/BRD.md` — business objective, scope,
stakeholders, use cases, business questions/KPIs, business rules, risks, and
open items (template §11 by default).

**What "done" looks like:** the BRD passes its local `validate` and
`check-generation` checks and is committed; the response states full/targeted/
no-op and what to review.

## `/generate-frd`

**Use it when:** you need functional behavior and data requirements
specifically.

**Reads:** linked knowledge layer; the run's dynamic FRD template.

**Writes:** `outputs/02_deliverables/FRD.md` — functional behavior, business
rules, data requirements, interfaces, non-functional requirements, evidence,
assumptions, and open items (template §11 by default). Uses EARS phrasing
where appropriate.

**What "done" looks like:** same commit/validation contract as `/generate-brd`,
scoped to FRD.

## `/generate-urs`

**Use it when:** you need a User Requirements Specification — needs expressed
from the user's perspective rather than the system's.

**Reads:** linked knowledge layer; the run's dynamic URS template.

**Writes:** `outputs/02_deliverables/URS.md` — user needs, personas, outcomes,
constraints, criticality, verification intent, evidence, assumptions, and open
items (template §18 by default). Does not impose a fixed specification shape
beyond what the selected template requires.

## `/generate-jira-stories`

**Use it when:** you need a draft, reviewable backlog — not publication.

**Reads:** linked knowledge layer; the run's dynamic Jira
template/framework.

**Writes:** `outputs/02_deliverables/JIRA.md` — draft stories with IDs,
fields, hierarchy, phase labels, acceptance criteria, dependencies, and
requirement traceability derived from the supplied framework/template
(template §8 Open Items by default).

**What "done" looks like:** a complete, independently valuable story pack.
Generating this document **never** contacts Jira; only `/publish-to-jira` does.

## `/evaluate-run`

**Use it when:** the selected documents are ready for a quality gate, or after
any revision that marked the prior evaluation stale.

**Reads:** every selected deliverable, the linked knowledge layer, and — via
independent re-reads — the original source evidence (the evaluator does not
trust the graph or the documents without checking sources itself first).

**Writes:**
- `outputs/03_evaluation/evaluation_report.md`
- `outputs/03_evaluation/quality_scores.json`
- `outputs/03_evaluation/traceability.yaml`

**What "done" looks like:** a verdict with separate knowledge and output
scores, a source-coverage and entity/document traceability projection, and
any blocking defects with domain, finding, basis, impact, and remediation.

**Behind the scenes:** `knowledge_layer.py prepare-evaluation` opens a
transaction (fails unless every selected deliverable is complete); one
`quality-reviewer` performs two ordered passes — independent knowledge
verification, then output verification against the now-validated
knowledge — and writes the three files under a hidden `.pending/` path; the
parent commits with `knowledge_layer.py commit-evaluation`, which rejects a
stale or inconsistent bundle and preserves the last public evaluation on
failure.

## `/revise-run <feedback>`

**Use it when:** a reviewer gave concrete feedback on generated knowledge or a
document.

**Reads:** only the knowledge/document sections implicated by the feedback —
never the whole knowledge corpus or a full deliverable.

**Writes:** targeted updates to the linked knowledge layer and/or only the
affected `RA-BLOCK`s of the affected document(s). Unrelated managed blocks,
and any manual edits outside a block, are preserved untouched. Marks
`/evaluate-run`'s prior result stale.

**What "done" looks like:** a report of exactly what feedback was applied,
which knowledge entities and document blocks changed, what was preserved, and
that evaluation should be re-run. See
[Revisions and recovery](../workflow/revisions-and-recovery.md) for the full
classification and ownership model.

## `/publish-to-jira`

**Use it when:** the Jira Story Pack (`outputs/02_deliverables/JIRA.md`) is
approved and you explicitly want to publish it — this is the only command in
the package that writes anything outside the run workspace.

**Reads:** the final Jira pack, current evaluation (if present), and any prior
`jira_issue_mapping.json` when updating an earlier publication.

**Writes:**
- `outputs/04_publish_handoff/jira_issue_mapping.json` — stable story ID to
  Jira key/URL mapping with a per-row action (`created`, `updated`, `skipped`,
  `failed`).
- `outputs/04_publish_handoff/jira_publish_summary.md` — confirmed target,
  counts, partial failures, attachment results, remediation.

**What "done" looks like:** every resolvable story upserted in dependency
order using stable IDs and the prior mapping for idempotency; partial failure
is always reported, never hidden. See [Jira integration](../integrations/jira.md)
for the credential and confirmation model.

**Gate:** immediately before the first write, the agent must show the site,
project, create/update counts, and attachment plan and get your explicit
confirmation. It never invents or caches Jira configuration in private state.

## `/status`

**Use it when:** you need a short orientation without rescanning anything.

**Reads:** `knowledge_layer.py status` output and root `progress.json` only —
never inputs, knowledge bodies, or deliverables directly.

**Reports:** selected outputs, source-change counts, knowledge page/entity
counts, generation status, evaluation status, conflicts, and the next
command.

## `/inspect-run`

**Use it when:** resuming after an interruption, or you need more detail than
`/status` gives — including a case where state and artifacts might disagree.

**Reads:** `knowledge_layer.py status` and `knowledge_layer.py validate`,
`progress.json`, `outputs/00_state/state.json`, and
`outputs/00_state/knowledge/index.md`; verifies that selected final
deliverables and the three evaluation artifacts actually exist when state
marks them complete.

**Reports:** input changes, source/topic counts, broken links, changed
entities, dirty or conflicting deliverables, evaluation staleness, and the
exact next command. It does not repair semantic content — if deterministic
state and artifacts disagree, it identifies the mismatch and recommends the
owning phase to fix it, rather than silently reconciling on its own.
