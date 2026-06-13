---
name: diff-regression-check-planner
description: Analyze a branch diff and produce the exact regression checks, smoke tests, and validation commands that should run before merge. Use when the user wants a diff-aware test plan focused on changed contracts, entrypoints, generated artifacts, migrations, config, and user-facing behavior; report the plan only unless the user explicitly asks to execute it.
---

# Diff Regression Check Planner

Use this skill to turn a diff into a concrete validation plan. The goal is to answer: what exactly must be re-tested because of these changes, in what order, and with what confidence.

## When to use

- Before opening a PR.
- After a large fix batch.
- When a diff touches user-facing behavior, interfaces, configuration, data flow, or generated artifacts.
- When you want a tighter local gate before asking for GitHub Codex review.

This skill is not a replacement for code review. It is the validation planner that should sit beside code review.

## Workflow

### 1. Scope the diff

- Resolve the base branch and review `merge-base(base, HEAD)..HEAD`.
- Summarize the changed files by area: product code, tests, config, migrations, build scripts, CI, generated assets, docs, and developer tooling.
- Note file moves, renames, and deletions because they often create missing-reference regressions.

### 2. Map the changed surfaces

For each changed file or cluster, identify the affected runtime surface:

- public API or HTTP contract,
- CLI or shell interface,
- UI behavior or state flow,
- background jobs or async workers,
- database schema or persistence,
- configuration and feature flags,
- build, packaging, or deployment behavior,
- generated artifacts or rendered configuration,
- logging, observability, or monitoring hooks.

Also attach the closest specialized reviewer profile to each surface so the
plan can be reused by review or remediation orchestrators:

- `$pre-pr-review-frontend`
- `$pre-pr-review-backend-services`
- `$pre-pr-review-infra-runtime`
- `$pre-pr-review-security-boundaries`
- `$pre-pr-review-tests-validation`
- `$pre-pr-review-docs-release`
- `$pre-pr-review-config-data-flow`
- `$pre-pr-review-cli-tooling`
- `$pre-pr-review-ci-actions`
- `$pre-pr-review-agent-workflows`

### 3. Derive regression risks from the diff

Look specifically for:

- changed function signatures or return shapes,
- renamed exports, files, routes, or commands,
- modified validation and parsing logic,
- wrapper, shell, or workspace argument parsing that may accidentally interpret
  user input instead of tokenizing it,
- generated or documented command strings that may not match the wrapper's
  accepted option shape,
- changed auth, permissions, caching, or retries,
- changed defaults, environment handling, or flags,
- private or ignored override files that now become deploy/runtime inputs and
  must be included in sync, stale-check, generated-artifact, or deploy guards,
- changed include/import, handler, or notification wiring where the callee may
  not inherit lifecycle, privacy, or reload behavior from the caller,
- sentinel/default state changes, such as empty or placeholder meaning
  all/default/auto/inherit/fallback,
- negative-path behavior where expected misses or invalid lookups may now return
  the wrong status or error class,
- optional companion files or marker files that may be absent even when the main
  condition is true,
- supported content or input topology assumptions, such as flat-root versus
  nested-folder layouts at configured boundary or depth limits,
- identity inference from partial metadata, sparse caches, date-only joins, or
  filename-derived fallbacks that may merge distinct items or drop legitimate
  outputs,
- URL/path encoding changes that should escape a persisted filename,
  identifier, or artifact name without changing its stored Unicode normalization
  or other representation form,
- derived output paths where two planned operations can collide before either
  destination exists,
- fallback-source replacement where a preferred metadata/probe source can carry
  sentinel or unusable values for fields the older source still provides,
- dry-run, preview, validate, disabled, no-op, or read-only paths that may now
  perform external side effects,
- declarative automation probes or collectors whose `changed` result may drift
  from actual managed-state changes,
- changes that affect generated code or rendered artifacts, especially
  discovery, stale-check, or report-only paths that must cover default and
  specialized outputs,
- release/version metadata changes that can drift across changelog sections,
  package metadata, runtime version constants, published CLI output, and tests,
- concurrency, ordering, or state-transition changes,
- Makefile targets with ordered install, uninstall, enable, disable, or
  teardown side effects, especially when the target uses prerequisites that may
  run concurrently under `make -j`,
- background workers or repeated triggers touching the same resource,
- async wait loops, callbacks, or polling paths where terminal errors may arrive
  before success or timeout,
- privilege grants, service policies, credentials, capabilities, scheduled-job
  artifacts, or root-helper installation paths, including overridden
  destination paths and parent directories,
- identity joins or maps that may rely on non-unique display names,
- time/cadence scheduling paths affected by clock skew, stale markers, or
  future timestamps,
- boundary limits duplicated across schemas, validators, UI, docs, helpers, or
  runtime code,
