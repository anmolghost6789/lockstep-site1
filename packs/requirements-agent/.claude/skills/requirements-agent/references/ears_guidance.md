# EARS Requirements Guidance

Use EARS-style phrasing for formal requirement statements when the deliverable format supports it.

**Status: preferred, not mandatory.** EARS is the default style for FRD requirements, URS requirements, and Jira acceptance criteria. However, if a user-supplied input (any file under `inputs/**` or `context/**`) explicitly declares a different preferred style (Given/When/Then, checklist, or a project-specific format), follow the user preference and record the chosen style and its source file in Open Items. The quality gate flags non-EARS acceptance criteria only when no alternative style was declared by the user.

## Preferred subjects

Use a generic system subject first, then name the component in the object or acceptance criteria:

- `The platform shall ...`
- `The system shall ...`
- `The application shall ...`
- `The service shall ...`
- `The module shall ...`

Avoid starting a formal requirement with a highly specific component name if the statement is intended to be EARS-compliant.

## Common patterns

| Pattern | Form |
|---|---|
| Ubiquitous | `The platform shall <capability>.` |
| Event-driven | `When <trigger>, the platform shall <response>.` |
| State-driven | `While <state>, the platform shall <behavior>.` |
| Optional feature | `Where <feature/context> is enabled, the platform shall <behavior>.` |
| Unwanted behavior | `If <failure/exception>, then the platform shall <mitigation>.` |

## Practical rules

1. Use `shall` for binding requirements.
2. Use measurable acceptance criteria where possible.
3. Avoid vague modifiers such as fast, easy, robust, seamless, adequate, several, many, as needed, user friendly, etc.
4. Preserve source evidence even when the source wording is vague; clean the requirement prose while citing the source accurately.
5. Do not force EARS syntax into tables that are not formal requirements, such as KPI business-rule rows or evidence quotes.
