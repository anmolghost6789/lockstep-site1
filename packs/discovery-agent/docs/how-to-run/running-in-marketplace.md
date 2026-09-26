# Running DE Discovery via the hosted Guided UI

DE Discovery is listed alongside the other Data Engineering skill packages in the repository's [package overview](../../../README.md). That overview describes two ways to run any package: direct Claude Code, and a separate hosted convenience layer called the Guided UI.

## Where Discovery sits in the lifecycle

The five delivery packages follow a fixed lifecycle:

```text
Requirements -> Design -> Build -> Deploy -> Test
```

`de-discovery` is explicitly positioned **before** that lifecycle: "`de-discovery` can be used before that lifecycle to establish evidence and readiness." It is not one of the five sequential stages and it is not coordinated by `orchestrator-skill-package` the way Requirements through Test are — it is the tool you reach for when a data initiative is new, changing, or poorly understood, so that Requirements (or Design/Build directly, for a narrower change) starts from evidence instead of assumptions.

The shared package table describes it as:

| Package | Start it when you need to | Main output |
|---|---|---|
| `de-discovery` | Explore a new, changing, or poorly understood data initiative. | Versioned evidence, OKF knowledge layer, readiness assessment. |

And its first command, same as inside Claude Code directly:

| Package | First command |
|---|---|
| Discovery | `/de-discovery:discover-project` |

## What the Guided UI is (and is not)

Per the shared package guide: "The Guided UI is a separate convenience layer: it creates an isolated run workspace, supplies project context, streams progress, and reads the same package files. It does not change the package workflow or make a later phase run automatically."

In practice, that means running Discovery through the Guided UI:

- uses the same `discover-project` skill, the same `discovery-agent`, and the same deterministic `de_discovery.py` utility described in [Command reference](command-reference.md);
- does not skip or reorder the seven discovery phases in [Workflow phases](../workflow/phases.md);
- does not auto-advance into Requirements or any other package once discovery finishes — a phase completes, reports its result, and stops.

## When to use the Guided UI instead of direct Claude Code

Use the Guided UI when a non-technical user needs project/session management and controlled handoffs. Use direct Claude Code (`claude --plugin-dir .`, as in [Running in Claude Code](running-in-claude-code.md)) when you need local file control, an existing repository checkout, or want to inspect and adapt the plugin itself. Both surfaces read and write the same plugin-relative files described in [Inputs and outputs](../workflow/inputs-and-outputs.md); neither changes what the plugin actually does.
