# `context/`

Durable, agent-shared context that lives independently of any one run. The Build Agent reads these on every run; users update them only when the underlying truth changes (new enterprise standard, new domain SOP, new branding guideline).

## Layout

- **`branding/`** — DOCX rendering preferences, fonts/colors, header/footer choices. Used by deliverable rendering steps.
- **`guidance/`** — Enterprise, domain, and project context documents. The build agent consults these when picking conventions (naming, layering, tooling).
- **`reference/`** — Reusable reference material the agent may cite or pattern-match against (e.g., Databricks patterns reference, internal style guides).

## How runs use this

When `start-build-run` snapshots inputs, it also snapshots `context/` into the run dir so the run is reproducible even if these files change later.
