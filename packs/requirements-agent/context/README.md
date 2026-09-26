# Context

`context/` contains stable material that can apply across runs. It is different from `inputs/`, which contains active source material for the current run.

| Folder | Purpose | Evidence strength |
|---|---|---|
| `guidance/` | Standing enterprise, domain, and project rules the agent should read before each run. | Governing context, not a substitute for active inputs. |
| `branding/` | Reusable document branding, logos, export preferences, tone, and style rules. | Formatting/style context only unless the user explicitly says otherwise. |
| `reference/` | Legacy implementations, prior approved examples, reusable frameworks, or external standards. | Reference material; do not override active inputs unless user instructions say so. |

Priority rule: active user instructions and active input evidence govern the run. Context guides interpretation, style, constraints, and consistency.
