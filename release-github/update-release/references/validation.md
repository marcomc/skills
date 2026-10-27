# Validation

Run from the skill directory:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
```

The suite uses disposable bare Git remotes and worktrees. GitHub responses are
isolated fixtures; no live tags, releases or other external writes occur.

| Behavior | Observable check |
| --- | --- |
| Competing worktrees from one baseline | Both propose the same candidate; the second guard fails after the first target advances. |
| Release/target/tag advances | Fresh guards reject saved plans; replanning recomputes the version. |
| Target metadata ahead of public release | Candidate follows target version; missing intermediate publications block final publication. |
| Available, partial or absent chat | Scope preserves explicit coverage; missing history does not block preparation. |
| GitHub absent or draft visibility unknown | Local proposals remain possible; commit/binding/publication cannot pass. |
| Drafts and prereleases | They remain distinct from stable publications and reserve conflicting versions. |
| Incomplete TODO and unrelated notes | Incomplete items and unrelated Unreleased entries remain; completed entries retain IDs/URLs in release notes. |
| Source metadata and history | Version sources update together; disagreement, lost history and edited plan expectations fail. |
| Feature-branch preimages | Already reconciled TODO/notes and a new Unreleased section produce a captured target/local delta and a bindable plan. |
| Source metadata | Exact persistent HTML identity comments and existing issue labels/URLs move once with the original note block, through final target binding. |
| Stale local preimages | Uncommitted metadata and committed reverts of unrelated target notes/tasks are rejected. |
| Final target | Binding and clean exact-target checks precede publication validation. |
| Intermediate publication catches up | Fresh binding recomputes the candidate from unchanged integrated scope; stale bound plans still fail. |
| Read-only helper and private plans | Planning preserves files/index/refs; plan creation is exclusive with mode `0600`. |

For independent forward-testing, give a separate agent a realistic release
request, this skill and minimal raw project artifacts in a temporary workspace.
Include verified and unfinished work, unrelated notes, multiple worktrees and
changing remote state. Inspect its actual edits and decisions; do not substitute
wording assertions for task execution.

These checks establish local preparation and stale-plan rejection. The paired
publisher suite also runs two real worktree processes through the default
common-Git-directory gate, using local transport and a synthetic GitHub service.
They do not establish multi-host exclusion, production gate policy, live
publication or external Portfolio TODO writes. Verify those when required by
the selected project under its separate authorization.
