# Phases

Every phase follows the same shape: check the previous gate, read the approved upstream artifact, do the work, write one artifact, validate it, run its policy pack, open its gate pull request, summarise, and stop.

## 01 Discover & Define

Turns the intent into requirements everyone can test against: personas, user stories, functional and non-functional requirements with thresholds, risks and measurable success criteria. Clarifying questions are asked in batches of up to four. Output: `adlc/01-aiprs.md`. Gate G1, product owner.

## 02 Architect & Design

Decomposes the spec into a Level-1 plan of units, and designs agent topology, model choices (approved models only), knowledge and RAG design, tools and MCP integration, and security. Significant choices become ADRs. Output: `adlc/02-blueprint.md`. Gate G2, architect.

## 03 Build & Orchestrate

Builds each unit in bolts: short build-and-test cycles. Each unit gets its own branch and pull request, reviewed by an engineer. Write tools stay in dry-run until release. Output: `adlc/03-units.yaml`. Gate G3, engineer.

## 04 Evaluate & Validate

An evaluator that did not build the code runs functional tests, LLM and RAG evaluations, tool, security, performance and regression checks, against thresholds taken only from the approved spec. Output: `adlc/04-scorecard.json`. Gate G4, QA lead.

## 05 Release & Operate

Pins every version, plans a staged rollout with numeric rollback triggers, writes the runbook, and assesses risk. High risk adds a security officer to the gate. The agent never deploys; the pipeline does, after G5. Output: `adlc/05-release.md`. Gate G5, release manager.

## 06 Observe & Evolve

Measures real outcomes against the success criteria, records incidents and drift, and turns learnings into a prioritised backlog with one proposed next intent. Output: `adlc/06-backlog.md`. Gate G6, product owner; approval starts the next cycle.

Next: [Inputs and outputs](inputs-and-outputs.md).
