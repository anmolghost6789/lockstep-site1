# VALIDATION CHECKS

Checks run at four points in every phase. `scripts/validate_artifact.py` and `scripts/policy_check.py` automate the ones marked (auto); the rest are the orchestrator's responsibility before requesting a gate.

## Before a phase starts

- The previous gate is approved: its pull request is approved and merged (or, in local mode, `adlc_gate.py check` passes).
- The upstream artifact on the default branch is the version that was approved.
- Required inputs exist and are classified (see `input-folder-contract.md`).
- `run_state.json` is not `cancelled`, and no other phase is `running`.

## While writing the artifact

- Every section in the template is filled; no `{{placeholders}}`, TBD or TODO remain. (auto)
- Every new item has an ID with the phase's prefix. (auto)
- Every `Trace:` reference resolves to an upstream ID. (auto)
- No fact is restated from an upstream artifact; reference it by ID instead.

## Before requesting the gate

- Validation passes for the phase. (auto)
- The phase policy pack passes, or has a recorded, unexpired waiver. (auto)
- The context packet and `latest_summary.md` are current.
- Open questions are either resolved or listed with an owner.

## Across phases

- Every functional requirement is covered by at least one unit (02) and one evaluation metric or test (04).
- Every evaluation threshold traces to an NFR or success criterion in the approved AIPRS. (auto)
- Every release item traces to accepted units (03) and a passing scorecard (04).
- Every backlog item traces to an observation and a requirement (06). (auto)

## Validation log

Each run of the scripts writes `adlc/.state/validation/{phase}.json` and `adlc/.state/policy/{phase}.json`. Never edit these by hand. If a check is wrong for a legitimate reason, record a waiver at the gate instead of changing the result.
