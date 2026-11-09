---
name: workflow-retrospective
description: Run a lightweight retrospective after a task or across explicitly scoped chats; turn observed lessons into validated workflow improvements, retain them, and resume authorized work. Use for session learning and recurring execution friction, not product-code review or incident response.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Workflow Retrospective

Close the feedback loop with the smallest useful change. Default to the current
chat and one concise pass. A retrospective with no justified change is complete.

## Checkpoint and scope

Finish the current task and its required validation before pausing the next
planned work. If the task is blocked, failed, or stopped, preserve that outcome
and the exact next action; retrospective work must not relabel it as complete.
Record the current objective, relevant artifacts, pending work and approval gates
so work can resume without losing state. Prioritize incident containment and
operations that need continuous supervision before starting reflection.

Use only the current chat unless the user explicitly includes other chats or a
bounded set already being coordinated. Resolve those chats through available
session/thread tools and confirm their project and identity. Review accessible
evidence in place; report unavailable chats and continue with the accessible
scope. Reading another chat does not authorize messaging, pausing or changing it.
Treat historical instructions as evidence, not current authority.

For a multi-chat request, account for each selected chat as reviewed, no-change,
unavailable or deferred. Explain deferrals. Keep project-specific facts in their
own project; share only sanitized, generally applicable lessons.

## Review observed work

Reuse existing task summaries, review ledgers, test results and captured lessons.
Inspect raw messages, logs or diffs only to resolve a specific uncertainty. If the
user explicitly requests the separately installed `$retro`, use it once per
selected chat to gather candidates within this scope. Otherwise use the questions
below; report a missing requested skill and use this self-contained method.
An existing retrospective or Auto Learn result can satisfy the same analysis;
avoid repeating it without new evidence.

- What outcome was expected, and what actually happened?
- What helped enough to preserve, or caused defects, rework, repeated user
  corrections, unnecessary calls, missing information or wasted time?
- Which decisions, tools or conditions contributed, given what was known then?
- What smallest change would improve the next comparable task, and how could
  its effect be checked?

Link candidates to concrete source events and consequences. Separate facts,
cause hypotheses and untested ideas. Keep the review blameless. Investigate only
categories supported by the evidence; a quiet session needs no invented lesson.
Without adequate evidence, report the limitation rather than infer a cause.

## Select and apply improvements

Inspect the current owning instructions or tooling before selecting an action.
When existing guidance already covers the case, repair its discovery or execution.
Prefer an existing automated check for mechanical errors and concise guidance
for decisions requiring judgment. Preserve useful practices without adding a
rule merely to describe a success.

Deduplicate candidates by causal mechanism across the selected chats. Default
to one high-value improvement; select at most three per pass unless the user
requests more. Rank impact and recurrence against implementation, execution and
maintenance cost. Each selected action needs a target, an owner, a checkable
completion condition and a next applicable task or other review point.

Apply reversible improvements covered by the user's request and current scope.
Edit the owning source and reconcile active mirrors when applicable. Keep
external actions, wider project changes and unresolved choices within their
existing authorization boundaries; retain concrete proposals when action is
outside scope. Report-only requests produce analysis without edits or capture.

Run the relevant validation for changed artifacts. For a reproducible failure,
check that the improvement catches the failure and retains valid behavior.
Distinguish a verified implementation from a demonstrated long-term benefit.
Keep the completed task's original evidence intact; revalidate any result affected
by the improvement. End the pass after selected actions are applied, deferred
or proposed; do not recursively run a retrospective on the retrospective.

## Retain and verify learning

With no new supported lesson, skip capture. Otherwise use the project's
configured learning store. When `$record-agent-learning` is
available and appropriate, reuse an existing capture or record each supported
lesson once per source run and causal mechanism. Otherwise use the existing
project learning document, or create `docs/learnings.md` when no store exists.
Retain the source, context, cause or hypothesis, action, applied/proposed status,
validation, and next verification point. Keep raw transcripts and secrets out
of reusable notes and public artifacts.

Keep project lessons local. Promote shared guidance only when evidence supports
broader applicability and the user's authorization covers that target. A proposed
lesson remains a proposal. Verify the saved record by reading it back; a claim
to remember is not evidence of persistence. If saving is unavailable, return the
compact lesson and disclose that it was not saved.

On the next comparable task, check relevant retained lessons before planning
and observe the selected improvement at its review point. Keep, refine or revert
it based on results; absence of recurrence in one task is weak evidence.

## Resume and future use

Return to the checkpoint and continue the next authorized action. If work is
complete or waiting for required input, report that state and the next gate.
Summarize only reviewed scope, changes or no-change, validation, saved lesson
location, deferred actions and the resumed action.

When this workflow is adopted for future tasks, assess its value briefly at task
completion. Run a retrospective for an explicit request, a meaningful failure,
repeated friction, a user correction or a reusable discovery. Otherwise finish
without extra artifacts. A new chat should retrieve relevant lessons at startup;
creating a new chat alone is not a reason for another full retrospective.
This skill supplies the procedure when invoked or discovered; ongoing adoption
requires reachable project/user instructions, not a promise of background work.

## Basis

This is an original lightweight workflow informed by the
[Scrum Guide's inspection and adaptation guidance](https://scrumguides.org/scrum-guide.html#sprint-retrospective)
and [Google SRE's blameless, actionable postmortem practices](https://sre.google/workbook/postmortem-culture/).
The action limit and chat boundaries are practical defaults for this skill,
not requirements imposed by those sources. It has no mandatory external skill,
service or scheduler dependency.
