# URS methodology

Use a user-centered specification: state what users need and why, not internal
implementation design unless the evidence mandates it.

## Requirement rules

- Use stable `URS-*` IDs and one verifiable need per row.
- Name the grounded user/persona, outcome, source entity, criticality, and
  verification method.
- Draw actors and user groups from linked concepts. If the evidence does not
  establish them, record `[INSUFFICIENT INPUT]`; never insert default roles.
- Preserve links to related UC, KPI, BR, FR, DR, NFR, and Jira entities.
- Do not invent outcomes, thresholds, tools, regulations, or workflows.
- Keep system-access roles separate from business stakeholders who only consume
  outcomes.

## Quality checks

Each requirement must be clear, necessary, feasible, atomic, verifiable,
traceable, and implementation-neutral. Prefer EARS phrasing where it improves
precision. Name a verification method appropriate to evidence and criticality:
review, demo, inspection, analysis, test, or UAT; use specialized qualification
terminology only when governing evidence requires it.

## Domain and compliance

Use linked governing evidence. Include only applicable regulations and cite
their names and useful locators. Do not infer a regulated regime from industry
vocabulary alone. When no regime is established, say so explicitly and keep any
required confirmation visible.

Criticality must follow the impact evidenced for the requirement, not a fixed
domain-wide default. High-criticality rows need explicit risk and verification
intent.
