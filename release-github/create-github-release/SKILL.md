---
name: create-github-release
description: Use when the user explicitly authorizes creating or updating a GitHub release from prepared local changelog metadata, optionally through an update-release bound plan.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Create GitHub Release

Publish already reviewed metadata under separate release authorization. A Ready
event, clean review, prepared plan or merge approval grants no release authority.
Use `$update-release` for TODO, notes and version preparation; this publisher
does not edit project files or create commits.

## Select the publication mode

Read [guarded publication](references/guarded-publication.md) before executing.
Requires Python 3.9+, Git, authenticated `gh` with push/draft visibility and a
clean branch whose HEAD equals its fresh upstream target. The default gate is
an OS lock in the repository's common Git directory, shared across worktrees
and cooperating publisher processes on the same host. It stays held from target
selection through guards, mutations and readback. It does **not** exclude other
machines or clients that bypass this publisher.

- **Bound plan:** install `update-release` alongside this skill. After verifying
  the actual merge, bind the preparation plan to its exact target. Pass
  `--plan`; the publisher itself invokes fresh plan checks at each mutation
  boundary inside the gate. A preparation plan or mismatched repository, target,
  version or changelog is rejected. Existing releases are preserved.
- **No plan:** retain normal version inference from the first concrete stable
  changelog section, or honor `--version`. Existing stable releases can be
  updated under the explicit release request. Complete reads must prove whether
  a release exists before selecting edit or create.
- **Multiple hosts:** optionally provide an approved live `--gate-verifier`
  and `--gate-lease` for an existing shared service. The verifier must establish
  its lease, writer policy and target fence from that service. Flags, canned
  JSON and a local lock do not establish cross-machine exclusion. No CI or
  access-control infrastructure is installed by either skill.

For the managed single-host pipeline, use the default gate. Report its boundary
explicitly instead of requiring new infrastructure. If the project requires
multi-host exclusion, use the verified external adapter or stop publication
until that requirement is met. Preparation remains usable in either case.

## Publish

```bash
publisher="${HOME}/.agents/skills/create-github-release/scripts/create_release.py"
python3 "$publisher" --plan /path/to/private/publish.json
```

Legacy no-plan use and explicit non-latest publication:

```bash
python3 "$publisher"
python3 "$publisher" --version 1.0.1 --no-latest
```

The normal current release defaults to latest. A historical version below a
published stable version defaults to non-latest; honor explicit `--latest` or
`--no-latest`. Missing documented intermediate publications stop the flow rather
than folding their notes into a newer version. Publish/account for those through
the project policy before continuing; the helper has no continuity-bypass flag.

The publisher verifies exact remote tag object **and** peeled commit before
adoption. A conflicting annotation or commit is a stop. New tags push their
immutable object ID with a non-force explicit refspec; an existing remote tag
is never overwritten. Guarded runs allow only their journaled, read-back tag to
be excluded from the saved baseline after push, then verify the newly created
release without ignoring any unrelated change.

## Failure and report

A failed/incomplete release read means unavailable state, never absence. Edit
failure never becomes creation. Failed writes and failed post-write readback
retain a private intent journal and stop; do not automatically retry or roll
back. A prior unresolved intent blocks another attempt for that repository/tag
across local worktrees. Follow the read-only reconciliation procedure in the
reference; external controllers must also retain unresolved outcomes.

Return release URL, exact version/tag/SHA/upstream, latest status, serialization
mode and journal path. For the default gate, state that cross-host/bypassing
writers are outside its exclusion guarantee. Distinguish verified publication
from attempted/unknown state; skill or gate success is not release permission.
