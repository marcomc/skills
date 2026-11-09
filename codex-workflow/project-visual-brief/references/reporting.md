# Reporting

## Evidence model

Keep a small private model before drawing. Each work item has a stable ID,
plain-language outcome, workstream, development readiness, execution state, related chat IDs/titles,
runtime observation, source turn references and observation time. Record
dependency IDs, confirmed/proposed status, completion evidence, blocker owner
and release condition only when supported. A work item can span several chats;
one chat can cover several work items.

Retain conflicting claims until a later decision or a direct check resolves
them. Use “uncertain” instead of blending them into a confident status.

## Development versus execution

Answer two independent questions on each capability: what is already built,
and what is its execution doing now? Keep chat runtime as a third observation
in details. A waiting capability can be unbuilt, partly built, or implemented.

Use evidence-scoped readiness: planned, building, partial, implemented, verified
or unknown. “Implemented” identifies concrete functionality already present;
integration, deployment and verification gaps remain explicit. “Verified” needs
the relevant acceptance evidence and its scope, rather than a file or a test
count alone. A protocol/checklist is prepared procedure, not working automation.
For a mixed workflow, use partial and name the implemented parts.

Activity details answer “What exists?” and “What remains?” before the next step.
Differentiate missing implementation, missing integration, missing input and
missing validation. Keep these unknown rather than inferring them from waiting.
For decisions or outcome-only milestones, development can be not applicable;
label their decision/result state without inventing a software-build stage.

## Default status flow

Open a project-progress update with a compact top-to-bottom status flow using
colored rectangular nodes, short localized labels and a small legend. Mermaid
`flowchart TB` is sufficient when nodes and edges explain the static status.
Use the palette and example in [Visual design](visual-design.md#default-progress-flow).
Keep one primary vertical path and at most two readable parallel branches.
Group large projects into an overview and separate workstream maps instead of
shrinking text or repeating the same state in a table below the diagram.

Add only useful context: observation time, material gaps, a real blocker and the
next action. Expand source evidence or technical details when needed. Use an
interactive hybrid for requested drill-down or when the static map would become
unreadable; retain development, execution and attention as separate facts.
A different explicit user format takes precedence. Single facts and unrelated
answers do not need a project diagram.

| View | Answers | Use |
| --- | --- | --- |
| Outcome/dependency map | What contributes to the next useful milestone, and what unlocks it? | Default vertical status map. Show a confirmed dependency as a solid arrow and a tentative dependency as a labeled dotted arrow. |
| Compact work-state view | What is running, waiting, blocked, finished or needs the user? | Embed concise labels in the status nodes. Use stacked state groups only when they clarify the requested view. |
| Release slice or user journey | What minimum end-to-end capability becomes useful? | Optional when the project has a known user journey. Infrastructure and research may instead use an operational or evidence milestone. |

State what arrows mean. Group membership, chronology, dependency and contribution
to an outcome are different relationships; do not give them identical arrows.
Avoid circular layouts and wide timelines unless they solve the user's actual
question. Call a dependency chain a critical path only when scheduling evidence
supports that claim.

## Human reading order

Use the full sequence for a project-chat brief. A routine refresh can stop at
the status flow, actual blocker/next action and concise observation scope.

1. Desired result and first useful milestone, with a simple success condition.
2. Overall workstreams, completed foundation and the path still needed.
3. Current attention: what can advance, what is waiting, what needs a decision.
4. Up to three recommendations, ranked and linked to evidence.
5. Deferrable improvements and their return conditions.
6. Expandable chat evidence, technical detail and scan coverage.

Use everyday result labels such as “Try one real report” before terms such as
pipeline, adapter or deployment topology. Make counts literal: “8 chats read”
is useful; an invented completion percentage or priority score is not. Add dates,
effort or delay estimates only when sources establish them. Localize labels,
legends, statuses, accessible names and detail controls to the current user
language; source titles and identifiers remain exact.

Use status text and symbols alongside color. Keep text readable at normal chat
width and on a narrow screen. Include a concise text alternative naming the
outcome, active work, main blocker and next action. For interactive output,
keep local expansion and drill-down independent of worker chats. Opening a
detail panel only reveals evidence and the next step; it never changes work
status or submits a project decision. Keep actual decision requests separately
labeled and explain where a response belongs. Read the
available `visualize` skill before using its inline rendering contract. Mermaid
is the default for a sufficient static status flow; deterministic SVG/PNG exports
are preferable to image generation for exact status labels and relationships.

## Recommendations

For each proposed next action, name the outcome it unlocks, the source evidence,
the responsible person/chat when known and the check that would establish
success. Rank qualitatively by impact on the useful milestone and demonstrated
dependency fan-out, then consider cost/risk where evidence exists.

A deferral recommendation needs: what waits, why the milestone remains useful
without it, the cost or limitation accepted, and when to revisit it. If that
trade-off contradicts an explicit requirement, present a scope decision for
the user rather than a directive to workers. Never infer that a slow task or
extensive testing is dispensable merely because it consumes resources.

Distinguish a suggestion from the project's agreed plan. When no intervention
is warranted, state that rather than manufacturing a course correction.
