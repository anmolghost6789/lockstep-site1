---
name: inspect-build
description: >-
  Reconstruct run status from the filesystem, reconcile drift, and recommend the next safe action. Use when the user wants a deep inspection of the build run, suspects the state is inconsistent or stale, is recovering after an interruption or context loss, or asks what actually got produced.
metadata:
  author: ZS Associates
  owner-skill: build-agent
---

# Inspect Build

## Required reads
- `runs/_memory/` files if present
- The chosen run dir at `runs/run_id_<ID>/` — read both its working state and its `outputs/`

## Goal

Recover truth from disk after interruption, handoff, or uncertainty. More thorough than `/status`.

## Step 1 — Select the run

If none exist, say so. If one, use it. If multiple, list and let user choose.

## Step 2 — Read session.json
Read `phase_handoff.json` if it exists — it shows the last completed phase and recommended next action.

Summarize: active phase, checkpoint history, progress, remediation status, packaging status.

## Step 3 — Inventory filesystem

Verify: discovery artifacts, plans, generated artifacts, evaluation, package outputs. Cross-check state against filesystem.

## Step 4 — Determine true phase

Filesystem first, state second: not started → initialized → inputs evaluated → analyzed → planned → generated → evaluated → revised → packaged.

## Step 5 — Reconcile drift

If session.json disagrees with filesystem, trust filesystem. Note drift.

## Step 6 — Report status

Present: run id, true phase, discovery status, generation completeness, evaluation verdict, remediation status, packaging readiness, recommended next action.
