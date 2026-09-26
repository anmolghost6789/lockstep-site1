# ARTIFACT LINKING POLICY

## Purpose

Reviewers should open artifacts in one click, without chat filling up with their contents.

## Format

Relative links from the repo root:

```markdown
[Open the AIPRS](adlc/01-aiprs.md)
[Open the blueprint](adlc/02-blueprint.md)
[Open the gate pull request](https://github.com/org/repo/pull/123)
```

Never paste artifact bodies into chat unless the user asks. Summarise the key numbers and link to the file.

## Required link points

1. At the end of every phase: the artifact, its validation and policy results, and the gate pull request.
2. In `/status`: every artifact that exists, and every open gate pull request.
3. After a change is incorporated: the changed files and the re-requested gates.
4. At the end of a cycle: the backlog, the next intent, and any memory or reference-store proposals.

## Safety

A link is a pointer, not evidence. The artifact must also be recorded in run state.
