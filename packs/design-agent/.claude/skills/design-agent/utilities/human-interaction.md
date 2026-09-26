# HUMAN INTERACTION UTILITIES

## Principles

1. **Use Claude Code native structured choices.** At every discrete human-decision point, the orchestrator must call the native `AskUserQuestion` tool when available. Do not use Markdown task-list checkboxes as the primary UI.
2. **Provide explicit fallback text.** Immediately around each structured choice, display the same options in a concise yellow-themed fallback block so the user can type the option if `AskUserQuestion` is unavailable or the host cannot render it.
3. **Only the orchestrator asks humans.** Subagents must never ask the user directly. They return recommended questions/blockers to the main conversation.
4. **Be specific.** Provide context, options, consequences, recommended defaults, and evidence links. Never ask vague questions.
5. **Batch carefully.** `AskUserQuestion` supports small structured choice sets. Use one discrete decision per prompt. For clarification banks, ask focused batches and continue until the input set is strong enough.
6. **Show links, not dumps.** Provide concise summaries plus clickable links. Do not paste long reports, plans, intermediate artifacts, or workbook contents unless the user asks.
7. **Track every interaction.** Log every question, structured options, fallback text, raw human response, canonical decision, action taken, files affected, and IST timestamp.
8. **Use mid-run uploads deliberately.** Do not assume `inputs/midrun_uploads/` exists initially. During input clarification, create it only when file uploads are needed or accepted, direct the human there, then copy and parse those files into `outputs/00_state/midrun_uploads/`.
9. **Respect pre-loaded human input.** Files in `inputs/instructions/` named like `user_instructions.*` or other clearly directive files in that folder are pre-loaded explicit human input. Parse them into `user_instructions.json`; confirm every conflict with higher context tiers before applying. Persistent files under `context/guidance/` are enterprise/domain/project guidance by default, not user instructions, unless a clear run-specific directive is detected and confirmed during input standardization.
10. **Keep run state current.** Before every human decision point, update `outputs/00_state/run_state.json` to `waiting_for_user` with a valid `awaiting_user_action`. After response, update state immediately.
11. **Use IST timestamps.** All interaction logs and run-state timestamps use ISO-8601 IST with `+05:30`.
12. **Narrate delegation.** Tell the user when a subagent is spawned, when it finishes, and when the orchestrator intentionally handles work without a subagent.

## Phase boundaries are not questions

Every phase ends the same way: write the phase outputs and the state/progress completion write, give a concise summary with clickable links, recommend the next slash command, and STOP. Do not present an approval prompt, ask APPROVE/REQUEST CHANGES/REJECT, or write any approval file at a phase boundary. The user invoking the recommended next command IS the approval to proceed. If the user instead asks for changes, apply `change-impact-routing.md` and re-run the affected phase(s).

## Decision points that require AskUserQuestion

Use `AskUserQuestion` only for genuine in-phase human decisions:

```text
Stale-input confirmation at /start-design (inputs identical to a completed run): REPLACE INPUTS | CONTINUE ANYWAY
Error-grade readiness pause at /start-design (blocking input gaps before source discovery): RESOLVE GAPS | PROCEED WITH DOCUMENTED RISKS
Evaluate-design closure reference-store inclusion (only when context/reference/ exists): YES | NO | SELECTIVE
Blocker resolution when a phase cannot proceed confidently: RESOLVE BLOCKERS | PROCEED WITH DOCUMENTED RISKS
Cancel confirmation: YES CANCEL | DO NOT CANCEL
Error retry decision when needed: RETRY | STOP RUN | ASK FOR HELP
Context override confirmation: APPLY LOWER-TIER VALUE | KEEP HIGHER-TIER VALUE | PROVIDE DIFFERENT RESOLUTION
Unexpected output files present: REMOVE | KEEP AND STOP
```

If more than four options would be useful, reduce to the safest decision options above and ask follow-up details only after the user chooses.

## AskUserQuestion payload patterns

### Evaluate-design closure reference-store inclusion decision

```json
{
  "questions": [
    {
      "question": "Should any approved material from this run be proposed for the governed reference store?",
      "header": "Ref Store",
      "options": [
        {"label": "YES", "description": "Package eligible candidates using conservative governance metadata."},
        {"label": "NO", "description": "Do not add current-run material to the reference store."},
        {"label": "SELECTIVE", "description": "Ask me which candidates to include or exclude."}
      ],
      "multiSelect": false
    }
  ]
}
```

## Yellow fallback theme

For every discrete decision point, display a fallback block in chat in addition to using `AskUserQuestion`:

```text
🟨 ==================================================
🟨  DECISION - {short decision name}
🟨 ==================================================
🟨 {one-line context}
🟨 Select one option if the picker is not shown:
🟨   {OPTION 1} - {meaning}
🟨   {OPTION 2} - {meaning}
🟨 ==================================================
```

The fallback options are typed commands, not checkboxes. Accept exact typed options and natural-language equivalents only when the intent is unambiguous.

## Command taxonomy

| Canonical command | When | Meaning | Natural-language variations |
|---|---|---|---|
| SKIP | Clarification | Cannot answer; agent records risk/default | skip, do not know, move on, no idea |
| OK | Information/warning | Acknowledge | ok, got it, understood |
| RETRY | Error | Retry failed step | retry, try again |
| YES | evaluate-design ref-store | Include candidates | yes, include |
| NO | evaluate-design ref-store | Do not include candidates | no, skip |
| SELECTIVE | evaluate-design ref-store | Include only selected candidates | selective, choose items |
| PROCEED WITH DOCUMENTED RISKS | Blocker resolution | Continue despite listed risks; risks are documented | proceed, continue anyway |
| RESOLVE BLOCKERS | Blocker resolution | Provide answers/files before continuing | resolve, let me answer |

