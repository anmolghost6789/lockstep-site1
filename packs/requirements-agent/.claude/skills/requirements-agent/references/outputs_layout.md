# Requirements output layout

`outputs/` is the single run working tree.

```text
outputs/
  00_state/
    state.json                    machine-owned hashes, status, impact, ownership
    knowledge/
      index.md                    OKF root and progressive-disclosure entry point
      log.md                      human-readable semantic change history
      sources/index.md            descriptive provenance routes
      sources/*.md                generated provenance plus projected coverage
      coverage/index.md           generated coverage navigation
      coverage/*.md               non-captured exceptions by exact input category
      <semantic route>/index.md   generated input-shaped navigation
      <semantic route>/*.md       dynamic standalone concepts or cohesive collections
  01_input_evaluation/
    input_evaluation.md           updated in place by /start-run
  02_deliverables/
    BRD.md FRD.md URS.md JIRA.md   selected final deliverables
    .BRD.pending                  exists only while BRD generation is in flight
  03_evaluation/
    evaluation_report.md
    quality_scores.json
    traceability.yaml
  04_publish_handoff/
    jira_issue_mapping.json
    jira_publish_summary.md
```

Create only the declared paths. Do not persist source scans, fragments,
evidence catalogs, extraction packets, model-authored generation packets,
routes, contracts, chunks, batches, shards, or evaluation packets.

There is no scratch tree and no promotion folder. Each in-flight deliverable
uses exactly one dot-prefixed sibling pending file. It is hidden from the
artifact shelf, validated in place, and atomically replaces the final file only
after success.
