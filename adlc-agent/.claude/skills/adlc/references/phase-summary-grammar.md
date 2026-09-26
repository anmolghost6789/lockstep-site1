# PHASE SUMMARY GRAMMAR

Every phase ends with a summary in chat. Keep it under 300 words and use this shape, so reviewers learn where to look.

```markdown
**{NN} {Phase label} complete.** {One sentence on what now exists.}

- Artifact: [adlc/{file}](adlc/{file}) ({N} IDs, {M} trace links)
- Validation: {pass | fail: first problem}
- Policy: {pass | fail: checks that failed | waived: by whom, until when}
- Gate {Gx}: waiting for **{role}** in [pull request #{n}]({url})

{Two to four lines: the decisions a reviewer should look at first, and any open questions with owners.}

Next: once {Gx} is approved, run `{/next-command}`.
```

## Rules

- Lead with what was produced, not with what the agent did.
- Numbers over adjectives: "14 stories, 22 FRs, 6 NFRs", not "comprehensive requirements".
- Name the approver role, not a person, unless the user named one.
- Link, don't paste. Never include artifact bodies.
- If the phase is blocked, say so in the first line, then what unblocks it and who can.
- If a subagent was used, one line on which and what it produced; if a threshold was not met, one line saying none was used.

## Status summaries

`/status` uses the same grammar per phase in one table: phase, status, gate, approver role, link.
