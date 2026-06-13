---
name: scoped-pre-pr-remediation
description: Use when the user asks to review and fix a whole branch, selected commits, an explicit diff range, staged changes, unstaged changes, or all uncommitted work before PR review.
---

# Scoped Pre-PR Remediation

Use this skill when the user wants one command that reviews a chosen change
scope, fixes the findings, validates the result, and records reusable lessons
in the project instructions and pre-PR review skill corpus.

This is an orchestration skill. The user should not have to mention the
underlying skills. When invoked, automatically compose:

- `$pre-pr-review-gate` for the initial and final gate,
- `$max-findings-relentless` for remediation and fix-test-review loops,
- focused sub-agent review reports by default when the scope is not tiny and
  naturally splits into multiple independent review areas.

## Supported Scopes

Accept any of these inputs:

- whole branch against its merge base,
- explicit commit or commit range,
- selected commits listed by hash,
- staged changes,
- unstaged changes,
- all uncommitted changes,
- explicit paths or pathspecs within any of the above.

If the user does not specify a scope, use all current branch changes plus
staged and unstaged changes. Do not stash or commit just to create the review
scope.

## Workflow

1. Read all applicable `AGENTS.md` files before reviewing.
2. Resolve the scope and summarize exactly what is included:
   - base branch and merge base for branch scope,
   - commit hashes for commit scope,
   - staged and unstaged file lists for dirty-tree scope,
   - path filters if provided.
3. Identify whether the resolved scope contains multiple review areas. Treat
   areas as separate only when they have mostly disjoint files, tests,
   ownership, or risk models, such as backend/frontend, infra/runtime code,
   docs/tooling, or independent packages.
4. Map each review area to the smallest useful specialized reviewer profile.
   Prefer one primary profile and at most one secondary profile per area:
   - `$pre-pr-review-frontend` for browser UI, client state, CSS, templates,
     frontend builds, and user-facing interactions.
   - `$pre-pr-review-backend-services` for APIs, workers, persistence, domain
     logic, validation, and service integrations.
   - `$pre-pr-review-infra-runtime` for Ansible, Terraform, Docker, Compose,
     Workspace, Jenkins, systemd, deployment, service lifecycle, and OS package
     support.
   - `$pre-pr-review-security-boundaries` for auth, authorization, secrets,
     trust boundaries, privileged actions, telemetry, permission prompts, and
     read-only paths that call capable helpers.
   - `$pre-pr-review-tests-validation` for tests, fixtures, smoke checks,
     harnesses, validation scripts, and focused coverage-gap passes.
   - `$pre-pr-review-docs-release` for README, changelog, release notes,
     examples, operator docs, versioning, and PR-readiness text.
   - `$pre-pr-review-config-data-flow` for config keys, defaults, schemas,
     templates, override files, manifests, generated files, identifiers, and
     URL/path handling.
   - `$pre-pr-review-cli-tooling` for shell, Makefile, command wrappers,
     argument pass-through, installers, uninstallers, and local automation.
   - `$pre-pr-review-ci-actions` for GitHub Actions, reusable workflows,
     check logs, matrices, caches, artifacts, and workflow permissions.
   - `$pre-pr-review-agent-workflows` for `AGENTS.md`, `SKILL.md`, prompt
     templates, Codex automation guidance, learning hooks, and agent workflow
     boundaries.
5. When there is more than one review area and sub-agents are available, assign
   report-only sub-agents to the independent areas by default while the main
   chat keeps one blocking or cross-cutting area locally. Treat the user's
   invocation of this remediation skill as enough authorization for report-only
   sub-agents unless they explicitly opt out. Skip sub-agents only when the PR
   is really tiny or the areas cannot be separated cleanly. A really tiny scope
   is a single-risk change such as one or two small files, a docs-only wording
   fix, or a narrowly obvious patch where sub-agent setup would be larger than
   the review itself. If unsure, dispatch at least one report-only sub-agent.
   Include the selected reviewer profile instructions in each sub-agent brief.
   Each sub-agent must:
   - review only its assigned pathspecs or commits,
   - avoid editing files,
   - report findings with severity, file references, evidence, proposed fix, and
     narrow validation,
   - flag any finding that may overlap another area.
6. Keep the main chat as orchestrator. It owns the shared context, consolidates
   sub-agent reports, deduplicates findings, chooses the remediation order, and
   applies the actual code or documentation changes. Before each remediation,
   re-read the impacted files and current diff so fixes are based on the latest
   integrated state.
7. Prevent conflicts between remediation areas by maintaining a short
   integration ledger:
   - area name and assigned pathspecs,
   - selected reviewer profile or profiles,
   - findings accepted or rejected,
   - files already edited by the orchestrator,
   - checks already run,
   - remaining cross-area risks.
