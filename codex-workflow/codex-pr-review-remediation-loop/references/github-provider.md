# GitHub Codex review evidence

Use this provider contract only for remote observation and correlation. Local
quality and remediation belong to the shared coordinator.

## Core rule

Before posting `@codex review`, inspect the PR description timeline comment and
latest review triggers. The PR description is the authoritative Codex status
anchor for every pass: Codex adds `eyes` while reviewing and adds `+1`/👍 when
the current head is clean. A user-authored `@codex review` issue comment is a
trigger and correlation record; it is not the clean-status anchor.

When the PR description already has the bot's `eyes` reaction, treat the pass
as already running, monitor that PR description entry, and do not post a
duplicate `@codex review`. A `+1` reaction on the trigger comment alone never
completes the loop.

After posting a literal `@codex review`, treat that recent trigger as a
monitoring state until Codex posts a reaction, summary, inline feedback, or a
quota response. Do not post a second trigger merely because the status reaction
has not appeared yet.

The detector distinguishes two pending states: `requested_unacknowledged`
means the trigger has no observable Codex activity yet; `running` means Codex
has acknowledged the pass with `eyes`. Both are pending, so a quiet poll or
timeout must hand monitoring forward rather than return a completion result.
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
  `eyes`/👍 state and completion;
- trigger anchor: the `@codex review` comment that requested the pass, used only
  to correlate feedback and timestamps.

Use the recorded pass/head association or explicit reviewed commit to establish
current-head identity; commit creation time is insufficient.

Treat reactions from `chatgpt-codex-connector[bot]` on the PR description as
state:

- `eyes`: review is in progress; keep polling even if no review body exists;
- `+1`/👍 with no remaining `eyes`: clean signal when no newer actionable Codex
  content appeared and the signal belongs to the current PR head.
- Any newer timestamped Codex reaction is activity evidence for quota-age
  classification, but is not by itself a clean signal.

Do not use a `+1` on an `@codex review` trigger comment as the terminal signal.
A textual `Didn't find any major issues.` summary is useful corroboration, but
the loop remains non-terminal until the current PR description also receives
the bot's clean `+1` reaction.

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
  body, or current-pass summary. This is not terminal until the PR description
  receives the bot's current-head `+1` reaction.
- Non-actionable summary: a new Codex review summary for the current pass with
  no inline/location-tied findings.
- Operational block: the bot's usage-limit comment after the latest literal
  `@codex review` trigger. This is neither feedback nor a clean result.
- Ignore for action: stale summaries from older anchors and summary cards with
  no concrete requested change.

If GitHub reports the PR as merged or closed, the detector returns
`review_closed`. This stops remote review work. It does not retroactively prove
a clean review, particularly when new findings and merge happened concurrently.
