---
name: pre-pr-review-gate
description: Run a strict local pre-PR gate by composing project-context-rebuilder, branch-qa-remediation, max-findings-review, diff-regression-check-planner, security-best-practices, stack-best-practices-review, code-quality-remediation, repo-publication-sanitizer, and max-findings-relentless as needed. Use when preparing a branch for PR or before requesting GitHub Codex review, and report whether the branch is locally ready, blocked, or ready with known gaps.
---

# Pre-PR Review Gate

Use this skill to run the highest-signal local gate before opening a PR or spending a GitHub Codex review pass. This is an orchestration skill: it should compose the existing review skills in the correct order, deduplicate overlaps, and produce a clear readiness decision.

## Goal

Reduce avoidable findings before PR review by forcing:

- full project context,
- diff-aware review,
- stack-aware standards review,
- publication/privacy sanitization for public repositories,
- feedback from recent Codex remediations folded back into the pre-review sweep
  and reusable pre-PR skill corpus,
- regression-plan generation,
- area-specific reviewer profile routing for broad diffs,
- targeted remediation loops,
- a final fresh review on the final diff,
- a release-ready handoff that downstream publication skills can trust.

## Default mode

Default to review and reporting. Do not open the PR, request GitHub review, or change code unless the user explicitly asks for remediation after the gate report.

## Required workflow

### 1. Rebuild project context

Start with `$project-context-rebuilder` so the gate is grounded in:

- `AGENTS.md`,
- specs and status docs,
- README and TODO artifacts,
- repository-specific commands and constraints.

### 2. Resolve the diff and local validation commands

- Determine the base branch.
- Scope the branch diff as `merge-base(base, HEAD)..HEAD`.
- Identify the repository's real validation commands from local evidence.
- Separate commands that were actually run from commands that are only recommended.
- Resolve environment-specific wrappers exactly. Distinguish local/dev/staging/prod
  entrypoints and do not treat similarly named recovery or failover commands as
  interchangeable.

For Python repos, explicitly detect:

- the canonical repo gate, such as `make check`,
- whether the project uses `pytest`, `ruff`, `mypy`, and `uv`,
- whether `pyproject.toml`, example configs, install/bootstrap scripts, or packaged assets changed,
- whether `AGENTS.md` requires live validation for any touched surface.
- whether a CLI/config change introduced new argument combinations, sentinel
  values, worker cleanup paths, or filesystem/persistence migration logic that
  need direct smoke coverage through both read and write entrypoints.
- whether the diff touches host-state probes, alerting, diagnostics, adapter or interface selection, hostname handling, or OS-command parsing that can diverge between a user-facing identifier and the low-level identifier the underlying tool actually expects.
- whether the diff changes user-visible labels, options, descriptions, alert
  text, status banners, or errors that must stay synchronized across CLI, web,
  localization catalogs, and tests.

For workspace, harness, compose, service-lifecycle, or dual-node HA repos,
explicitly detect:

- whether touched files alter `workspace.yml`, wrapper env forwarding, harness
  config, compose templates, host-group vars, or service enablement contracts;
- whether the canonical validation path is container-backed and must include the
  real `enable` or bootstrap step before deploy or test;
- whether a direct narrow playbook run can pass while the real wrapper path
  still fails because of stale renders, missing env forwarding, wrong inventory,
  or runtime port collisions;
- whether host and container checks share generated dependency or cache paths.
  Container-backed validation should not consume host-only symlinks, absolute
  paths, or cache entries that break the wrapper after a host linter runs.
- whether the touched surface requires a planned failover, swap, promotion,
  demotion, restore, or recovery scenario instead of deploy-only validation.

For Jenkins pipelines, explicitly detect:

- whether scripted `node {}` blocks run on secondary agents without an
  explicit `checkout scm`, source unstash, or equivalent repository restore
  before invoking repo-local scripts or config files;
- whether `post` blocks delete or replace the workspace before executing helper
  scripts, reading checked-out files, or formatting stashed result artifacts.
- for Workspace-first Jenkins jobs, trace each `ws ...` command invoked by the
  pipeline through the Workspace command implementation and verify that project
  toolchain binaries run in the intended container, not on the Jenkins host.
  Credentials for release and provider helpers should cross the container
  boundary through environment variables, not command-line arguments.
