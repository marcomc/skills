---
name: codex-pr-review-remediation-loop
description: Monitor GitHub Codex review, route actionable feedback to the shared review coordinator and obtain a clean current-head remote result, or preserve an explicit non-success stop. Requires the companion review-coordinator skill.
metadata:
  short-description: Adapt GitHub Codex feedback to the shared review run
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Codex PR Review Remediation Loop

This is the GitHub/Codex adapter. `$review-coordinator` owns local quality,
remediation, evidence reuse and learning. Continue one existing coordinator and
ledger; do not create another local loop through pre-PR or relentless entrypoints.
Install the companion alongside this skill before local remediation/readiness.

## Observe before requesting

Pin every repository-sensitive GitHub read explicitly: use `gh pr view --repo
OWNER/REPO` and `gh repo view OWNER/REPO`, then compare PR URL, number and head
against the intended fork. `GH_REPO` alone does not bind every command's inference.

Find the PR for the requested branch and run:

```bash
python3 ~/.agents/skills/codex-pr-review-remediation-loop/scripts/detect_codex_review_anchor.py
```

Read [github-provider.md](references/github-provider.md) for status anchors,
current-head correlation, quota precedence and feedback classification. The
adapter returns remote facts, not a code-quality verdict. Existing unresolved
feedback takes precedence over starting another pass; an active pass needs one
monitor. Use the stale-pass recovery policy below for an elapsed interval;
a missing reaction or polling timeout alone never proves completion.

Treat `review_observation.phase`, `terminal` and `next_action` in detector
output as the runner's state machine. Do not replace them with a generic
“no new findings” interpretation. `running`, `requested_unacknowledged` and
`clean_confirmation_pending` are non-terminal states; continue the prescribed
observation or reconciliation. `feedback_ready` means start a complete closure
batch now. Only `clean` and `closed` are terminal, and `closed` is not clean.
If the detector cannot consume a provider summary, the explicit provider
reconciliation below may establish `clean`: retain the raw detector result,
record the verified evidence and derived phase separately in the same ledger,
then reconcile local/pushed inputs. This narrow evidence-based transition does
not allow silence, stale reactions or security-only results to override pending.

| Detector decision | Adapter action |
| --- | --- |
| `fix_existing_feedback` | Collect all actionable current feedback and return it to the same coordinator |
| `monitor_existing_pass` | Resume the existing pass with one compact monitor |
| `post_codex_review` | Require local `READY`, matching pushed inputs and a complete closure batch, then send one exact `@codex review` trigger |
| `verify_clean_signal` | A reaction exists but its head is unproven; reconcile the recorded pass before accepting or requesting anything |
| `clean_signal` | Reconcile local/remote HEAD and existing local proofs; finish only when both local and remote conditions hold |
| `usage_limit_blocked` | Preserve state and report remote `blocked`; never report clean |
| `review_closed` | Stop the loop and report whether closure happened with a proven clean current head; never push, retrigger or keep polling this PR |

## Completion authority

An explicit request to run or complete this remediation loop authorizes the
routine operations needed to obtain a clean current-head Codex Code Review:
scoped fixes, tests and documentation, validated closure commits and pushes to
the PR branch, literal review requests, resolution of verified fixed threads,
and continued monitoring. Carry that authority through the same coordinator and
subsequent closure batches; do not pause to ask permission to continue, commit,
push, request review or resolve fixed feedback. The goal is a PR ready to merge
with a proven clean Code Review, not merely a local fix or a configured monitor.

Honor explicit user limits such as report-only, no push or no thread resolution.
This completion authority excludes merging, release publication, deployment,
unrelated changes and destructive operations. Actual access failures, quota or
an unresolved scope decision remain explicit non-success outcomes; never invent
success or bypass platform controls. Complete any separately requested PR
metadata/readiness changes before terminal review; later edits invalidate the
affected evidence.

## Bind the observed pass to its head

Record the exact head and UTC start time when a review is requested under the completion authority
or when a new in-progress pass is directly observed on that unchanged head.
Store this association in the coordinator ledger; after confirming the same head,
pass `--review-head <full-sha> --review-start <recorded-iso-timestamp>` on detector
calls. Do not derive this record from commit dates or a later clean reaction.

A head-bound review/summary can also establish identity. `verify_clean_signal`
means an old reaction cannot yet be associated: inspect existing pass evidence.
If no association exists and no review is active, request one fresh
pass after local `READY`, recording its head/start. Do not poll an unprovable clean
forever, invent a start time or keep posting triggers. Commit creation time alone
is not push time or evidence that the current head was reviewed.

## Remediation handoff

Pass current head, anchor, raw finding IDs/locations, feedback and selected
contract context to `$review-coordinator`. It triages false positives, closes
confirmed siblings, checks recurrence and returns the local result. Do not
reinterpret its recovery allowance or request review while recovery is incomplete.

The handoff must include the PR's finite scope contract, non-goals, acceptance
matrix and actionable-finding definition. Findings that only request support for
an explicitly unsupported form are not defects; record them as optional scope
and do not trigger another remediation round.

Classify every finding before selecting a fix. A correctness finding demonstrates
an observable contract violation, unsafe mutation, data loss, or lack of durable
progress for supported normal input, and belongs in the closure batch. A
resilience finding about malformed, ambiguous, or unsupported input is not a
defect when the product contract permits leaving that input untouched and no
wrong mutation occurs. A request for broader recognition, compatibility, or
normalization is optional scope unless the PR explicitly accepts it. An edge-case
example does not itself expand the acceptance matrix.