8. If two findings touch the same file, behavior contract, test fixture, config
   key, or generated artifact, merge them into one orchestrated fix instead of
   applying them independently. After each fix, update the ledger and revisit
   later findings whose assumptions may have changed.
9. If sub-agents are unavailable, explicitly declined by the user, skipped for
   a really tiny PR, or the areas cannot be separated cleanly, run the same
   review-area structure and specialized profile guidance sequentially in the
   main chat.
10. Run `$pre-pr-review-gate` against that scope. If a helper only supports
   committed branch diffs, supplement it with direct review of `git diff`,
   `git diff --staged`, or the requested commit range.
11. Consolidate gate and sub-agent findings into blockers, strong
    recommendations, cleanup suggestions, and validation gaps.
    - When the scope moves private values into ignored/local override files,
      check whether tracked placeholders still flow into runtime config,
      generated files, numeric fields, service defaults, or validation paths.
      Safe non-private defaults should remain deployable unless the value is
      truly secret, local-only, or explicitly gated before use.
    - When a feature is intended to be disabled or opt-in, compare runtime
      gates against every surfaced default: installer-copied templates, schema
      defaults, docs, discovery payloads, and any helper/CLI modes. Ensure the
      default path is inert and does not leak user-specific telemetry.
    - When commands write a dedicated registry file that is later merged with
      broader config globs, test add/update/remove/import against the effective
      runtime config. Commands must fail clearly when another config file
      shadows the same key, and generated outputs must validate path or
      filename collisions across the whole effective config.
    - When "read-only" or telemetry paths call helpers, ensure they never use
      authorization/prompt-capable modes by accident. Add negative-path tests
      proving no UI prompts, permission requests, or other side effects occur.
    - When wrappers forward raw CLI pass-through arguments, do not parse them
      with `eval` or shell code. Tokenize as data (for example, `shlex.split`)
      and add a regression guarding against reintroducing `eval`.
    - When remediating support-matrix or dependency findings, validate through
      the real target package-manager path (apt/yum/dnf/etc). Do not assume
      static package names or ignore minimal-package conflicts.
    - When changing URL/path encoding, confirm escaping does not also change
      normalization or any other externally meaningful identifier
      representation (for example, preserving the stored filename form).
    - When adding stale-check manifests, sync validators, or deploy-input
      inventories, include ignored-but-required runtime inputs (for example,
      private override files) and validate any host tooling against macOS/BSD
      portability constraints.
    - For Jenkins pipeline diffs, inspect workspace cleanup in `post` blocks
      and verify every scripted node/agent switch either checks out SCM or
      restores needed files before running repository-local scripts.
    - For Jenkins pipeline diffs, treat publication, live-test, cleanup, and
      release-version toggles as explicit per-build operator controls. Prefer
      typed build parameters (or an equivalent explicit input surface) over
      fixed Jenkinsfile environment defaults.
    - When Jenkinsfile changes the control surface (parameters vs env defaults
      vs wrapper scripts), reconcile any CI/release docs and runbooks with the
      new behavior so operators are not relying on stale parameter wording.
    - For Workspace-first Jenkins diffs, trace every Jenkins-invoked workspace
      helper through its nested implementations and verify toolchain binaries
      run inside the intended container boundary, not on the Jenkins host.
    - For Workspace-first Jenkins diffs, validate the real running container
      environment after service creation (`enable`, `up`, `recreate`, etc.),
      not only `docker compose config` interpolation output.
12. Remediate blockers and accepted recommendations with
    `$max-findings-relentless`, using the orchestrator ledger to keep context
    focused between areas and avoid conflicting edits.
13. When editing `CHANGELOG.md` during pre-PR remediation, preserve the
    repository's existing release-note structure:
    - if an `Unreleased` section already exists, add the new entry there;
    - if no `Unreleased` section exists and the latest concrete release section
      is acting as the pending PR release body, add or merge remediation notes
      into that latest concrete release section instead of creating a new
      `Unreleased` section;
    - if the user says the branch is being prepared for a release PR, preserve
      the repository's concrete dated release heading format, such as
      `## [X.Y.Z] - YYYY-MM-DD - Title`; do not rewrite it to `vX.Y.Z` or
      `Unreleased` unless the user explicitly requests that format;
    - compact repeated entries about the same feature, command, credential,
      workflow, or documentation surface into reviewer-readable bullets or
      grouped subsections.
14. Run the narrow checks for each fix, then the repository's standard quality
    gate when available.
15. Rerun the pre-PR gate on the final scope after the last code change.
16. Extract reusable lessons from the findings and fixes.
17. Update the most relevant project `AGENTS.md` with repo-local prevention
    rules, and update reusable pre-PR skills when the lesson is generic enough
    to prevent future Codex review findings before they reach GitHub.
18. Validate every Markdown, shell file, or `SKILL.md` edited by the
    remediation.

Do not ask the user to repeat the composed skill names. Only ask for scope
clarification when no reasonable default can be inferred.

