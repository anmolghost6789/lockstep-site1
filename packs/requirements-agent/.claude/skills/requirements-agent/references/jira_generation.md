# Jira Story Pack authoring

Use this reference only for a selected Jira output. The selected template or
supplied Jira framework defines fields, hierarchy, terminology, and presentation;
this reference defines evidence and story-quality principles.

## Configuration authority

Derive project keys, issue types, hierarchy, statuses, fields, labels, personas,
priorities, estimation, Definition of Done, and acceptance-criteria style from
linked evidence or the selected template. Never import values from another run
or silently apply a package persona, label, estimation, or workflow scheme.

When a required value is absent, use the template's supported empty-state
convention or `[INSUFFICIENT INPUT]`, and route the gap to Open Items. Do not
invent a Jira configuration merely to make the pack look complete.

## Decomposition

- Create work items around independently valuable outcomes, not document
  sections, pipeline steps, environments, or arbitrary implementation layers.
- Prefer the fewest independently valuable stories that preserve all evidenced
  outcomes. Consolidate requirements, controls, and data concerns into their
  owning outcome instead of creating parallel stories that repeat the same
  capability.
- Keep related technical, data, security, operational, and compliance concerns
  inside the owning outcome unless they deliver independent value.
- Use dependencies only when one item genuinely cannot deliver value without
  another. Keep epic-level dependency statements consistent with child items.
- Create subtasks only when the selected template or evidenced delivery process
  requires them. Derive their roles and completion conditions from that source.

## Story content

For each story, preserve:

- stable story identity and owning epic;
- grounded actor or responsible role appropriate to the story's purpose;
- capability/outcome and business or user benefit;
- source and canonical knowledge IDs;
- assumptions, constraints, dependencies, and unresolved evidence;
- observable acceptance criteria covering evidenced happy paths, failures,
  boundaries, and governing controls;
- the selected template's required Jira fields.

Use a user-story sentence only when the template calls for it. Select the actor
from evidence: an end user is valid for user-facing value; a delivery or
operational role is valid for implementation or operational work. Do not force
persona variety or a closed persona pool.

Keep the pack concise without dropping required fields or evidence:

- use one direct sentence per scalar field or table cell;
- describe the outcome once, then use IDs in acceptance, constraint, subtask,
  and traceability rows instead of repeating the same narrative;
- emit the minimum number of acceptance criteria allowed by the governing
  template or evidence that still covers happy path, boundary/failure behavior,
  and material controls;
- include only constraints and assumptions that change delivery or validation;
- when subtasks are mandatory, keep each to one outcome and one observable
  completion condition, with no copied story description.

Conciseness never authorizes dropping a template field, an applicable canonical
ID, an exact threshold, a governing control, or a real gap.

## Acceptance criteria

Acceptance criteria verify the story outcome. Use the style required by the
template or supplied framework and keep it consistent within the story.

- Make each criterion observable and independently checkable.
- Preserve exact thresholds, states, exceptions, and evidence-backed controls.
- Do not convert unsupported detail into an acceptance criterion.
- Mark a required but unresolved criterion as insufficient input and link its
  open item rather than omitting or inventing it.
- Keep project-wide Definition of Done separate from story-specific acceptance.

## Delivery readiness

Check that every story is independently understandable, appropriately scoped,
traceable, and testable. Verify hierarchy and dependencies as one graph. Leave
priority, estimate, sprint, release, labels, and custom fields unset unless
evidence or the selected template defines their valid scheme.

Generation writes `outputs/02_deliverables/JIRA.md` only. Jira publication is a
separate, explicitly confirmed workflow governed by `jira_publication.md`.