- when Workspace values are surfaced through Compose environment interpolation,
  validate the real service-creation path and container environment. Do not
  assume `docker compose config` or a wrapper command's local shell variables
  prove the running service received the values.
- when Jenkins controls move between build parameters, fixed environment
  defaults, or wrapper commands, compare the Jenkinsfile against CI and release
  documentation so operators are not told to configure controls that no longer
  exist.

### 3. Run the review passes in order

Use these skills in this order:

1. `$branch-qa-remediation` for diff-scoped QA heuristics.
2. `$max-findings-review` for correctness, regressions, and operational risk.
3. `$diff-regression-check-planner` to derive the exact validation plan from the diff.
4. `$security-best-practices` when the change touches exposed or security-sensitive surfaces.
5. `$stack-best-practices-review` for language, framework, library, and project-structure fit.
6. `$code-quality-remediation` when maintainability, duplication, dead code, or file organization are part of the change or review scope.
7. `$repo-publication-sanitizer` when the branch, PR, repository, package, or generated artifacts may become public or externally visible.

Do not let maintainability feedback outrank correctness or regression findings.

### 3.5. Route specialized reviewer focus

When a diff is broad enough to split into distinct review areas, use the
specialized pre-PR reviewer profiles as focus context for report-only passes or
sub-agent briefs. They sharpen review coverage; they do not replace the ordered
gate above.

Use the smallest useful profile set:

- `$pre-pr-review-frontend` for UI, templates, CSS, browser behavior, and client
  state.
- `$pre-pr-review-backend-services` for APIs, workers, persistence, validation,
  and service integrations.
- `$pre-pr-review-infra-runtime` for Ansible, Docker, Compose, Workspace,
  Jenkins, service lifecycle, deploy, and package-manager behavior.
- `$pre-pr-review-security-boundaries` for auth, secrets, privileged actions,
  telemetry, permission prompts, and side-effect boundaries.
- `$pre-pr-review-tests-validation` for fixtures, smoke checks, validation
  scripts, and coverage gaps.
- `$pre-pr-review-docs-release` for README, changelog, release notes, examples,
  operator docs, and versioning.
- `$pre-pr-review-config-data-flow` for config, defaults, schemas, templates,
  generated artifacts, identifiers, and URL/path handling.
- `$pre-pr-review-cli-tooling` for shell, Makefile, installers, uninstallers,
  wrappers, and argument pass-through.
- `$pre-pr-review-ci-actions` for GitHub Actions, matrices, caches, artifacts,
  workflow permissions, and CI logs.
- `$pre-pr-review-agent-workflows` for `AGENTS.md`, `SKILL.md`, prompt
  templates, learning hooks, and agent workflow boundaries.

If review output is later converted into file edits by sub-agents, add
`$pre-pr-remediation-worker` to the edit-capable worker prompt and keep the
main chat responsible for the integration ledger.

### 4. Consolidate findings into one gate report

Deduplicate overlaps and classify results into:

- blockers,
- strong recommendations,
- non-blocking cleanup suggestions,
- validation gaps.
- publication/privacy findings.

Every blocker should name:

- the file or surface affected,
- the failure mode or concern,
- the suggested fix direction,
- the validation required before the branch can be considered ready.

### 4.4. Feed recent Codex findings back into the gate

If the current branch, a recent sibling branch, or the current session already
went through GitHub Codex remediation, convert each actionable finding into a
pre-review prevention item before declaring the branch ready.

If the repository already uses `$codex-review-skill-autolearn`, prefer the
current skill wording as the consolidated source of truth. Tighten the gate
only when the latest Codex remediation exposed a blind spot that has not yet
been folded back into the corpus.

Learning is not complete when it only updates project `AGENTS.md`. Use
`AGENTS.md` for repo-local conventions, but fold generic Codex failure classes
into the reusable pre-PR skills that should catch them before the next GitHub
review. The default reusable targets are:

- `$pre-pr-review-gate`,
- `$scoped-pre-pr-remediation`,
- the composed review and planning skills whose checks should have caught the
  class, such as `$max-findings-review` or `$diff-regression-check-planner`.

For each remediated finding:

- restate it as a generic failure class, not just as one fixed line;
- search the current diff for siblings that could fail the same way;
- add one concrete validation step that would have caught it before GitHub
  review;
