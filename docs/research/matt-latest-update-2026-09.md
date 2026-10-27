# Matt Pocock skills: latest-update check

Checked: 19 September 2026

## Scope

This separates the latest published release from the untagged work on `main`.
That distinction matters for `npx skills update`: a release is the dependable
version boundary, while `main` can contain unfinished skills.

## Latest published release: v1.2.3

The latest tag is [v1.2.3][v1.2.3], published on 6 August 2026. Its immediate
predecessor is [v1.2.2][v1.2.2]. The [release comparison][release-diff] shows
that **no skill was added, removed, renamed, promoted, or demoted** in v1.2.3.

It made three patch-level behaviour changes:

| Skill(s) | Change |
| --- | --- |
| `diagnosing-bugs` | Require redaction of secrets in commands, outputs, and captured artifacts. |
| `code-review`, `codebase-design`, `improve-codebase-architecture` | Make subagent-dispatch instructions harness-neutral rather than Claude-Code-specific. |
| `wizard` | Remove time estimates and show progress as stages instead. |

The official [v1.2.3 changelog][changelog] is the source for those three items.

## Untagged `main` changes since v1.2.3

`main` is still versioned `1.2.3` and has unreleased changesets. It adds three
skills, all in the **`in-progress`** bucket, so they are experiments rather
than additions to the supported/promoted set:

| Skill | Invocation | Intent | Status |
| --- | --- | --- | --- |
| `implement-spec` | User | Drive a spec and its ticket dependency graph to one PR using implementation and merger subagents. | In progress; unreleased. |
| `pr` | Model | Reference/template for a scan-friendly PR body based on the issue or spec. | In progress; unreleased. |
| `retro` | Model | Retrospective that moves mechanical standards findings into deterministic checks. | In progress; unreleased. |

No skill has been removed or renamed after v1.2.3. These entries are visible
in the current [in-progress skill tree][in-progress] and pending
[changesets][changesets]. Do not treat them as part of an ordinary update until
Matt promotes and releases them.

## `/grill-me` remains supported

Yes. It is not deprecated or replaced.

`/grill-me` remains a promoted, user-invoked productivity skill. Its purpose
is unchanged: it is a thin named wrapper that calls the reusable,
model-invoked [`grilling` primitive][grilling]. The only current source change
is clearer invocation wording: “Call the Skill tool with `grilling`”.

Matt's current router makes the choice explicit:

| Situation | Recommended entry point |
| --- | --- |
| No working directory: plan, design, writing, or any non-repo discussion | `/grill-me` |
| Working in a repository | `/grill-with-docs` |
| Need the bare interview primitive, with no wrapper | `/grilling` directly |
| Huge, foggy greenfield effort or feature that exceeds one session | `/wayfinder` |

`/grill-with-docs` does not replace the interview method. It runs the same
`grilling` primitive and adds `/domain-modeling`, leaving `CONTEXT.md` and ADRs
as a durable paper trail. `/wayfinder` also does not replace grilling: it is
the heavier decision-map flow for work too large to hold in one session, and
its route re-enters the normal flow at `/to-spec`.

The [current `ask-matt` router][ask-matt] calls `/grill-with-docs` the default
for repository work and reserves `/grill-me` for work without a working
directory. The [README][readme] still describes both as the main alignment
skills and recommends using them before making a change.

## Practical update interpretation

Updating from v1.2.2 to v1.2.3 does not change which Matt Pocock skills you
have selected. It brings the safe redaction rule, cross-harness subagent
language, and Wizard progress simplification. It does **not** remove
`grill-me`, and it does not require switching to Wayfinder.

[ask-matt]: https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md
[changesets]: https://github.com/mattpocock/skills/tree/main/.changeset
[changelog]: https://github.com/mattpocock/skills/blob/v1.2.3/CHANGELOG.md#123
[grilling]: https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md
[in-progress]: https://github.com/mattpocock/skills/tree/main/skills/in-progress
[readme]: https://github.com/mattpocock/skills/blob/main/README.md
[release-diff]: https://github.com/mattpocock/skills/compare/v1.2.2...v1.2.3
[v1.2.2]: https://github.com/mattpocock/skills/releases/tag/v1.2.2
[v1.2.3]: https://github.com/mattpocock/skills/releases/tag/v1.2.3
