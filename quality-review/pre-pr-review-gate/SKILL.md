---
name: pre-pr-review-gate
description: Report local readiness for a scoped PR or release change using the shared review coordinator and current evidence. Default to report-only unless remediation is already authorized; do not publish or request remote review.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Gate

Use `$review-coordinator` for the single local quality decision. This entrypoint
sets report-only mode unless the user or calling workflow already authorized
remediation. Preserve the supplied scope, findings, policy revision and evidence.
If a coordinator is active, ask it for the current verdict; do not start another
run, sequence of general reviews or nested fix loop.

The companion `review-coordinator` must be installed alongside this skill.
Its `SKILL.md` owns baseline coverage, risk routing, evidence reuse, remediation
and exit rules. A missing companion is a dependency gap, never a ready result.

Report the canonical status `READY`, `NEEDS_WORK` or `BLOCKED`, scope/base and
current content/HEAD, required gaps, optional recommendations and evidence actually
executed or reused. Use its `references/publication.md` for applicable privacy
checks and release handoff. Required missing evidence cannot be reported as
ready with known gaps.

Local readiness does not authorize a commit, PR, cloud review, release or deploy.
The active coordinator owns the one terminal learning/capture step.
