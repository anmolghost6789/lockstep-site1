# Quick start

This is the fastest path from a clean clone to a first design run. It assumes you have
already completed [Prerequisites](prerequisites.md).

## 1. Open the package root and install

```powershell
Set-Location .\skill-packages\design-skill-package
Copy-Item .claude\settings.template.json .claude\settings.json
python -m pip install -r .claude\skills\design-agent\scripts\requirements.txt
claude
```

## 2. Place reviewed requirements and source evidence

| Folder | Put this here |
|---|---|
| `inputs/requirements/` | Approved BRDs/FRDs, scope, entities, acceptance criteria. |
| `inputs/source_inventory/` | Source systems, schemas, catalogs, metadata, samples. |
| `inputs/additional_documents/` | KPIs, business rules, DQ requirements, legacy designs. |
| `inputs/instructions/` | Run-specific directives and hard boundaries, if any. |

Each folder ships a `README.md` describing what belongs there in more detail — those
`README.md` files are package guidance, not run evidence, so they are ignored by the
empty-input guard. If every input category holds only a `README.md` or placeholder file,
`/start-design-run` will not start a run; see
[Prerequisites](prerequisites.md) and
[Inputs and outputs](../workflow/inputs-and-outputs.md) for the full folder contract.

Do not place a raw production data extract, a credential, or a user-provided script that
you expect the agent to execute — user `.py` files are parsed as text only and are never
executed.

## 3. Run `/start-design-run`

```text
/start-design-run
```

This applies the empty-input guard, snapshots your inputs, ingests them into UTF-8
sidecars, publishes an input readiness report, and then — unless the readiness verdict is
blocking — selects the source universe and records any gaps in the same turn. Review
`outputs/01_inputs/input_set_evaluation_report.md` and
`outputs/02_sources/source_gap_report.md` before continuing.

## 4. Continue with the recommended next command

Every phase ends by recommending the next slash command. The full sequence is:

```text
/start-design-run -> /design-architecture -> /generate-artifacts -> /evaluate-design
```

`/design-architecture` is the most important review point — it produces the canonical
mappings, DQ rules, and lineage everything downstream depends on. See
[Phases](../workflow/phases.md) for what each phase reads and writes, and
[Command reference](../how-to-run/command-reference.md) for every available command.