- decide whether the durable lesson belongs in project `AGENTS.md`, reusable
  pre-PR skills, or both;
- note whether the class is already covered by the preventable-finding sweep
  below, and expand the sweep when it is not.

Typical examples:

- not-found or invalid-upstream paths must preserve user-visible semantics,
  such as `404` instead of `500`;
- wrapper argument parsing must tokenize input without executing it;
- validators and probes must handle more than one valid content topology, such
  as flat-root and nested layouts.

### 4.5. Run the preventable-finding sweep

Before deciding the branch is ready for external PR review, explicitly check
the final diff for these language-agnostic failure classes:

- sentinel/default round trips: empty, null, omitted, placeholder, `all`,
  `auto`, `default`, `inherit`, and disabled values must keep their meaning
  after normal saves instead of becoming stale concrete values; when a sentinel
  means "inherit" or "use fallback", normalize it before applying defaults so
  fallback-bearing fields do not collapse to empty;
- entrypoint argument routing: mutually exclusive flags, required-together
  options, and alternate command modes must be validated on the real user-facing
  entrypoint so one branch does not pre-empt another before dispatch;
- side-effect mode contracts: dry-run, preview, validate, disabled, no-op, and
  read-only/index/list flows must not mutate external systems, prune generated
  or published artifacts, or launch privileged work;
- tokenizer-vs-evaluator safety: user-controlled CLI, shell, workspace, or
  wrapper arguments must be tokenized as data, not interpreted via `eval`,
  command substitution, shell separators, or similarly executable parsing. If a
  wrapper only supports simple whitespace-separated arguments, reject quoted or
  escaped forms explicitly instead of silently corrupting them;
- background/shared-resource ownership: repeated triggers should not start
  duplicate workers against the same resource, and status messages must match
  whether work actually started;
- async wait-loop termination: polling, callback, retry, and run-loop code must
  exit on terminal error states as well as success and deadline expiry;
- interrupt and cleanup robustness: `Ctrl-C`, cancellation, timeout, and worker
  shutdown paths must not emit secondary tracebacks or leak sibling work during
  best-effort cleanup;
- feature-gated privileges: sudoers, capabilities, credentials, service units,
  helper grants, and install-time policies should be skipped or removed when
  the feature that needs them is disabled;
- opt-in telemetry defaults: example configs, installer-copied templates,
  schemas, docs, and discovery payloads must not activate user-specific
  telemetry, static identities, or auxiliary topics until the user explicitly
  configures the feature;
- disable or teardown symmetry: turning a feature off must also remove or
  invalidate persisted runtime state, generated config entries, cron jobs,
  service units, and other side effects instead of leaving stale behavior
  behind from the previously enabled state; when Makefile targets perform
  ordered install or teardown side effects, put the ordered calls in one recipe
  or mark the flow non-parallel instead of relying on prerequisite order that
  can break under `make -j`;
- stable identity: maps, joins, charts, caches, filenames, and routes should use
  unique IDs where display names or labels can collide;
- batch output collision: rename, copy, export, and generation plans should
  reject two inputs that resolve to the same future target path, even when the
  destination does not exist before the batch starts;
- time/cadence robustness: scheduling code should handle future markers, clock
  skew, stale timestamps, zero/default intervals, and catch-up behavior;
- path migration topology: rename/move/migration logic must reject self-moves,
  descendant moves, and other topology that would nest a directory into itself
  or silently redirect outputs;
- cross-layer limits: schemas, validators, UI constraints, docs, helpers,
  installers, and runtime code should share the same bounds and enum values.
- deployment-input parity: deploy, sync, stale-check, and generated-artifact
  guards must cover every real input consumed by the runtime, including ignored
  or private override files when they affect deploy behavior;
- host-tool portability: shell/workspace gates that run on developer hosts must
  avoid GNU-only flags on macOS/BSD paths unless the dependency is checked or a
  portable fallback is used;
- negative-path semantics: expected misses, stale references, invalid lookups,
  and upstream not-found conditions should produce the intended user-visible
  status or error class instead of leaking generic internal failures;
- valid-topology coverage: probes, validators, importers, and content-serving
  code should handle each supported layout shape, such as flat-root and
  nested-folder inputs, rather than assuming only one topology exists;