If ambiguous, ask for clarification instead of guessing.

## Input set evaluation report questions

/start-design must generate `outputs/00_state/standard_input_set/input_set_evaluation_report.md` before asking the first clarification question in a new run.

When presenting it:

```text
[/start-design] - Input Set Evaluation Report Ready

I generated the input set evaluation report:
  [Open input set evaluation report](outputs/00_state/standard_input_set/input_set_evaluation_report.md)

Input readiness: {Excellent | Good | Partial | Weak | Insufficient}
Overall confidence: {X}%
Critical blockers: {N}

I will now use the report's questions to complete and strengthen the input set.
Please answer the questions below. For any question you cannot answer, type SKIP with the question ID.
If a file is needed, I will create `inputs/midrun_uploads/`; place the file there and tell me which question it addresses.
```

Clarification questions can be free text when needed, but discrete choice questions should use `AskUserQuestion` with typed fallback.

## Low confidence or unresolved blockers: surface and ask

When critical confidence is below threshold or a critical blocker is unresolved, do not silently continue and do not run any multi-step acknowledgement ceremony. Surface the blocker plainly and ask how to proceed.

Before asking, update `outputs/00_state/run_state.json`:

```json
{
  "run_status": "waiting_for_user",
  "status": "waiting_for_user",
  "awaiting_user_action": "execution_blocker_decision",
  "updated_at": "IST ISO timestamp"
}
```

Use `AskUserQuestion`:

```json
{
  "questions": [
    {
      "question": "Confidence is below threshold or blockers remain: {one-line blocker summary}. How should I proceed?",
      "header": "Blocker",
      "options": [
        {"label": "RESOLVE BLOCKERS", "description": "Answer questions or provide files so I can improve confidence before continuing."},
        {"label": "PROCEED WITH DOCUMENTED RISKS", "description": "Continue; risks are recorded in outputs/RISK_MANIFEST.json and affected values are marked [BEST-GUESS]."}
      ],
      "multiSelect": false
    }
  ]
}
```

If the user chooses to proceed, create or update `outputs/RISK_MANIFEST.json`, mark every affected downstream value `[BEST-GUESS]`, and continue. No separate acknowledgement prompt is required — the explicit choice is the acknowledgement.

## Context-hierarchy conflict confirmation

When a lower context tier conflicts with a higher tier, the agent must ask explicit confirmation before applying. The hierarchy is:

```text
enterprise_context.json -> domain_context.json -> project_context.json -> user_instructions.json
```

Use `AskUserQuestion` with these options:

```text
APPLY LOWER-TIER VALUE
KEEP HIGHER-TIER VALUE
PROVIDE DIFFERENT RESOLUTION
```

Record the decision in `outputs/00_state/standard_input_set/human_clarifications.json` with:

```text
clarification_id
conflict_id
lower_tier_source
higher_tier_source
severity
applied_decision
tiers_skipped
timestamp_ist
```

Then update the directive status in `user_instructions.json` if applicable and increment `run_state.json.context_overrides`.

## Change requests after a phase

When the human asks for changes to already-produced artifacts (at any point), ask for the complete change list in one batch when possible, log the feedback, classify every change using `change-impact-routing.md`, select the earliest required rerun phase across the full change set, and rebuild downstream artifacts consistently. Then summarize what changed and recommend the next command as usual.

## Evaluate-design closure reference-store decision

Before asking whether to add current-run material to `context/reference/`, update run state:

```json
{
  "run_status": "waiting_for_user",
  "status": "waiting_for_user",
  "current_stage": "evaluate-design",
  "awaiting_user_action": "reference_store_decision",
  "updated_at": "IST ISO timestamp"
}
```

Use the closure `AskUserQuestion` payload above (only when context/reference/ exists; otherwise auto-skip with a note). After the answer, return run state to `in_progress`, clear `awaiting_user_action`, and apply the governed reference-store path.

## Clickable artifact links

Use relative Markdown file links from the project root:

```markdown
[Open input set evaluation report](outputs/00_state/standard_input_set/input_set_evaluation_report.md)
[Open STTM L2](outputs/05_artifacts/L2/STTM_L2.xlsx)
[Open ER Diagram](outputs/05_artifacts/ER_DIAGRAM.xlsx)
[Open evaluation report](outputs/00_state/evaluation/evaluation_report.md)
```

If the environment does not render local file links, print the exact relative path and tell the user to open it from the file tree.

## Progress updates

```text
[{phase_name}] - Progress

Completed: {what}
  - {metric}: {value}
Next: {what happens now}
```

## Run completion

```text
🟨 ==================================================
🟨  RUN COMPLETE - current-run
🟨 ==================================================
CLIENT: {name} | DOMAIN: {domain}
LAYERS: {list} | TABLES: {count}

OUTPUT: outputs/
  Files: {count} (expected: {layers x 3 + 1})
EVALUATION SCORE: {X}/100
LEARNINGS: {N} new entries
REFERENCE STORE: {added/skipped/selective}
CLEANUP: none — inputs/, outputs/00_state/, and outputs/ are preserved

Thank you!
🟨 ==================================================
```

## Subagent delegation updates

When delegating:

```text
I am delegating {stage/task} to `{subagent_name}` because {reason}. I will review its handoff before moving forward.
```

When intentionally not delegating:

```text
I am handling {stage/task} in the main orchestration context because {reason}. No subagent is needed for this step.
```

When a subagent completes:

```text
`{subagent_name}` completed {stage/task}.
Key outputs: {short list}
Status: {complete | blocked | needs_human | failed}
Next: {orchestrator action}
```
