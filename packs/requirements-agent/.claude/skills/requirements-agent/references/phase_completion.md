# Phase completion response

Read this only after a user-invoked workflow phase reaches a terminal result.
The response is a user-facing review surface, not a dump of tool output or
worker receipts.

## Timing and authority

- Render the completion response only after the phase transaction commits and
  `progress.json` is projected successfully.
- If the transaction fails, use the blocked variant and never claim completion.
- Derive counts, status, paths, conflicts, and the next command from the
  committed result and projected state. Do not rescan the corpus for narration.
- Show elapsed time or cost only when the runtime provides it. Never estimate.
- Do not claim semantic quality before `/evaluate-run` has passed.

## Presentation contract

Use compact GitHub-flavored Markdown. Adapt the wording to the phase; the labels
below describe required information, not fixed section titles.

1. Start with one status banner:

   ```markdown
   > ## ✅ <Phase> complete
   > <One sentence stating the concrete outcome and current readiness.>
   ```

   Use `⚠️` for completed-with-attention and `⛔` for blocked. Do not use a green
   banner when conflicts, failed validation, or partial publication remain.

2. Give a small snapshot table containing only meaningful committed facts, such
   as selected outputs, sources changed, concepts updated, deliverables changed,
   evaluation verdict, publication counts, or no-op status.

3. List created or updated artifacts as clickable Markdown links. For every
   artifact, state in one phrase what changed and what the user should inspect.
   Omit internal pending files, worker prompts, receipts, hashes, and state JSON
   unless they are directly relevant to a blocker.

4. Surface material findings separately:

   - confirmed decisions or coverage gains;
   - assumptions, contradictions, unresolved evidence, or manual-edit conflicts;
   - validation or evaluation findings requiring attention.

   Say `No material issues surfaced in this phase` when appropriate. Do not
   manufacture findings to fill the section.

5. End with one primary next action and its reason:

   ```markdown
   ### Continue

   `/next-command` — <why this is the correct next step>.
   ```

   Add alternatives only when the state presents a genuine branch. Never end
   with a vague offer such as “let me know what you want to do.”

## Phase-specific minimums

| Phase | Snapshot and review focus |
|---|---|
| Start | readiness, changed inputs, selected outputs, input-evaluation report, blockers |
| Extract | changed sources, concepts/pages updated, coverage, contradictions and evidence gaps |
| Generate | full/targeted/no-op per deliverable, document links, areas to review, conflicts |
| Evaluate | verdict, knowledge/output scores, traceability, blocking defects, evaluation artifacts |
| Revise | feedback applied, exact knowledge/documents changed, preserved content, evaluation staleness |
| Publish | created/updated/skipped/failed counts, Jira links, mapping/summary, partial failures |

## No-op and blocked variants

- A no-op is a successful result. Say what was checked, why nothing changed,
  which artifacts remain current, and the correct next command.
- For a blocked phase, lead with the exact blocking condition, state what
  remained unchanged, link the artifact the user should inspect when available,
  and provide the single recovery action.

Keep the response detailed enough to support review but normally below roughly
300 words. Prefer two small tables over a long wall of bullets.
