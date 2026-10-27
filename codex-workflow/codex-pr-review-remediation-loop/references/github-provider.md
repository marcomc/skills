# GitHub Codex review evidence

Use this provider contract only for remote observation and correlation. Local
quality and remediation belong to the shared coordinator. The entrypoint's
completion authority covers routine scoped publication and review operations;
do not add another confirmation gate here.

## Core rule

Before posting `@codex review`, inspect the PR description timeline comment and
latest review triggers. The PR description supplies reaction status:
Codex adds `eyes` while reviewing and may add `+1`/👍 when clean. Structured
Code Review state or an explicit reviewed commit can also establish completion
under the entrypoint's reconciliation contract. A user-authored `@codex review` issue comment is a
trigger and correlation record; it is not the clean-status anchor.

When the PR description already has the bot's `eyes` reaction, treat the pass
as already running, monitor that PR description entry, and do not post a
duplicate `@codex review` except under the entrypoint's bounded stale-pass
recovery policy. A `+1` reaction on the trigger comment alone never
completes the loop.

After posting a literal `@codex review`, treat that recent trigger as a
monitoring state until Codex posts a reaction, summary, inline feedback, or a
quota response. Do not post a second trigger merely because the status reaction
has not appeared yet.

The detector distinguishes two pending states: `requested_unacknowledged`
means the trigger has no observable Codex activity yet; `running` means Codex
has acknowledged the pass with `eyes`. Both are pending, so a quiet poll or
timeout remains non-terminal. Apply the entrypoint's stale-pass recovery policy
when its inactivity threshold is reached; otherwise hand monitoring forward.
When the detector reports `feedback_ready`, stop polling and begin the complete
closure batch from its full finding snapshot. When it reports
`clean_confirmation_pending`, a summary or reaction exists but cannot yet prove
the exact head; reconcile that pass before requesting another review.

Every review request must be an issue comment whose literal body is exactly
`@codex review`, including the `@` mention. Do not use `codex review` without
the `@`, quote it as prose, or use a different trigger spelling.

If the bot posts `You have reached your Codex usage limits for code reviews.`
after the latest literal trigger, treat it as quota-blocked until newer bot
activity proves that pass resumed. Compare timestamped description reactions,
review summaries, inline comments and issue comments against the quota response.
An older description 👍 cannot suppress a new quota block. Do not send another
request or nudge while that block is current.

Complete any authorized PR title, body, draft, or readiness changes before
starting terminal review polling. If any such mutation happens afterward,
discard the earlier terminal snapshot and refresh the authoritative status
anchor; when it is already in progress, resume monitoring without posting a
duplicate review trigger.

## Anchor Rules

Each pass has two distinct anchors:

- status anchor: the PR description timeline comment, authoritative for
  `eyes`/👍 state;
- trigger anchor: the `@codex review` comment that requested the pass, used only
  to correlate feedback and timestamps.

Use the recorded pass/head association or explicit reviewed commit to establish
current-head identity; commit creation time is insufficient.

Treat reactions from `chatgpt-codex-connector[bot]` on the PR description as
state:

- `eyes`: pending review; monitor or apply bounded stale-pass recovery even
  if no review body exists;
- `+1`/👍 with no remaining `eyes`: clean signal when no newer actionable Codex
  content appeared and the signal belongs to the current PR head.
- Any newer timestamped Codex reaction is activity evidence for quota-age
  classification, but is not by itself a clean signal.

Do not use a `+1` on an `@codex review` trigger comment as the terminal signal.
A textual `Didn't find any major issues.` summary establishes clean when its
explicit `Reviewed commit:` matches the current head and active pass and no
actionable feedback remains. Structured `code_review` completion must likewise
match the current head/pass and show no remaining findings. A security-only
result never substitutes for Code Review; an unbound summary is non-terminal.

For structured evidence, read the `<!-- codex-review-state:v1 {JSON} -->`
summary from a `chatgpt-codex-connector[bot]` comment on this PR. Require its
`code_review.commit_sha` to equal the full current head, `status` to equal
`completed`, and both `has_any_findings` and `has_unresolved_findings` to be
`false`. Require timestamped current-head Code Review progress after the recorded
trigger and the summary's latest update after that trigger; preserve the raw
comment and pass association. A summary update caused only by thread resolution,
an old completed component or another component cannot bind a new request.
Unknown/null fields, unrelated checks and `security_review` do not qualify.
When these checks pass but the detector still reports pending because it lacks
this summary parser, preserve its output and record a separate provider
reconciliation with derived phase `clean`, the raw source, exact head and active
trigger. This is the entrypoint's permitted terminal reconciliation; all local
proof and unresolved-feedback requirements still apply.

Always compare review content timestamps against the active anchor so older
summary cards do not get mistaken for the current pass.
Always compare clean signals against the current PR head so stale PR-description
reactions do not stop a required re-review after new commits land.

## Feedback Handling

Classify Codex output carefully:

- Actionable: inline review findings and concrete location-linked findings in
  submitted reviews or bot issue comments. Body locations must identify the
  current head and PR repository; summaries, quoted examples and other repos
  do not establish a current finding.
- The detector reads every page of review threads. A finding outside the first
  GitHub result page is still current feedback and must enter the same closure
  snapshot before a replacement-head review is requested.
- Clean evidence: `Didn't find any major issues.` in a PR issue comment, review
  body, or current-pass summary, subject to the current-head/pass binding above.
- Non-actionable summary: a new Codex review summary for the current pass with
  no inline/location-tied findings.
- Operational block: the bot's usage-limit comment after the latest literal
  `@codex review` trigger. This is neither feedback nor a clean result.
- Ignore for action: stale summaries from older anchors and summary cards with
  no concrete requested change.

If GitHub reports the PR as merged or closed, the detector returns
`review_closed`. This stops remote review work. It does not retroactively prove
a clean review, particularly when new findings and merge happened concurrently.
