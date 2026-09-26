# Machine-Readable Specs

These YAML files are contracts that Claude can read when it needs a machine-readable checklist. They are not executable scripts and must not be treated as shipped runtime code. The four phase skill files (`start-design-run/SKILL.md`, `design-architecture/SKILL.md`, `generate-artifacts/SKILL.md`, `evaluate-design/SKILL.md`) plus the utility files under `.claude/skills/design-agent/utilities/` remain the human-readable source of detailed procedure.

Files:

- `artifact_contract.yaml`: expected output inventory and naming rules.
- `template_contracts.yaml`: workbook/sheet/header/summary layout rules for STTM, Data Model, DQ, and ER Diagram.
- `validation_contracts.yaml`: deterministic validation checks and severities.
- `traceability_contract.yaml`: mandatory row-level `References` rules and evidence prefixes.
