# ARTIFACT LINKING POLICY

## Purpose

Generated reports and Excel artifacts must be easy for the user to open without flooding chat with file contents. The orchestrator provides clickable Markdown links whenever a reviewable artifact is created or updated.

## Link format

Use relative file links from the project root:

```markdown
[Open input set evaluation report](outputs/00_state/standard_input_set/input_set_evaluation_report.md)
[Open STTM L2](outputs/L2/STTM_L2.xlsx)
[Open ER Diagram](outputs/ER_DIAGRAM.xlsx)
```

Do not paste full report, plan, summary, intermediate report, or workbook contents into chat unless the user explicitly asks. Summarize key metrics in chat and link to the artifact for detailed review. In-phase human decision prompts (stale-input confirmation, blocker decisions, the reference-store inclusion question) show their options in chat, with `AskUserQuestion` as the primary decision UI and the yellow typed fallback when structured choices are unavailable.

## Required link points

1. After /start-design writes or refreshes `input_set_evaluation_report.md`, present a clickable link to it before asking clarification questions.
2. During `/status`, show links to the evaluation report and generated outputs if they exist.
3. After /generate-artifacts, show a grouped link list for every generated output workbook and any `RISK_MANIFEST.json`.
4. After change incorporation, show links to changed files and the updated summary.
5. At run completion, show links to the output folder, ER Diagram, final evaluation report, and any learning/reference-store candidate reports.

## Safety

Links are only pointers to local project files. They are not evidence by themselves. The artifact must also be recorded in run state, manifests, or handoffs as appropriate.
