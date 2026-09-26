# `context/guidance/`

Enterprise, domain, and project context the Build Agent consults when picking conventions and making implementation choices.

## Files

- **`enterprise_context.docx`** — Enterprise-wide engineering standards: naming conventions, layering rules, tooling allow-lists, security postures.
- **`domain_context.docx`** — Domain-specific guardrails (e.g., CDISC for clinical, FHIR for health, OMOP for research) that the build must respect.
- **`project_context.docx`** — Project-specific goals, scope, stakeholder priorities, and known constraints.

These are durable across runs. Update them only when the underlying enterprise/domain/project truth changes.
