---
name: codex-pr-review-remediation-loop
description: Use when a GitHub PR is under Codex review and current Codex feedback must be monitored, coordinated, remediated, re-reviewed, or driven to a clean terminal result.
metadata:
  short-description: Loop Codex PR review, fixes, and re-review until clean
---

# Codex PR Review Remediation Loop

Use this skill when a GitHub PR is under Codex review and you need to keep the
loop moving until Codex reports no major issues.

## Quick Start

From the repository branch, run the bundled anchor detector first:

```bash
python3 ~/.agents/skills/codex-pr-review-remediation-loop/scripts/detect_codex_review_anchor.py
```

Use its `decision` field:

- `fix_existing_feedback`: remediate unresolved actionable Codex feedback first.
- `monitor_existing_pass`: start or resume monitoring the reported anchor.
- `post_codex_review`: no active pass was found; post `@codex review`.

## Core rule

Before posting `@codex review`, inspect the PR description timeline comment and
latest review anchors. Codex often starts the first review by adding an `eyes`
reaction from `chatgpt-codex-connector[bot]` to the PR description. When that
reaction exists, treat the first pass as already running, use the PR
description timeline comment as the active anchor, and wait for Codex feedback.
Do not post a duplicate `@codex review`.

## Workflow

1. Find the active PR for the current branch.
2. Run `scripts/detect_codex_review_anchor.py` or inspect these surfaces
   manually before posting anything:
   - PR description timeline comment and reactions,
   - existing `@codex review` comments and reactions,
   - PR issue comments,
   - submitted reviews and review summaries,
   - inline review threads/comments.
3. If unresolved actionable Codex comments already exist, collect all of them
   into one remediation context before applying fixes.
4. If a current review pass is in progress, monitor it instead of requesting a
   duplicate review.
5. If no pass is active and no unresolved actionable comments exist, post
   `@codex review` and use that comment as the anchor.
6. Start a dedicated `monitor` agent for polling unless a thread heartbeat is
   already set up to resume the loop.
7. If a newly posted `@codex review` comment sits for several polling cycles
   with no `eyes`, no `+1`, and no newer Codex review, post one explicit nudge
   comment that asks Codex to re-run on the latest pushed commit SHA; then
   monitor that nudge as the active request.
8. When actionable feedback arrives, coordinate subagent remediation, integrate
   the fixes, test, commit, push, resolve the fixed threads, request another
   review, and repeat. Classify each finding by the smallest useful specialized
   reviewer profile before dispatching work.
9. Before ending the loop, run `$codex-review-skill-autolearn` with the
   findings, fixes, regressions, and terminal outcome. Its learning target is
   not only project `AGENTS.md`; generic Codex findings must also be folded
   into the reusable pre-PR review skills that should catch them before the
   next Codex review.

## Anchor Rules

An active pass is anchored by either:

- the PR description timeline comment, for the first pass when Codex put
  `eyes` there before any dedicated review request exists,
- the `@codex review` comment that started a later pass.

Treat reactions from `chatgpt-codex-connector[bot]` on the active anchor as
state:

- `eyes`: review is in progress; keep polling even if no review body exists.
- `+1` with no remaining `eyes`: clean signal when no newer actionable Codex
  content appeared for that anchor and the signal belongs to the current PR
  head. Confirm this with a Codex clean summary whose reviewed commit matches
  `headRefOid`, or with a bot clean-reaction timestamp at or after the latest
  head commit time.

Always compare review content timestamps against the active anchor so older
summary cards do not get mistaken for the current pass.
Always compare clean signals against the current PR head so stale PR-description
reactions do not stop a required re-review after new commits land.

## Monitor Contract

Pass the monitor agent:

- PR number,
- branch,
- anchor comment id/url,
- anchor type: PR description timeline comment or `@codex review` comment,
- anchor timestamp,
- terminal conditions below.

If using the detector script, pass its `active_anchor` object directly into the
monitor prompt.

The monitor returns only when one of these happens:

- new actionable Codex inline/thread/location-tied feedback appears,
- Codex posts `Didn't find any major issues.`,
- the active anchor gets a clean `+1` signal and no newer actionable content,
- a new Codex review summary for the active pass arrives with no actionable
  inline/location-tied findings,
- polling fails or times out.

Poll for up to 20 minutes, using longer waits such as 60-120 seconds. Do not
treat silence while `eyes` is present as idle or failed review.

If the monitor exits without a terminal condition, restart monitoring or report
the monitoring failure. Do not end the turn with only "waiting" and no resume
mechanism.

## Remediation Coordination

The main chat is the coordinator and owns the full PR context. Use subagents to
apply remediation work when Codex reports multiple actionable findings, but do
not let subagents choose fixes in isolation.

Before dispatching any remediation subagent:

- collect every current actionable Codex finding from comments, reviews, and
  unresolved threads,
- inspect the branch diff, dirty tree, touched files, and project validation
  commands,