- deletions that may leave stale references,
- changes that require backward compatibility checks.

### 4. Produce a layered validation plan

For each meaningful risk, propose checks in this order:

1. The narrowest check that proves the changed path still works.
2. The closest integration or smoke check that exercises the real entrypoint.
3. The broader project checks that should still pass after the change.

Prefer exact repo commands when they can be discovered from scripts, docs, CI config, or existing workflows. If a command is inferred, label it as an inference.

### 5. Include non-obvious checks

Always consider whether the diff requires any of the following:

- regeneration or rerendering of derived artifacts,
- handler/notification resolution checks for role-local changes,
- migration apply and rollback checks,
- compatibility checks for old inputs or existing persisted data through both
  writer paths and read-only/reporting paths,
- negative-path tests for bad input, missing config, or denied access,
- missing optional marker/sidecar-file tests for summary, notification, or
  cleanup paths,
- normal and parallel dry runs for Makefile side-effect flows whose steps must
  stay ordered, such as `make -n target` and `make -n -j4 target`,
- explicit malformed-input or injection-shaped checks for wrapper and shell
  entrypoints,
- cross-platform or shell-quoting checks, including macOS/BSD compatibility for
  host-side shell tools and flags,
- cache invalidation or stale-state checks, including deleted/replaced
  persisted files when a ready-state cache can skip initialization,
- compatibility checks for old and new generated filenames, cache keys, or
  persisted artifact names during migration windows,
- paired encoded-output checks for composed and decomposed Unicode filenames,
  already-qualified identifiers, or other representation variants when the
  generated URL/path must keep serving the exact stored artifact,
- cleanup-path verification after failure or partial success.
- filesystem-probe resilience checks for `exists()`, `is_dir()`, directory
  iteration, stat-like calls, and per-entry skips when benign permission
  errors or unrelated folders should not fail the whole run,
- round-trip checks for empty/null/omitted/default/auto/all/inherit sentinel
  values, including fallback-bearing fields where placeholders should inherit
  rather than become empty concrete values, while derived defaults such as
  project names, paths, or dates still change when source context changes,
- no-side-effect checks for dry-run, preview, validate, disabled, no-op, and
  read-only modes,
- forced-error checks for async wait loops, proving recorded failures unblock the
  caller before the full timeout,
- idempotence checks for command/shell probes, collectors, and runtime refresh
  tasks so repeated runs do not report changes unless managed state changed,
- repeated-trigger checks for background jobs that mutate shared resources,
- user-visible status checks that prove messages match whether work actually
  started or skipped,
- disabled-feature install/deploy checks for privilege artifacts,
- duplicate-label checks where stable IDs should distinguish resources,
- duplicate-target checks for batch rename, copy, export, or generation plans,
- unusable-preferred-source checks where enriched metadata lacks a required
  date, ID, path, or status and should fall back to a known-good source,
- future timestamp and clock-skew checks for schedulers,
- just-inside and just-outside boundary checks where helpers impose limits.

For Python diffs, always consider whether the change also requires:

- `pyproject.toml` or optional-dependency validation,
- package-data or packaged-asset smoke checks,
- example-config round-trip or config-validation checks,
- installed CLI or `python -m` smoke checks,
- installer/bootstrap script validation when runtime paths, generated service or
  scheduler destinations, or extras changed,
- version-alignment checks when changelog release notes, `pyproject.toml`,
  runtime `__version__`, package metadata, or `--version` tests changed,
- mypy/ruff/pytest and the repo's top-level gate command,
- live-validation follow-up when `AGENTS.md` marks the touched surface as appliance-affecting.
- flat-root and nested-layout validation when a serving, import, or directory
  traversal feature supports more than one valid content shape.

### 6. Separate blocking from optional checks

- Mark checks as blocking when they protect correctness, compatibility, or deployment safety.
- Mark checks as recommended when they add confidence but are not essential for merge.
- Call out gaps when the repo lacks a test harness for an affected surface.

## Output requirements

Return:

- a short diff summary,
- the impacted surfaces,
- a prioritized regression checklist,
- exact commands where known,
- expected success signals,
- validation gaps and untestable risks.

Use findings only by default. Do not execute commands unless the user asks for it.

## Python-specific planning hints

When the repo is Python-first:

1. Prefer the repo's documented gate command, such as `make check`, as the broader regression step.
2. If config files or settings code changed, include:
   - config validation,
   - tests covering the new settings,
   - example-config verification,
   - installer/bootstrap checks when those files copy or rewrite config.
3. If `pyproject.toml`, imports, or assets changed, include:
   - editable-install or package smoke checks,
   - console-script entrypoint checks,
   - package-data validation for shipped assets.
4. If the diff touches Python web handlers or HTML renderers, include:
   - request/action tests,
   - redirect/result checks,
   - any renderer or screenshot path used by the real feature.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
