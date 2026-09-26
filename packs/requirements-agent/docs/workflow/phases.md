# Phases

## The end-to-end sequence

```text
Put evidence in inputs/
        |
/start-run -> select BRD, FRD, URS, and/or Jira; ingest and assess readiness
        |
/extract-requirements -> create evidence-backed concepts, links, assumptions, and gaps
        |
/generate-deliverables or one /generate-... command -> write selected documents
        |
/evaluate-run -> check fidelity, coverage, consistency, and traceability
        |
optional /revise-run <specific feedback> -> patch affected concepts and document blocks
        |
optional /publish-to-jira -> explicit external publication
```

| Stage | Command | Result |
|---|---|---|
| Set up | `/start-run` | Selected outputs, input snapshot, and readiness report. |
| Understand | `/extract-requirements` | Evidence-backed knowledge, assumptions, conflicts, and source links. |
| Write | `/generate-*` or `/generate-deliverables` | Selected BRD, FRD, URS, and/or Jira Story Pack. |
| Check | `/evaluate-run` | Quality score, coverage findings, and a remediation list. |
| Improve or publish | `/revise-run`, optional `/publish-to-jira` | Focused corrections or an approved Jira update. |

See [Command reference](../how-to-run/command-reference.md) for exactly what
each command reads and writes.

## The checkpoint model

Every command is an explicit checkpoint, not a step in an automatic pipeline:

1. It performs its scoped work (ingest, extract, generate, evaluate, revise,
   or publish).
2. It writes durable state — the knowledge layer, a deliverable, an evaluation
   artifact, or a publication record — through the package's deterministic
   scripts, never by hand-editing `outputs/00_state/` or `progress.json`.
3. It renders a compact, user-facing completion response: a status banner
   (complete, complete-with-attention, or blocked), a snapshot of what
   changed, links to created/updated artifacts, material findings
   (confirmed decisions, assumptions, contradictions, or conflicts), and
   exactly one recommended next command with its reason.
4. It stops. The agent never runs the next phase on its own.

This means running a later command is always your decision, made after you
had a chance to read the previous checkpoint's output. It also means a phase
skill never generates an output you did not select — `/generate-deliverables`
and every single-document `/generate-*` command only ever touch outputs
present in `state.json`'s `selected_outputs`.

### No-op and blocked results

A checkpoint is not always a change. If a phase determines nothing needs to be
redone — for example, `/start-run` sees the same inputs and same selection as
last time, or `/extract-requirements` sees no changed sources — it commits a
"no-op" result: still a successful checkpoint, stating what was checked and
why nothing changed. A "blocked" result (marked with a warning or stop banner)
means a transaction could not complete safely — a manual-edit conflict, a
failed validation, or missing required evidence — and the last known-good
public artifact is left untouched rather than partially overwritten.

## Review points

- **After extraction**, review if the agent reports material gaps or
  contradictions — these are knowledge-layer-level findings, before any
  document has been written from them.
- **After each generated document**, review it for business accuracy. The
  package preserves what evidence supports; it does not verify that the
  underlying business decision was the right one.
- **After `/evaluate-run`**, review the verdict and any blocking defects. A
  failed or incomplete quality check is a reason to revise the document, not a
  reason to hide the finding — the evaluation report always shows it.
- **Before handoff or publication**, use the checklist below.

## Review and handoff checklist

Before handing a result to Design or publishing stories:

1. Confirm each material requirement still matches the evidence and
   stakeholder intent.
2. Resolve or explicitly accept contradictions, assumptions, and open items.
3. Review scope boundaries, acceptance criteria, data requirements, and
   business rules.
4. Run `/evaluate-run` and address evidence, coverage, consistency, or
   traceability findings.
5. Hand off the reviewed document files themselves (from
   `outputs/02_deliverables/`), not private state and not a copied chat
   transcript.

## Output selection and generation order

`/start-run` asks which deliverables matter for the current run once; the
selection persists as the `selected_outputs` field in
`outputs/00_state/state.json` (set by `commit-start --selected <ID> [...]`)
and every downstream phase reads it. You may select one, several, or all four
outputs. A selection
is not a promise the evidence is sufficient — documents visibly retain open
items when required facts are missing rather than being filled in with a
guess.

| Output | Contains | Preferred use |
|---|---|---|
| BRD | Business objective, scope, stakeholders, rules, measures, risks, and open items. | Establish business agreement before solution design. |
| FRD | Functional behavior, data needs, interfaces, validations, and open items. | Explain what the solution must do. |
| URS | User-facing requirements, scenarios, controls, and acceptance-oriented needs. | Validate the solution from the user's perspective. |
| Jira Story Pack | Draft stories with traceability and acceptance criteria. | Prepare a reviewable backlog before publishing. |

The preferred generation order is **BRD -> FRD -> URS -> Jira** (a soft
dependency order), but the package never forces an unselected upstream
document to be generated as a hidden dependency — it uses the selected
template(s) and available evidence proportionally for whatever you actually
selected.
