# Human-in-the-Loop Protocol

The chat-output templates and ETA tier table referenced in items 7–8 below live in `references/checkpoint_format.md`. Heavy phases also print a **pre-flight preview** at phase start per that file.

## Golden Rule

While a phase is running, the agent NEVER asks the user any questions. Make the best decision possible, document every assumption, and present results only after the phase completes.

Mid-phase questions destroy performance (context bloat), break automation, and slow down the user. If you cannot proceed without information, make a safe assumption and document it. If no safe assumption exists, mark the section as `[INSUFFICIENT INPUT]` and move on.

## Phase Boundary Checkpoints

After each phase completes, present to the user:

1. **Phase summary** — what was done, key metrics
2. **Decisions made** — every decision the agent made autonomously, with rationale
3. **Assumptions** — every assumption with risk level (low / medium / high)
4. **Issues requiring attention** — severity-ordered (blocker → critical → major → minor → info)
5. **Recommended next action** — the exact command to run next
6. **Context management guidance:**
   - Claude Code: "Run `/compact focus on: run_id, phase status, user decisions, next steps` before the next command"
   - Cursor: "Start a new Agent session before the next command"
7. **What's next** — preview of the next recommended command (one-line purpose, numbered steps, ETA, cost note). Render per the next-phase template in `references/checkpoint_format.md`. When the next phase is conditional, print one preview block per realistic option. When the run is terminal, replace this section with `### Run delivered — no further commands required.`
8. **Cost note** — one-line reminder to run `/cost` (Claude Code) or check Cursor billing if the user wants to track spend. Use the exact wording from `references/checkpoint_format.md`.

## User Response Options

At every phase boundary, the user can:
- **Proceed** — run the next command as recommended
- **Provide feedback** — give specific corrections or additional context; the agent applies them and re-runs the affected portion of the current phase
- **Re-run** — update inputs in `inputs/` and re-run the same command
- **Skip to a different phase** — run any command they choose

## What Qualifies as a Safe Assumption

An assumption is **safe** if:
- It follows widely accepted industry norms (e.g., SCD Type 2 for slowly changing dimensions)
- It does not make business-specific claims (e.g., "revenue target is $10M" is NOT safe)
- It does not affect data correctness in a way that could cause silent errors
- A senior engineer reviewing it would say "that is reasonable"

An assumption is **unsafe** (do not make it — use `[INSUFFICIENT INPUT]` instead):
- Business rules, join conditions, filter criteria, aggregation logic
- Compliance requirements, which regulations apply
- Data ownership, access patterns, authorization chains
- Specific thresholds, limits, SLAs, or deadlines
- Organizational structure or approval hierarchies

## Inline Notices for Outputs

When the agent makes an assumption in a generated artifact:

```markdown
> **[ASSUMPTION]** This section assumes [X] based on [evidence or industry norm].
> If incorrect, provide [specific input] and re-run this phase.
> Risk if wrong: [specific impact].
```

When the agent cannot generate a section due to missing input:

```markdown
> **[INSUFFICIENT INPUT]** This section requires [specific input type] to generate.
> What to provide: [concrete description]
> Where to add it: Place the document in `inputs/[subfolder]/` and re-run this phase.
```

## Eliminated Interaction Points

The following previously-required user interactions are eliminated. The agent handles them autonomously:

| Old Interaction | New Behavior |
|---|---|
| Output selection ("what do you want to generate?") | Agent determines what it CAN produce from inputs and produces everything |
| Kickoff questions (business problem, stakeholders, timeline) | Agent infers from input content; gaps become documented assumptions |
| Branding and formatting questions | Agent uses `inputs/branding/` if present, otherwise professional defaults |
| Layer-by-layer data requirements approval | Agent generates all layers in one pass; user reviews at phase end |
| Wave approval in build planning | Agent presents full plan at phase end |
| Broad generation approval | Agent generates everything; user reviews at phase end |
| Refinement scope confirmation | Agent classifies scope automatically; defaults to targeted |

## Questioning Style (Phase Boundary Only)

When presenting the phase boundary checkpoint:
- Lead with the most important information (blockers first, then decisions)
- Be concise — the user is reviewing, not being interviewed
- Offer a clear recommendation for next steps
- Never present more than 3 items requiring user input at once
- If the user response is ambiguous, default to the safer option and document why
