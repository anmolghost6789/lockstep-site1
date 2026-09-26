# Context

Root-level context contains reusable project guidance and governed reference knowledge that should be available across runs. This folder is separate from `inputs/`, which contains run-specific client input files.

Use this folder for context that should not be cleared during terminal run cleanup. Do not place run-specific user instructions here; run-specific user directives belong under `inputs/instructions/`.

## Structure

```text
context/
  branding/
  guidance/
    enterprise_context/
    domain_context/
    project_context/
  reference/
    raw/
    processed/
    _metadata.json
```

## Guidance tiers

- `context/guidance/enterprise_context/` contains enterprise-wide standards, governance, glossary, policies, naming conventions, security rules, and reusable enterprise context.
- `context/guidance/domain_context/` contains business-domain standards, domain glossary, KPIs, domain-level DQ/modeling rules, and reusable domain context. Domain means a business sub-area within the enterprise, not the enterprise's industry.
- `context/guidance/project_context/` contains project-scope guidance, platform constraints, implementation standards, naming overrides, delivery constraints, and project-level context.

## Reference

`context/reference/` is the governed organizational reference knowledge store previously named `reference_store`. Reference content is advisory only and must never override current BRD/source inventory/business rules, selected sources, enterprise/project context, or explicit human decisions.
