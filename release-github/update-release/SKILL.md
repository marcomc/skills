---
name: update-release
description: Prepare a project's next release metadata by reconciling completed work, TODO, changelog and version sources against fresh mainline, tag and GitHub release evidence. Use before a release preparation commit or PR; publication is a separate authorized handoff.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Update Release

Prepare one reviewable release delta. Invocation authorizes preparation within
the user's task; it does not authorize commits, pushes, merges, tags, releases,
issue/Sheet writes or deployment. Preserve unrelated work and published history.

## Establish scope and completion

1. Inspect project instructions, release policy, configured remote and
   authoritative mainline/release target, TODO, changelog and version sources.
   Resolve the actual target from repository configuration or CI; an upstream
   feature branch is not evidence of the release target. Ask only if ambiguity
   blocks progress.
2. Check the current chat for relevant work history. Inspect available context
   and any directly relevant accessible continuation; report `available`,
   `partial` or `unavailable` with its coverage. Continue with repository and
   verification evidence when history is absent. Do not require chat exports or
   search unrelated chats. Chat claims and removed TODO rows are leads, not
   completion proof.
3. Map the user's scoped work to code/diff, meaningful checks and source items.
   Retain stable source IDs and issue URLs verbatim. Only independently verified
   completed work leaves active TODO; keep unfinished, blocked and uncertain
   tasks active. Removing a row does not close an issue. For external TODO stores,
   prepare a proposed delta unless write authorization already exists.
4. Write concise user-facing notes for completed changes. Preserve unrelated
   Unreleased notes, unfinished tasks, historical release sections and optional
   heading suffixes. Move existing selected note blocks with their exact source
   metadata comments and issue labels/URLs, preserving parser-owned markers
   once rather than replacing them with prose IDs. Keep completion evidence in
   the private plan, not release
   prose. Read [Portfolio adapter](references/portfolio.md) only when that
   optional integration is actually present.

## Choose a provisional version

Read [planning and guards](references/planning.md) before creating a version
plan. The bundled Python helper supports stable SemVer, Markdown release
headings and exact scoped text edits; use project-native tools for other formats
while retaining the same baseline, delta and freshness guards.

- Inspect fresh remote tags, target metadata and the latest **actually
  published** GitHub release before selecting a version when access exists.
  Separate stable publications, prereleases, drafts and unavailable/partial
  coverage. A stale local changelog or GitHub's latest publication alone is not
  the baseline: release metadata already integrated into mainline also counts.
- Default to **MINOR**. Choose **MAJOR** for incompatible changes and **PATCH**
  only for bugfix-only scope. Ground the reason in the actual completed changes.
  Honor an explicit version or documented project policy exactly; report a
  collision or incompatible policy rather than silently changing it.
- Keep the scoped notes independent of the candidate number. Record baseline
  SHAs/versions, tag objects, release identities/states, coverage, version reason
  and expected edits. Label the result provisional. With unavailable remote or
  GitHub evidence, local proposals may proceed; committing and publication stay
  blocked until required freshness is verifiable.

## Prepare and validate metadata

Apply only the reviewed planned edits: selected TODO removals, selected notes
under the candidate heading and applicable version sources. A scoped release
must not sweep unrelated Unreleased notes into its version. Retain an Unreleased
section according to project convention. Reconcile lock/generated metadata
through the project's toolchain, then validate the complete release delta.

Immediately before a preparation commit or PR publication, refresh remote,
target, tags and release evidence and check the exact edits. If another
worktree/machine advances any baseline, preserve the scope manifest, integrate
the current target, reconcile only this plan's edits and generate a fresh plan.
An explicit version conflict needs a user/project-policy decision. Never
renumber unrelated sections, force-push or overwrite a published tag.

Run project-required checks and any requested pre-PR review on the complete
scope. A check result has a timestamp and inputs; it is not a reservation.

An already reconciled feature branch is supported: completed TODO entries may
already be absent and their notes may be in a new Unreleased section. The helper
requires fresh target ancestry, committed local metadata at the scoped code
HEAD, explicit completion evidence and a captured target/local diff. It permits
scoped completed-item removals and additive pending notes/tasks while rejecting
unrelated target deletions, historical edits and unreviewed working-file drift.

When the project prepares final metadata after code review, keep the PR's
earlier version provisional. The final version/changelog commit creates a new
HEAD: run affected local gates and required remote review for that exact HEAD
before merge. Reenter the existing review/remediation owner; an earlier clean
review does not cover the metadata commit. A draft-to-Ready event starts only
the review workflow authorized by the user/project; it grants no merge or
release authority by itself.

## Publication handoff

Metadata preparation in a PR and final publication are separate operations.
After verifying the actual merge/integration and its resulting target commit,
bind the plan to that exact clean remote release-target commit. Invoke
`$create-github-release` with the bound plan under separate release authorization;
the compatible publisher runs fresh guards inside its held gate at each
mutation boundary. If it is absent, preparation remains usable; report the
unavailable publication dependency.

For the managed same-host pipeline, the publisher's default common-Git-directory
lock serializes cooperating worktrees/processes through readback. Report that
it does not exclude separate clones, other machines or bypassing clients. Use
its approved external shared-gate adapter only when stronger multi-host
coordination is required. A local lock or assertion flag cannot establish that
stronger guarantee. The planning helper installs no CI and never publishes.
See [planning and guards](references/planning.md) for binding and recovery.

## Report

Return the scope and completion evidence, TODO/notes/version changes, candidate
and reason, baseline and GitHub state, chat coverage, exact validation results
and outstanding gates. Distinguish `prepared`, `stale`, `unverifiable` and
`publication-ready inside the configured gate`; local readiness grants no
publication authority. Provide plan/artifact paths without exposing credentials
or private evidence in public notes.
