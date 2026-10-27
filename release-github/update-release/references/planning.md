# Planning and guards

## Local plan

The helper uses Python 3.9+, Git and optional authenticated `gh`. It performs
remote reads and fetches target objects without changing branches, tags,
tracking refs or the index. It writes only an explicitly requested **new** plan
file. Keep plans and manifests private, preferably under the worktree's Git
directory; they contain source evidence and file preimages. The helper never
edits project files, commits, locks a server or calls a publisher.

The helper accepts committed feature-branch metadata ahead of the current
target, including a completed TODO row already removed and its ID/issue-linked
note already in Unreleased. It records both target and local preimages, their
exact diff/hash, scoped code HEAD and completion evidence. Current target must
be an ancestor of that HEAD. Local working files must equal their committed
preimages; prepare the reviewed code first, then plan the final metadata delta.

Completed scoped blocks may already be absent. Other target TODO/pending lines
must remain in order; additive local tasks/notes are retained. Historical
sections and preamble remain exact. Configured version files may differ only
in the matched version value. Reverted unrelated target content is rejected
even when committed on the feature branch. A missing Unreleased section is
created without moving unrelated notes into the candidate. There is no safety
assertion bypass; unsupported transformations need a separately evidenced
project-native adapter.

Configure the verified target and the version sources that actually apply:

```json
{
  "remote": "origin",
  "target": "main",
  "changelog": "CHANGELOG.md",
  "tag_prefix": "v",
  "version_sources": [
    {"path": "package.json", "pattern": "\"version\"\\s*:\\s*\"(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)\""}
  ]
}
```

Each regex must identify exactly one named `version` group; use project-native
tooling for generated files, monorepos or other schemes. Explicitly enumerate
applicable generated files too, or review their independent validation before
committing. For GitHub Enterprise, set `github_host` to the verified hostname
matching the remote. SSH aliases and non-GitHub remotes need an adapter with
independently verified identity; the helper reports GitHub unavailable for them.
Different fetch/push destinations are ambiguous and block guards.

The scope manifest separates evidence from release prose:

```json
{
  "chat": {"status": "unavailable", "coverage": "No relevant chat context in this run."},
  "items": [
    {
      "id": "SRC-42",
      "completed": true,
      "kind": "feature",
      "summary": "Add filtered exports.",
      "issues": ["https://github.com/example/project/issues/42"],
      "evidence": ["Export implementation diff and passing filtered-export checks"],
      "todo": {"path": "TODO.md", "entry": "- [ ] SRC-42 Add filtered exports.\n"},
      "unreleased": "- Add filtered exports.\n"
    },
    {
      "id": "SRC-43",
      "completed": false,
      "kind": "fix",
      "summary": "Retry failed uploads.",
      "issues": [],
      "evidence": [],
      "todo": {"path": "TODO.md", "entry": "- [ ] SRC-43 Retry failed uploads.\n"}
    }
  ]
}
```

Supported kinds are `breaking`, `feature`, `fix` and `other`. Verify evidence
yourself before setting `completed`; the helper does not adjudicate claims.
`todo` and `unreleased` are optional **exact complete text blocks**, unique when
present; a completed entry may already be absent. Include child lines belonging
to the item. An existing scoped Unreleased note must be mapped explicitly so
its ID is not left behind in pending notes. Omit `todo` for an external store
and reconcile it through its authorized adapter. The helper retains incomplete
items and removes only explicit completed-item blocks.
Selected existing note blocks move with their source-metadata comments and
visible issue labels/URLs intact. Missing ID/URL references are appended without
reconstructing the original block. This preserves parser-owned metadata as
metadata rather than substituting a parenthesized ID string.

```bash
skill_dir="${HOME}/.agents/skills/update-release"
plan_dir="$(git rev-parse --git-path update-release)"
mkdir -p "$plan_dir"
python3 "$skill_dir/scripts/release_plan.py" plan \
  --config "$plan_dir/config.json" --scope "$plan_dir/scope.json" \
  --date 2026-10-27 --output "$plan_dir/prepare.json"
python3 "$skill_dir/scripts/release_plan.py" diff --plan "$plan_dir/prepare.json"
```

Use the project's release date/timezone. Review and apply that diff with normal
file tools. `--version X.Y.Z` honors an explicit version; `--bump major|minor|patch`
with `--policy-reason 'documented policy and source'` selects a documented policy.
The default reason derives from the completed items. An occupied or non-forward
explicit version fails rather than being silently replaced.

