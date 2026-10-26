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
monitor. A missing reaction, an elapsed interval or a polling timeout is not
permission to retrigger or to declare the review finished.

Treat `review_observation.phase`, `terminal` and `next_action` in detector
output as the runner's state machine. Do not replace them with a generic
“no new findings” interpretation. `running`, `requested_unacknowledged` and
`clean_confirmation_pending` are non-terminal states; continue the prescribed
observation or reconciliation. `feedback_ready` means start a complete closure
batch now. Only `clean` and `closed` are terminal, and `closed` is not clean.

| Detector decision | Adapter action |
| --- | --- |
| `fix_existing_feedback` | Collect all actionable current feedback and return it to the same coordinator |
| `monitor_existing_pass` | Resume the existing pass with one compact monitor |
| `post_codex_review` | Require local `READY`, publish permission, matching pushed inputs and a complete closure batch, then send one exact `@codex review` trigger |
| `verify_clean_signal` | A reaction exists but its head is unproven; reconcile the recorded pass before accepting or requesting anything |
| `clean_signal` | Reconcile local/remote HEAD and existing local proofs; finish only when both local and remote conditions hold |
| `usage_limit_blocked` | Preserve state and report remote `blocked`; never report clean |
| `review_closed` | Stop the loop and report whether closure happened with a proven clean current head; never push, retrigger or keep polling this PR |

Review/remediation scope and Git/GitHub permissions remain those granted by the
user. The adapter does not authorize commits, pushes, comments or thread closure.
Complete authorized product/docs, PR title/body and readiness changes before
the terminal remote review; subsequent edits invalidate affected evidence.

## Bind the observed pass to its head

Record the exact head and UTC start time when an authorized review is requested
or when a new in-progress pass is directly observed on that unchanged head.
Store this association in the coordinator ledger; after confirming the same head,
pass `--review-head <full-sha> --review-start <recorded-iso-timestamp>` on detector
calls. Do not derive this record from commit dates or a later clean reaction.

A head-bound review/summary can also establish identity. `verify_clean_signal`
means an old reaction cannot yet be associated: inspect existing pass evidence.
If no association exists and no review is active, request one fresh authorized
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
coordinator returns `READY` for its frozen closure head. After an authorized
push, refresh thread IDs and resolve only fixed feedback whose fix is present
remotely, when resolution is authorized. Re-observe the anchor: if an automatic
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

After 20 minutes without a terminal result, report the head, detector phase,
latest observed bot activity and resume path. Continue or renew monitoring
within authorization using an available monitor or thread heartbeat; do not
abandon active work, duplicate triggers or turn silence into success. A monitor
handoff must say which non-terminal phase remains, when it was last observed and
that the next runner must re-run the detector before acting. Quota, operational
failure and unresolved user choices keep explicit non-success states.

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
separate implementations or grant publication permission.
