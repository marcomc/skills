# Optional Portfolio Ops adapter

Use only when the selected project already has a Portfolio Ops integration.
The core skill has no dependency on a portfolio checkout, Sheet or coordinator.

- Resolve the project's configured active TODO source and stable row/source IDs.
  Preserve IDs and issue URLs in the plan and changelog when moving completed
  scope out of active TODO. Verify implementation and acceptance evidence for
  each source item; an absent Sheet row, closed issue or chat claim alone does
  not establish completion.
- A paused project can accept TODO intake without authorizing implementation.
  Release preparation must keep unfinished work active and preserve unrelated
  Unreleased entries.
- When TODO is a Sheet or another external store, prepare an explicit proposed
  source-ID delta. Actual updates, issue state changes and readback require that
  adapter's existing write authorization and validation. Report external TODO
  reconciliation as pending until verified; a helper check does not prove it.
- Return candidate, scoped IDs, issue links, completion evidence, baseline and
  plan fingerprints, chat coverage, proposed/applied TODO delta and review
  results to the coordinator. Keep preparation, merge, final serialized target
  validation and publication as separate status fields.

Do not change Portfolio Ops configuration or its checkout merely to install or
use this skill. Integration wiring and external write acceptance belong to the
coordinator's separately authorized task.

## Review and publication ordering

| Stage | Required transition |
| --- | --- |
| Code delivery | Deliver the draft PR; any proposed PR version remains provisional. |
| Ready event | The user personally marks the PR Ready; the authorized `codex-pr-review-remediation-loop` starts. |
| Clean code review | Prepare the final version/changelog commit through this skill and the required scoped local gates. |
| New final HEAD | Reenter the same review owner; affected local gates and current-head remote review must pass for the metadata commit too. |
| Merge | Require applicable explicit merge authority and verify the actual merged commit/target; review cleanliness alone grants none. |
| Publication | After separate explicit release approval, bind the original scoped plan to the verified target and invoke `create-github-release --plan`; its held gate covers fresh guards, writes and readback. |

The Ready event starts only review/remediation. The user approves merge and
GitHub Release separately; a clean review and skill invocation supply neither
approval. A check of an earlier PR HEAD or a saved pre-merge plan cannot satisfy
the final publication gate. For cooperating worktrees on one Mac, use the
publisher's default common-Git-directory gate and report its same-host boundary.
Only an approved live external adapter can establish stronger multi-host
exclusion; no CI infrastructure is installed by this adapter.