The JSON records current target SHA, target file hashes/versions, relevant
remote tag objects, published releases, prereleases, drafts and draft visibility.
`latest_published` uses publication time; `latest_stable` excludes prereleases.
The stable baseline is the highest stable version in target metadata, remote
tags or published stable releases. Prereleases/drafts reserve their version
cores without being treated as stable publications. Divergent current target
version sources require reconciliation. Two consecutive remote observations
must agree; this catches observed changes during collection, not all races.

Before committing or publishing the metadata PR:

```bash
python3 "$skill_dir/scripts/release_plan.py" check \
  --plan "$plan_dir/prepare.json" --phase commit
```

This requires complete remote/GitHub evidence including draft visibility,
unchanged baseline, target ancestry, unchanged scoped code HEAD and exact
expected working-tree edits.
Inspect the actual staged/PR diff as well: the helper does not stage files or
prove that all release edits are staged. Recheck immediately before publication
if review or other work intervenes.

If the code PR is reviewed before final release metadata is committed, treat
that earlier version as provisional. After the version/changelog commit,
refresh affected local checks and obtain any required remote review on the new
exact HEAD before an authorized merge. The helper proves metadata/freshness
conditions only; it cannot certify a remote review or infer merge authority.
Reuse the project's existing review owner instead of starting another loop.

On stale plans, keep the original scoped manifest. Reconcile the plan's own
generated edits against their preimages, integrate the latest target, then
generate a new plan at a new path and reapply the scope once. Preserve concurrent
notes. Never use a fresh snapshot to bless an old version without recomputing
the candidate and edit expectations. Local proposals with missing access remain
provisional; every commit/publication guard fails closed on missing evidence.

## Final target binding and serialization

After verifying the metadata PR's actual merge/integration and after release
publication is separately authorized, use a clean checkout at the authoritative
target with a matching upstream. Bind the original preparation plan:

```bash
python3 "$skill_dir/scripts/release_plan.py" bind \
  --plan "$plan_dir/prepare.json" --output "$plan_dir/publish.json"
```

Binding permits the target SHA to advance only when it descends from the saved
baseline and all planned files on the target equal the expected prepared content.
Existing tags/releases must retain their saved identities. Added publications
trigger a fresh version calculation that excludes only this plan's exact
integrated candidate metadata; the calculated candidate must still equal the
prepared version. This allows an intermediate release to catch up without
bumping again merely because this plan is already integrated. The new remote
state becomes publication baseline. If content differs or the candidate changes,
reconcile and replan; do not weaken comparisons or fold in unrelated notes.

Under separate release authorization, invoke the compatible publisher:

```bash
python3 "${HOME}/.agents/skills/create-github-release/scripts/create_release.py" \
  --plan "$plan_dir/publish.json"
```

The final guard requires a bound plan, clean HEAD exactly at the remote target,
matching upstream/destination, unchanged target/tags/releases, exact expected
files, an unused candidate tag/version, and no unaccounted intermediate concrete
changelog releases. Missing intermediate publications must be handled using the
existing publication workflow before explicitly binding the original preparation
plan again to a new output path; this helper does not skip them. A saved bound
plan remains stale until that fresh binding succeeds.

The publisher holds a default same-host lock in the common Git directory
through fresh guards, exact tag push, release write and readback. It recognizes
only its journaled/read-back tag and newly created release while comparing the
saved baseline; unrelated remote state remains stale. Use the same publisher
for cooperating processes/worktrees. Separate clones, other machines and clients
bypassing it are outside this exclusion guarantee; non-force tag pushes and
fresh reads detect observed collisions without claiming global atomicity.

The optional external adapter provides stronger coordination only when its
approved live verifier establishes the real shared lease/writer/target policy.
Preparation requires no infrastructure changes. See the installed
`create-github-release/references/guarded-publication.md` for the gate protocol
and private intent journal. Both skills need to be upgraded together for guard
API version 1. See [GitHub release visibility](https://docs.github.com/en/rest/releases/releases)
for why draft coverage requires push access.

If a tag push, release creation/edit or readback has an uncertain result, halt,
retain the plan/journal and reconcile the exact tag object/peeled commit,
release state and notes using read-only calls. Never replay a failed mutation
or fall back from an ambiguous view/edit to creation. Guarded publication
preserves existing releases. A check, lock or Ready event never grants merge or
release authority; these remain separate explicit approvals.