- selected-resource probe parity: when one feature selects a specific adapter,
  interface, device, controller, host, route, service instance, credential, or
  client identity, every follow-up probe in that flow must keep using that same
  selected resource instead of silently falling back to a default/global probe
  later in the path;
- identifier translation correctness: when config or UI uses one identifier
  form but an OS or vendor tool expects another, such as interface name vs
  controller address or display hostname vs advertised FQDN, verify the exact
  translation contract and add a regression for the real command shape;
- pre-normalized input handling: values that may already be fully qualified,
  canonicalized, or concrete must not be normalized a second time, such as
  appending suffixes to already-qualified hostnames or reifying `auto`-style
  values into stale concrete ones during later passes;
- encoded artifact URLs and paths: percent-encoding or escaping should preserve
  the stored filename, identifier, or artifact representation, including
  composed versus decomposed Unicode forms, unless the serving layer explicitly
  requires a different canonical form;
- fallback-source preservation: enriched metadata, probes, or sidecar records
  must not replace a fallback source when downstream-critical fields are
  missing, sentinel, or unusable;
- probe/parser output fidelity: command-output parsers must capture the field
  that downstream alerts actually mean to report, not a nearby label, suffix,
  transport marker, or display-only token;
- protocol probe completeness: health, recovery, and readiness probes must
  validate the protocol-level success signal that gates the real workflow,
  such as authentication, authorization, negotiated session, or accepted
  handshake, rather than treating transport reachability as sufficient;
- context-to-message fidelity: when an alert or status carries disambiguating
  context, verify that the rendered operator-facing message changes accordingly
  instead of collapsing distinct failures into one misleading generic string;
- multi-resource asymmetry: for hosts with more than one plausible adapter,
  interface, controller, node, or route, run at least one thought experiment or
  test where the default resource is unhealthy but the selected one is healthy,
  and one where the selected one is missing while some other resource exists;
- warm-spare topology and port ownership: PRIMARY and SECONDARY services that
  can both exist in the same local environment must not claim the same host
  port, volume, project name, or singleton helper resource during create,
  recreate, standby, or promotion flows;
- wrapper and render parity: when settings flow through workspace wrappers,
  generated harness files, env forwarding, and playbooks, verify the rendered
  artifact or live runtime contract, not only the source template;
- environment-targeting safety: commands that look similar across dev and prod,
  especially failover, swap, recovery, deploy, and cleanup entrypoints, must be
  validated for the intended environment and called out explicitly in the gate
  report when mis-targeting would be dangerous.

Treat any untested applicable item as a validation gap even when no code
finding is reported.

When any applicable item involves live services, a source-only review is not
enough. Require the closest real runtime proof the repo supports.

For host-health, adapter-selection, mDNS, command-parser, or alerting changes,
the gate should explicitly ask:

- does every helper in the chain operate on the same selected resource, or did
  one helper drift back to the default host/global view;
- are we passing the identifier that the external command actually accepts, or
  only the identifier that our own config/UI uses;
- what happens when the selected resource is missing but another similar
  resource still exists on the host;
- what happens when the input is already normalized or qualified before our
  code touches it;
- does the final operator-visible message say the exact failure that occurred,
  and are all locales updated if that text changed.

### 4.6. Run the publication sanitizer

For public GitHub repositories, public PRs, open-source packages, shared
examples, or release artifacts, run `$repo-publication-sanitizer` before
declaring the gate ready.

Treat these as blockers unless the user explicitly accepts the disclosure:

- real home paths, local usernames, hostnames, IP addresses, machine names, or
  private service URLs,
- secrets, tokens, credentials, private keys, webhook URLs, or signed URLs,
- hardware identifiers, serials, MAC addresses, Bluetooth IDs, and live device
  inventory tied to the user's equipment,
- copied logs or terminal output exposing user, host, shell prompt, local
  directories, or environment details.

Do not block on intentional public author/license/package metadata, but report
that it was intentionally preserved.

Before reporting a publication/privacy blocker, explicitly distinguish between
real identifiers and already-sanitized placeholders. For example, placeholders
such as `<user>`, `example.com`, project-default `.local` hostnames, obviously
synthetic MACs, reserved/example ranges, fixture values, or values explicitly
labeled as examples should not be treated the same as live operator data.

If sanitized identifiers are intended to remain in public docs, tests, fixtures,
or examples, require them to be easy to spot at a glance. Prefer one or more of:

