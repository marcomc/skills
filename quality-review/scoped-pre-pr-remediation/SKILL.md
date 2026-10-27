---
name: scoped-pre-pr-remediation
description: Review and fix an authorized branch, selected commits, explicit diff range, staged, unstaged or all uncommitted changes using one shared review coordinator before PR review.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Scoped Pre-PR Remediation

Resolve the requested scope and enter `$review-coordinator` in remediation mode.
Pass the user's behavior/constraints and existing findings/evidence. When called
inside an active review run, continue that coordinator and ledger; do not invoke
`pre-pr-review-gate` or `max-findings-relentless` as additional loops.

Carry a finite scope contract into the coordinator: objective, in-scope
behaviors, non-goals, intentionally unsupported forms, a fixed acceptance
matrix, and the definition of an actionable finding. Do not expand the branch
because a reviewer proposes an unbounded language variant or adjacent feature.

When a dependency migration exposes a synthetic malformed-row case, compare the
pre-migration model and read-completeness contracts before broadening
validation. Classify the synthetic case separately from observed persisted-data
shapes, retain only established domains, and keep unrelated write authorization
out of the remediation.

For a branch that will receive remote review, make the reviewable unit explicit:
name the one user-visible behavior or finite contract it changes, the complete
acceptance cases, and the intentionally unsupported cases. The pre-PR pass must
leave one integrated closure candidate, not a sequence of separately reviewed
micro-fixes. If local remediation finds related defects, include their reachable
siblings in that candidate; otherwise record the required PR split before any
remote review is requested.

## PR completeness gate

Before `READY` or any remote review request, answer this exact question for the
proposed PR: **“Does it deliver one complete, verifiable and unambiguous user
behavior without requiring a second PR to make that behavior correct?”** The
answer must be `yes`, with evidence, for a reviewable PR unit.

Record the answer as a short PR-unit card:

| Field | Required content |
| --- | --- |
| Behavior | One observable user outcome or finite contract |
| Boundary | Inputs, persisted/shared state and side effects it owns |
| Acceptance | Complete supported cases and their proof |
| Non-goals | Unsupported or optional cases that do not make the behavior incorrect |
| Dependency decision | Why a follow-up PR is optional, or why this work must be recombined or split |

Small commits may implement parts of that behavior; they do not individually
justify remote PRs. A second PR may add an independent optional capability, but
may not be necessary to repair a missing state transition, permission,
configuration path, error case or acceptance case of the first behavior. If the
answer is `no` or unclear, do not request remote review: either recombine the
dependent work into one closure candidate or narrow the first PR to an honestly
complete behavior and record the explicit split.

The companion `review-coordinator` must be installed alongside this skill.
Its shared contract owns risk selection, specialist routing, sibling closure,
integrated validation, proof reuse and the local exit decision. Report a missing
companion as a dependency gap rather than substituting assumed coverage.

## Scope

Use `git status --short`, `git diff --stat`, `git diff --staged --stat`,
`git diff <base>...HEAD --stat` and `git show` as appropriate. For all uncommitted
work include both staged and unstaged changes plus relevant untracked artifacts;
for explicit ranges preserve their exact boundaries. A branch-only helper does
not establish coverage of working-tree changes. Preserve unrelated user work.

Review-only requests retain report-only mode. Remediation authorization does not
by itself authorize staging, commits, pushes, PRs, thread resolution or deployment.
The coordinator owns edits and integration; independent reviewers receive only
their relevant contracts, raw artifacts and required evidence.

Return the shared local status, actual scope, fixed/open defects, executed/reused
checks and remaining optional suggestions. The coordinator runs terminal learning
once; this entrypoint does not mutate policies or start a second capture.
