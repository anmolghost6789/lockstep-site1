# RUNTIME CODE AND CLEANUP POLICY

## Purpose

This package is instruction-driven. It must not accumulate undocumented, persistent Python scripts or helper programs in the package, input, output, template, reference-store, or root folders.

The agent may dynamically write, execute, and iterate on code at runtime when needed for parsing, validation, or Excel generation. That code is temporary run work, not package content.

## Allowed

- Write temporary runtime code only under:

```text
outputs/00_state/runtime_scratch/
```

- Use short inline Python snippets through Claude Code Bash/Python execution when appropriate.
- Keep generated runtime code long enough for debugging during the active run.
- Save execution logs under:

```text
outputs/00_state/logs/
```

## Not allowed

The agent must not leave generated `.py`, `.sh`, notebooks, scratch scripts, or undocumented helper files in:

```text
.claude/skills/design-agent/
.claude/
config/
inputs/
outputs/
.claude/skills/design-agent/templates/workbooks/
context/reference/
memory/
project root
```

The agent must not execute user-provided `.py` files from `inputs/`. User `.py` files are parsed as text/reference material only.

The agent must not add permanent pre-written runtime scripts to the skill package unless the human explicitly requests a package design change and the script is documented, versioned, and included intentionally.

## 01 - Start_Run setup

01 - Start_Run creates:

```text
outputs/00_state/runtime_scratch/
outputs/00_state/logs/
```

## 06 - Execute execution behavior

During artifact generation:
- Prefer direct, minimal runtime code snippets.
- If a reusable temporary helper is needed for the run, write it under `outputs/00_state/runtime_scratch/` only.
- Record what temporary code was created in `outputs/00_state/logs/runtime_code_manifest.json`.

Example manifest:

```json
{
  "run_id": "RUN_YYYYMMDD_HHMMSS_IST",
  "generated_runtime_files": [
    {
      "path": "outputs/00_state/runtime_scratch/generate_artifacts_tmp.py",
      "purpose": "Temporary workbook generation helper for this run",
      "created_at": "IST ISO timestamp"
    }
  ]
}
```

## No terminal cleanup (containment instead of deletion)

Runtime scratch is never deleted at run end — `outputs/00_state/runtime_scratch/` is preserved with the rest of the run folder (owner decision, consistent with the other agents). The policy is containment, not cleanup:
1. Runtime code exists ONLY under `outputs/00_state/runtime_scratch/`; the manifest records what was created and why.
2. If a generated script is found in a blocked persistent location at any point, move it to `outputs/00_state/runtime_scratch/quarantine/` immediately and note it in the manifest.
3. The evaluate-design hygiene check (below) verifies containment before the run is marked completed.

## Validation

08 - Evaluate deterministic validation should include a package/run-folder hygiene check:
- No generated runtime scripts exist in `inputs/`, `outputs/`, `.claude/skills/design-agent/`, `.claude/`, `.claude/skills/design-agent/templates/workbooks/`, `config/`, `context/reference/`, `memory/`, or project root.
- Runtime scratch content is contained under `outputs/00_state/runtime_scratch/`.

This avoids clutter and preserves the package as an instruction-driven Claude Code skill.