## Scope Resolution

Use these commands as inputs for review, adapting to the repository:

```bash
git status --short
git diff --stat
git diff --staged --stat
git diff <base>...HEAD --stat
git show --stat <commit>
```

For commit scopes, inspect the exact patches with `git show` or
`git diff <start>..<end>`. For uncommitted scopes, inspect both staged and
unstaged diffs.

## Multi-Area Review Orchestration

Use sub-agents by default for independent review evidence on non-tiny,
multi-area scopes, not for unsupervised edits. Give each sub-agent a bounded
assignment with:

- the exact pathspecs, commits, or diff range to inspect,
- the relevant `AGENTS.md` instructions,
- the selected specialized reviewer profile instructions,
- a no-edit instruction,
- required report fields: findings, evidence, proposed remediation, validation,
  and possible overlaps.

The main chat must verify each reported finding against the current local files
before fixing it. If a sub-agent proposes a fix that would touch files outside
its area, treat it as cross-area work and fold it into the orchestrator ledger.

## Specialized Reviewer Routing

Use reviewer profiles as reusable prompt context for report-only review agents.
They are not independent orchestrators and do not replace `$pre-pr-review-gate`
or `$max-findings-relentless`.

| Diff signal | Primary profile | Common secondary profile |
| --- | --- | --- |
| UI, templates, CSS, client state, browser tests | `$pre-pr-review-frontend` | `$pre-pr-review-tests-validation` |
| APIs, jobs, persistence, domain logic | `$pre-pr-review-backend-services` | `$pre-pr-review-config-data-flow` |
| Docker, Ansible, Jenkins, Workspace, deploy, packages | `$pre-pr-review-infra-runtime` | `$pre-pr-review-cli-tooling` |
| Auth, secrets, privileged actions, telemetry, prompts | `$pre-pr-review-security-boundaries` | `$pre-pr-review-tests-validation` |
| Config keys, schemas, defaults, generated artifacts, URLs | `$pre-pr-review-config-data-flow` | `$pre-pr-review-docs-release` |
| Shell, Makefile, installers, wrappers, local automation | `$pre-pr-review-cli-tooling` | `$pre-pr-review-infra-runtime` |
| GitHub Actions, CI logs, workflow permissions, matrices | `$pre-pr-review-ci-actions` | `$pre-pr-review-infra-runtime` |
| `AGENTS.md`, `SKILL.md`, prompt workflows, learning hooks | `$pre-pr-review-agent-workflows` | `$pre-pr-review-docs-release` |
| README, changelog, runbooks, release metadata | `$pre-pr-review-docs-release` | `$pre-pr-review-tests-validation` |
| Test harness, fixtures, validation scripts, smoke checks | `$pre-pr-review-tests-validation` | Area-specific implementation profile |

If a security, config, or validation risk crosses multiple file areas, keep it
in the main chat instead of handing it to a sub-agent with incomplete context.
If a later remediation phase dispatches edit-capable sub-agents, include
`$pre-pr-remediation-worker` in those worker prompts so report-only reviewer
profiles are not mistaken for permission to edit broadly.

## Learning Rules

Only add lessons to `AGENTS.md` when they are reusable for future development.
Do not paste one-off bug details, PR history, or file-specific trivia.

Do not stop at `AGENTS.md` when a finding reveals a generic blind spot in the
local review process. In that case, update the smallest relevant reusable
pre-PR skill as well, usually one of:

- `$pre-pr-review-gate`,
- `$scoped-pre-pr-remediation`,
- a composed review or regression-planning skill that should have caught the
  class before GitHub Codex did.

Use `AGENTS.md` for repository conventions and reusable skills for cross-repo
review heuristics, validation requirements, and remediation workflow rules.

Good lessons are:

- generic enough to apply across the project,
- grounded in a real finding from the remediation,
- actionable during future implementation or review,
- short enough to be read before work starts,
- placed in the most relevant local `AGENTS.md`.

Bad lessons are:

- only about one deleted line or one temporary branch,
- long retrospectives,
- blame-oriented notes,
- duplicate rules that already exist,
- rules that conflict with repository conventions.

Prefer language like:

- "When adding config keys, update load, write, validate, examples, docs, and
  installer rewrite paths in the same change."
- "When adding privileged web actions, include an explicit trust boundary,
  authorization check, CSRF/origin protection, and tests before exposing them."
- "When a feature is disabled, installer-created privileges and helper
  artifacts must be skipped or removed, not merely unused."

## Output Requirements

Return:

- reviewed scope,
- review areas and sub-agent reports used or skipped,
- findings fixed,
- cross-area conflicts merged or avoided,
- final gate status,
- validation commands run,
- `AGENTS.md` lessons added or updated,
- reusable pre-PR skill lessons added or a no-op rationale,
- unresolved risks or validation gaps.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