If two complete closure snapshots produce distinct findings in the same family,
the coordinator must examine the common invariant and either make one coherent
root-cause correction or record why the later request is optional scope. Do not
add a third pattern-specific patch merely to satisfy a new example. This is a
scope-health gate, not a cap on review passes: remediation may continue after
the classification/root-cause decision and a normal closure batch.

For a replacement-head request, first freeze one complete feedback snapshot for
the reviewed head: every current actionable finding must have an ID, location,
family and disposition. The coordinator's closure batch must contain every
confirmed defect from that snapshot and its reachable siblings, or record an
explicit PR split for work that cannot share the same contract. Do not request
review for a partial fix, an interim commit, an individual regression test or
ledger/docs bookkeeping. New independent findings from a later pass form the
next normal snapshot; the number of review rounds alone never ends the loop.

After the complete batch has passed its focused and integrated checks, the
coordinator returns `READY` for its frozen closure head. After the validated
push, refresh thread IDs and resolve only fixed feedback whose fix is present
remotely, subject to any explicit user restriction. Re-observe the anchor: if an automatic
review is already active, monitor it instead of posting another trigger.
Otherwise request one pass for that closure head. If the coordinator reports
`SUSPECTED` or `RECOVERY`, follow its convergence or recovery process before
asking for another remote pass; only its `BLOCKED` outcome stops remediation.

## Monitor the existing pass

Give the monitor PR identity, head, active anchor, seen finding IDs and terminal
conditions. It needs no code diff, full chat or remediation history. Poll at
30, 60, then 120 seconds while unchanged; reset on new evidence. Use scheduler
waits or foreground waits of at most 60 seconds to preserve responsiveness.
Only one component polls. Send state changes instead of repeated full snapshots;
honor user-requested updates and host communication requirements.

At every observation, run the detector again against the exact PR head. Its
output contains the complete unresolved inline snapshot, including finding body,
priority, review identity and head relation. It also paginates review threads,
so feedback beyond GitHub's first page remains visible. A transition to
`feedback_ready` is an instruction to hand the full snapshot to the coordinator,
not to wait for a reaction. A `requested_unacknowledged` pass has no observed
bot acknowledgement yet; it remains pending rather than failed. A `running`
pass has observed acknowledgement but no terminal result. A current textual
clean summary without a bound clean anchor is `clean_confirmation_pending`:
reconcile it before any new trigger.

### Recover a stale pass

Default to a 30-minute inactivity threshold, configurable to 60 minutes at the
user's request. Measure from the latest trigger or meaningful current-pass bot
progress, whichever is newer. Repeated reads, an unchanged `running` card and
old reactions do not reset the timer. Staleness is a recovery heuristic, not
proof that the provider process failed or stopped.

For `running` or `requested_unacknowledged` at the threshold, re-observe the
exact open PR and unchanged head. Handle findings, quota, closure and clean
signals first. Under the completion authority, with the published head's existing
validation still applicable, send one literal `@codex review` recovery request
on that same head, even when the old card still says `running`. No commit or
push is needed. If an explicit user restriction prevents the request, report the concrete recovery action.

Preserve the old pass in ledger history with the staleness evidence. Record the
new trigger ID, UTC start, head, recovery count and last meaningful progress;
rebind the sole monitor and any heartbeat prompt to that pass. A successful
post proves a request, not cancellation of the old job or startup of the new
one. On an uncertain POST outcome, reconcile the timeline before retrying.

Allow one automatic stale-pass recovery per unchanged head. If the replacement
also reaches the inactivity threshold, preserve remote `blocked`, notify the
user once that the replacement is stalled. Continue quiet read-only monitoring
under the completion authority, without asking permission to proceed or posting
more triggers on that head. Fresh provider progress can resume the pass; quota,
access failure or PR closure follows its explicit non-success handling. A new
user instruction may establish a fresh recorded recovery allowance.

Keep the monitor handoff explicit about its pending phase, observation time,
current trigger/head and remaining recovery allowance. Use one quiet monitor;
notify only on meaningful change, recovery, failure or required user action.

## Reconcile once

Remote status is `not_requested`, `pending`, `feedback`, `clean_current` or
`blocked`. Success requires local `READY`, matching validated local/pushed content,
no unresolved actionable feedback and the detector's current-head clean signal.
A historical 👍, textual summary alone or local test PASS does not satisfy it.
The bot comment `Codex Review: Didn't find any major issues.` is also a clean
signal when its `Reviewed commit:` matches the recorded current head, it follows
the active trigger, and no actionable feedback remains; a missing 👍 alone is
therefore not a failure.

Reuse current pre-publication audit/test evidence after a clean cloud result.
Only new substantive feedback or changed inputs reopens affected local work.
A bookkeeping correction cannot start another whole-PR review. Return the exact
head and both statuses; the existing coordinator owns terminal learning once.

## Compatibility commands

The old `scripts/analyze_remediation_loop.py` and
`scripts/prepare_remediation_audit.py` paths forward to `review-coordinator`.
Their schemas and CLI contracts remain available there. They do not contain
separate implementations; the completion authority above governs publication.
