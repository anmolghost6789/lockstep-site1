---
name: status
description: >-
  Quick status check: read phase_handoff.json and session.json to tell the user where the build run stands and what to run next. Use when the user asks for status, progress, where they are, what's next, or a quick orientation on the build run.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Status

## Goal

After a `/compact` or context reset, quickly tell the user where their run stands.

## Step 1 — Find the active run

If one run exists, use it. If multiple, list. If none, say so.

## Step 2 — Read state

Read `session.json` and `phase_handoff.json`.

## Step 3 — Present

Report: Run ID, current phase, evaluation verdict (if available), key decisions, recommended next command, unresolved issues. Keep it concise.