- placeholder syntax such as `<user>` or `<host>`
- clearly synthetic/example domains, hostnames, addresses, or IDs
- nearby comments or prose that label the value as an example, fixture, or
  sanitized sample
- test/fixture naming that makes non-production intent obvious

If a value appears sanitized but still looks plausibly real enough to confuse a
reviewer, report it as cleanup work to make the sanitization more obvious, even
when it is not a hard publication blocker.

### 5. If remediation is requested, run the fix loop

When the user asks to fix the branch:

- use `$max-findings-relentless` as the main remediation loop,
- if multiple edit-capable sub-agents are dispatched, include
  `$pre-pr-remediation-worker` plus the relevant specialized reviewer profile
  in each worker brief,
- apply focused fixes,
- run the targeted checks from `$diff-regression-check-planner`,
- rerun the real wrapper path if the bug could hide in rendered state, env
  forwarding, service startup order, host-port allocation, or container-backed
  orchestration,
- rerun broader repo checks after the narrow checks pass,
- keep looping until the final review pass is clean enough for PR.

### 6. Require a final fresh pass

After the last code change, rerun at least:

- `$max-findings-review`,
- `$diff-regression-check-planner`.

Rerun `$security-best-practices`, `$stack-best-practices-review`, or `$code-quality-remediation` when the remediation touched their relevant surfaces.
Rerun `$repo-publication-sanitizer` whenever remediation changed docs, examples, scripts, config, logs, metadata, generated reports, or files that will be included in the PR/package.

Never declare the branch ready based only on review results gathered before the final fix batch.

For Python repos, the final pass should normally include the repo gate command plus any diff-specific checks required by config, packaging, installer, CLI, web, or live-validation surfaces.
For CLI, config, concurrency, or migration changes, the final pass should also
include at least one real entrypoint smoke check for each documented mode that
shares the touched dispatch or cleanup logic.
For wrapper or shell-dispatch changes, the final pass should also include at
least one malformed or injection-shaped input on the real user-facing
entrypoint and prove it is rejected without side effects.
For API, file-serving, listing, or validation changes, the final pass should
also include at least one negative-path proof and at least one alternate valid
topology proof when the feature supports more than one shape of input or
content layout.
For host-selection, parser, alerting, or localization changes, the final pass
should also include the narrow regression tests for:

- default vs explicitly selected resource behavior,
- missing-selected-resource behavior when another similar resource exists,
- already-normalized or already-qualified input values,
- user-facing alert or status text on every changed surface.

For workspace or HA service-lifecycle changes, the final pass should normally
include the real enable/bootstrap step, the canonical deploy path, the fastest
relevant smoke lane, and at least one promotion or failover-style scenario when
the diff changes standby behavior, teardown behavior, or cross-node wiring.

### 7. Emit the release handoff

If the branch is plausibly headed for tagging or public release, end the gate
with a handoff block that `create-github-release` can consume. Include:

- the reviewed `HEAD` commit SHA,
- gate status,
- publication or privacy status,
- commands actually run,
- commands still recommended,
- whether the result is acceptable for tagging,
- any environment-targeting caveats discovered during validation.

`create-github-release` should be treated as downstream of this handoff, not as
an independent substitute for the gate.

## Decision rules

- `Ready`: no known blockers remain, critical validation was run or clearly satisfied, and the final review pass was done on the final diff.
- `Ready with known gaps`: no direct blocker is left, but some recommended validation was not run or some low-confidence risk remains.
- `Blocked`: correctness, regression, security, or deployment risk is still unresolved, or the final post-fix pass has not been completed.

If the repository lacks tests for an affected surface, do not hide that fact. Treat it as a validation gap and downgrade confidence.

## Output requirements

Return:

- gate status: `Ready`, `Ready with known gaps`, or `Blocked`,
- base branch and diff scope used,
- reviewed `HEAD` commit SHA,
- which review skills were run,
- blockers,
- recommended follow-up work,
- commands actually run,
- commands still recommended,
- publication/privacy scan status,
- reusable pre-PR skill updates made, or a no-op rationale when the corpus
  already covered the learned class,
- release handoff summary when the branch may be published,
- whether the branch is ready for GitHub Codex review.

If the branch is not ready, say exactly what remains before a PR review pass is worth spending.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