- group findings by shared files, modules, behavior contracts, migrations,
  tests, deployment paths, and user-facing outcomes,
- map each group to the smallest useful specialized reviewer profile, such as
  `$pre-pr-review-frontend`, `$pre-pr-review-backend-services`,
  `$pre-pr-review-infra-runtime`, `$pre-pr-review-security-boundaries`,
  `$pre-pr-review-tests-validation`, `$pre-pr-review-docs-release`,
  `$pre-pr-review-config-data-flow`, `$pre-pr-review-cli-tooling`,
  `$pre-pr-review-ci-actions`, or `$pre-pr-review-agent-workflows`,
- decide which findings can be fixed in parallel and which must be fixed
  serially because they touch overlapping code or could imply incompatible
  behavior,
- write one shared remediation brief that every subagent receives.

Each remediation subagent prompt must include:

- PR number, branch, base branch, and current HEAD,
- the full list of actionable Codex findings, not only the assigned one,
- the subagent's assigned finding ids, file paths, and expected scope,
- `$pre-pr-remediation-worker` as the edit-capable worker contract,
- the selected specialized reviewer profile or profiles as domain context,
- explicit conflicts and dependencies with the other findings,
- files or modules the subagent must not edit unless the coordinator expands
  its scope,
- required regression tests or validation commands for its assigned fix,
- instruction to edit files directly and report changed paths, tests run, and
  any residual risk.

Parallelize only when write scopes are disjoint or clearly compatible. If two
findings touch the same file, shared abstraction, public contract, generated
artifact, or validation workflow, handle them in one subagent or sequence them
through the main chat. The coordinator must review each returned patch before
merging it with other subagent work.

After subagents return:

- inspect combined diffs for conflicting assumptions or duplicated logic,
- run the targeted checks for each finding and the repo's standard validation,
- refresh live GitHub thread ids before resolving fixed conversations,
- commit and push only after the integrated branch is coherent and validated.

## Feedback Handling

Classify Codex output carefully:

- Actionable: inline review findings, concrete requested changes, or comments
  tied to specific code locations.
- Clean: `Didn't find any major issues.` in a PR issue comment, review body, or
  current-pass summary.
- Non-actionable summary: a new Codex review summary for the current pass with
  no inline/location-tied findings.
- Ignore for action: stale summaries from older anchors and summary cards with
  no concrete requested change.

When feedback is actionable:

- inspect the referenced code and root cause,
- apply the smallest correct fix, using remediation subagents according to the
  coordination rules above when there are multiple actionable findings,
- run targeted checks first, then the repo's standard validation command,
- add or run a sibling regression for the same failure class,
- commit and push before resolving GitHub review threads,
- refresh live thread ids before resolving if a resolve attempt fails.

## Failure Classes To Learn From

After each fix batch, classify reusable lessons so local review skills can be
improved before the next GitHub review:

- sentinel/default round-trip loss,
- dry-run/read-only side effects,
- duplicate background workers,
- misleading status after skipped work,
- feature-disabled privilege leakage,
- config forwarding and wrapper/render parity gaps,
- generated service or scheduler artifacts ignoring configured install paths,
  destination parents, or overridden runtime locations,
- non-unique label identity,
- time/clock skew scheduling,
- cross-layer validation limit drift,
- publication/privacy disclosure.

If a Codex finding is intentionally accepted as product behavior, document that
decision in the repo before requesting another review.

## Learning Targets

After a terminal Codex review pass, update durable guidance at the right level:

- project `AGENTS.md` for repo-local conventions and commands,
- the smallest relevant specialized pre-PR reviewer profile for domain-specific
  prevention rules,
- `$pre-pr-review-gate` for generic checks that should block or flag a branch
  before requesting Codex review,
- `$scoped-pre-pr-remediation` for generic remediation orchestration lessons,
- this skill when the Codex review loop itself missed a sequencing,
  monitoring, remediation, or autolearn obligation.

Do not treat `AGENTS.md` updates as a substitute for reusable skill updates
when the learned class is cross-repo. If the relevant pre-PR skills already
cover the class with enough precision, record a no-op rationale instead of
adding duplicate text.

Run `markdownlint` with `$HOME/.markdownlint.json` on every
`SKILL.md` changed by this learning step.

## Stop Conditions

Stop successfully when the latest current-pass Codex result says
`Didn't find any major issues.` or when the active anchor has a clean `+1`
signal for the current PR head with no newer actionable Codex content.

You may stop the monitoring phase, but not mark it clean, when Codex delivered
a non-actionable summary review for the current pass. Report it as
`non-actionable summary review` so the caller can decide whether to accept the
pass or request another review.

Before exiting any terminal state:

- summarize fixes and validation,
- note unresolved or intentionally accepted items,
- run `$codex-review-skill-autolearn`,
- update relevant pre-PR skills or state why no reusable skill update was
  warranted,
- do not keep polling once a valid terminal condition has been reached.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
