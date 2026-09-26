# Context

Durable guidance that applies across runs. Separate from `inputs/`, which is per-intent.

```text
context/
  guidance/
    enterprise_context/   # org-wide standards: security, AI policy, naming, glossary
    domain_context/       # business sub-area: domain glossary, KPIs, process rules
    project_context/      # this product: platform constraints, delivery rules, overrides
  reference/              # governed reference patterns (advisory only)
```

Precedence (highest first): confirmed gate decisions > approved upstream artifacts > inputs/instructions > project_context > domain_context > enterprise_context > reference > defaults.

Reference content is advisory. It never overrides current requirements or a human decision. Nothing here may contain secrets or client personal data.
