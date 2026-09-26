# ADLC REPOSITORY LAYOUT

What lives where once a run is under way. Folders marked (git-ignored) never reach a pull request.

```text
adlc/
  01-aiprs.md               # G1: product owner
  02-blueprint.md           # G2: architect
  adr/ADR-NNN-*.md          # decisions from phase 02
  03-units.yaml             # G3: engineer (plus per-unit code pull requests)
  04-scorecard.json         # G4: QA lead
  05-release.md             # G5: release manager (+ security officer if high risk)
  06-backlog.md             # G6: product owner
  .gates/                   # local-mode gate records (written by adlc_gate.py)
  .audit/audit.jsonl        # local-mode hash-chained audit log
  .state/                   # run ledger, packets, handoffs, validation, evidence
    runtime_scratch/        # (git-ignored) temporary code
    eval/raw/               # (git-ignored) raw evaluation output
progress.json               # UI projection for the extension
.github/CODEOWNERS          # maps each adlc/ artifact to its approver team
```

## Branches

- Phase artifacts: `adlc/{intent_id}/{NN}-{phase}`, one pull request per phase.
- Build units: `adlc/{intent_id}/unit-{NNN}`, one pull request per unit.

## What each pull request contains

Only the phase artifact, its companions (such as ADRs) and the matching `adlc/.state/` updates. Code changes go in unit pull requests, never in a phase pull request.
