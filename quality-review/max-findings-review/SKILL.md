---
name: max-findings-review
description: Code review skill for PRs/diffs that maximizes real findings (bugs, regressions, risks) across any tech stack; minimal style feedback.
---

# Max Findings Review

## When to use

Use for PR/code reviews where the user wants maximum coverage of real issues (bugs, regressions, unsafe behavior, broken configs, operational risks) regardless of stack.

## Specialist lenses

Use specialized reviewer profiles as focus lenses when the diff clearly touches
one of their domains. Do not delegate or edit from this skill unless another
orchestrator explicitly asks for that workflow.

- `$pre-pr-review-frontend` for UI, templates, CSS, browser behavior, and client
  state.
- `$pre-pr-review-backend-services` for APIs, workers, persistence, validation,
  and integrations.
- `$pre-pr-review-infra-runtime` for deploy, Docker, Compose, Workspace,
  Jenkins, services, and package-manager behavior.
- `$pre-pr-review-security-boundaries` for auth, secrets, privileged helpers,
  telemetry, prompts, and side-effect boundaries.
- `$pre-pr-review-tests-validation` for fixtures, smoke checks, validation
  scripts, CI signals, and coverage gaps.
- `$pre-pr-review-docs-release` for README, changelog, release notes, examples,
  operator docs, and versioning.
- `$pre-pr-review-config-data-flow` for config, defaults, schemas, generated
  artifacts, identifiers, and URL/path handling.
- `$pre-pr-review-cli-tooling` for shell, Makefile, installers, wrappers, and
  argument pass-through.
- `$pre-pr-review-ci-actions` for GitHub Actions, check logs, matrices, caches,
  artifacts, and workflow permissions.
- `$pre-pr-review-agent-workflows` for `AGENTS.md`, `SKILL.md`, prompt
  templates, learning hooks, and Codex automation guidance.

## Review protocol

1) Load AGENTS.md if present in repo root; obey it.
2) Review full diff and relevant files. If specs are referenced, read them.
3) Maximize real findings: bugs, regressions, unsafe behavior, config mistakes, operational risks. Avoid pure style feedback.
4) Assume production realities: missing env vars, empty lists, services down, unmounted paths with existing directories, stale configs, etc.
5) Scrutinize shell/command invocations: enforce proper quoting (whitespace, globbing), prefer args lists where possible; flag unquoted paths/env values.
6) Verify result-shape and template-language assumptions: module/tool outputs may omit fields (`rc`, `stderr`, `path`) on success, companion files may be optional, and embedded template/filter expressions must use functions the target runtime actually supports; flag logic that fabricates failures or truthy values when a field or file is missing.
7) Inspect any failure-suppression patterns (e.g., `failed_when: false`, `ignore_errors`, `try/except: pass`, best-effort probes) to ensure errors are captured before suppression and downstream logic keys off the real failure signal (rc/stdout/stderr/exception), not the suppressed state. Required preconditions, pauses, stops, locks, and cleanup guards must fail closed before dependent writes or reconciliations continue.
8) For declarative automation, command/shell tasks and runtime refresh probes must report changes from actual managed-state drift, not from merely running. Flag unconditional `changed_when: true` on idempotent probes, collectors, validators, and status refreshes.
9) Check normalization/sanitization workflows for collisions, uniqueness, and
   representation drift after transformation (e.g., slugging, case-folding,
   Unicode normalization, percent-encoding, regex replaces). Flag duplicate
   keys/paths/names, planned operations that target the same future path before
   the destination exists, and URL/path encoders that change the stored
   filesystem or external identifier form instead of only escaping it.
10) Check consistency between validation/expectation logic and render/config logic (same prefix/variables/derivations used in both places).
11) Scrutinize matching logic where exact identity matters: avoid substring/regex matches that can produce false positives; prefer token/line/field-aware exact matching.
12) Preserve sentinel and unset-state semantics across read, render, form/API write, config serialization, and later reload. Flag cases where "all", "default", "auto", "inherit", placeholders, empty, null, or omitted values get materialized into a stale concrete list/value on ordinary save, and cases where sentinel cleanup runs after fallback/default selection so fallback-bearing fields collapse to empty.
13) Check mode contracts and defaults for side effects. Dry-run, preview, validate, no-op, disabled, or read-only flows must not perform external writes, privileged operations, network calls, device mutations, or background jobs unless explicitly documented. Defaults for outbound notifications, external delivery, or third-party writes must be inert placeholders or require explicit configuration.
14) Review background/asynchronous work against shared resource ownership and terminal states. Look for duplicate workers, missing single-flight guards, stale status messages, wait loops that ignore recorded errors, and paths that start expensive live work when a snapshot/cache/artifact should be reused.
15) Check privilege lifecycle, runtime artifacts, and feature gating. Privileged policies, credentials, capabilities, service units, handlers, permissions, install-time grants, containers/proxies, generated configs, and scheduled jobs should be created only when the feature that needs them is enabled, honor configured install/render destinations including overridden paths and parent directories, and be removed, invalidated, or skipped when disabled. For include/import mechanisms, verify privacy and lifecycle keywords apply to inner tasks, not only the wrapper statement.
16) Check stable identity versus display labels. Any map, join, merge, cache, route, filename, chart series, or generated artifact that must distinguish resources should use stable unique IDs, not names or other user-facing labels. Be especially suspicious of identity inferred from partial metadata, date-only matches, or sparse caches; if more than one real object can share that key, fallback behavior must avoid silently merging or dropping items.
17) When a newer canonical data source, richer metadata, probe, or sidecar data replaces a fallback or legacy source, verify every reader, writer, summary, and reporting path migrates or falls back before querying it. Missing or sentinel values should preserve fallback data, and schema/resource-ready caches must recheck the backing file after deletion, replacement, or partial initialization.
18) Check time and cadence logic for clock skew, future timestamps, stale markers, zero/default intervals, and catch-up behavior after time corrections or delayed jobs.
19) Check boundary limits across layers. Validators, schemas, examples, UI limits, helper scripts, installers, and runtime code should share the same minimums, maximums, enum values, and rejected ranges.
20) Check negative-path semantics. Expected misses, denied access, stale references, absent records, or unsupported lookups should fail with the intended user-visible status or error class, not a generic internal failure.
21) Scrutinize executable parsing boundaries. If user-controlled input flows through shell wrappers, workspace commands, config DSLs, or CLI passthrough logic, verify the generated or documented command shape matches the parser contract and tokenizes data without `eval`-style execution, command substitution, or separator interpretation.
22) Check supported topology assumptions. Validators, probes, importers, scanners, and serving code should handle each documented or plausible valid shape of input or content layout instead of assuming only one nested or happy-path topology. Include benign-but-hostile filesystem states such as unreadable entries, restricted `exists()` or `is_dir()` probes, empty folders, non-project folders, and partial metadata caches that still coexist with valid content.
23) For Python repos, explicitly inspect drift across `pyproject.toml`, example config files, install/bootstrap scripts, package data, locale catalogs, optional extras, CLI entrypoints, version metadata, release notes, and tests. New config keys, asset files, user-facing strings, optional imports, persistence migrations, canonical-store changes, or release/version bumps must be reflected everywhere they are required, especially when changelog release sections, package metadata, runtime `__version__`, and `--version` expectations all need to stay aligned.
24) For Python repos with strict tooling (`pytest`, `ruff`, `mypy`, `uv`, `make check`), review the diff against the real project gate rather than only against isolated files. Check whether the change updated the commands, assumptions, or generated artifacts that the gate exercises.
25) Prioritize “intended behavior vs actual behavior” gaps and fragile defaults.
26) If an issue is plausible, report it with rationale and scenario.

## Output format

- Findings first, ordered by severity (P1–P3).
- Each finding: file path, exact code lines, impact, trigger scenario, concrete fix suggestion.
- If no findings, say “No issues found” and list what you checked.

## Default review prompt to include

Use the following prompt verbatim when reviewing:

You are an expert reviewer. Goal: maximize real findings (bugs, regressions, unsafe behavior, broken configs, operational risks), not style.

Inputs available:

- Full PR diff
- Relevant repo files
- AGENTS.md rules (if present)
- Specs referenced by the PR

Review instructions:

1) Enumerate risks and edge cases.
2) Assume production realities: missing env vars, empty lists, services down, unmounted paths with existing directories, stale configs.
3) Validate defaults, list indexing, conditionals, and shell/command argument safety (quote paths/values; avoid whitespace or globbing issues).
4) Verify result shapes and template expressions for tools/modules: optional companion files may be absent, output fields may be missing, and filters/methods must exist in the target template runtime; prefer explicit signals over defaults that turn missing data into false failures/successes.
5) Check that validation/probe/guard code does not mask failures before recording them (e.g., `failed_when: false`, `ignore_errors`, `try/except: pass`, best-effort checks); ensure flags/maps are built from real failure signals, not masked values, and required pauses/stops/locks/cleanup guards fail closed before dependent mutations continue.
6) For declarative automation, command/shell probes must use truthful change reporting: idempotent collectors, validators, status refreshes, and no-op probes should not use unconditional changed results.
7) Check normalization/sanitization collisions and representation drift
   (slugged names, case-folding, Unicode normalization, percent-encoding, regex
   replaces), including duplicate planned output paths before files are written
   and URL/path encoders that change stored filesystem or external identifier
   forms instead of only escaping them.
8) Check for expectation/render mismatches: same inputs should drive validation and emitted config/artifacts (prefixes, naming conventions, variable overrides).
9) Prefer exact matching where presence/absence is asserted; avoid substring/regex matches that can hide missing entries.
10) Preserve sentinel and unset-state semantics. Check whether ordinary saves turn "all", "default", "auto", empty, null, or omitted values into stale concrete values.
11) Enforce mode contracts and safe defaults. Dry-run, preview, validate, no-op, disabled, or read-only flows must not perform external side effects unless explicitly documented. Outbound notification or external-delivery defaults must be inert until explicitly configured.
12) Check async/background work touching shared resources for single-flight guards, truthful status messages, wait loops that exit on recorded errors as well as success/timeouts, and unnecessary live work when cached/snapshot data should be reused.
13) Check feature-gated privileges and runtime artifacts. Sudoers/capabilities/credentials/service grants, handlers, unit lifecycle hooks, containers/proxies, generated configs, and scheduled jobs should exist only when the corresponding feature is enabled, honor configured install/render destinations including overridden paths and parent directories, and be skipped, removed, or invalidated when disabled. Include/import privacy keywords must apply to nested tasks when secrets flow through them.
14) Use stable unique IDs for joins, maps, series, caches, filenames, and routes where labels can collide.
15) When preferring a new canonical store, enriched metadata, or probe output over a fallback, require every read/write/reporting path to migrate or fall back before querying it, and require ready-state caches to recheck the backing file after deletion/replacement; otherwise preserve the fallback.
16) Check time/cadence logic for future timestamps, clock skew, stale markers, zero/default intervals, and delayed catch-up.
17) Keep limits aligned across validators, schemas, UI, docs, helper scripts, installers, and runtime code.
18) Check negative-path semantics: not-found, unauthorized, invalid-input, and stale-reference cases should surface the right user-visible status or error class rather than an internal generic failure.
19) Check executable parsing boundaries: wrappers, shell helpers, and config-driven command paths must emit the documented option form and treat user input as data, not something to execute via `eval`, command substitution, or separator parsing.
20) Check deploy-input and sync-manifest parity: if runtime behavior now depends on ignored/private override files, generated config, or sidecar inputs, stale checks and sync/deploy guards must include those real inputs, not only tracked examples.
21) Check host-tool portability for shell/workspace gates: commands that run on macOS/BSD developer hosts must not require GNU-only flags unless the dependency is explicitly checked or a portable fallback exists.
22) Check supported topology assumptions: if the feature may accept flat-root and nested layouts, or more than one valid shape of content/input, verify the code and tests cover those shapes.
23) For Python repos, check cross-file drift: config dataclasses/schema, load/write/validate logic, locale catalogs, example TOML/YAML files, installer/bootstrap scripts, docs, version metadata, and tests must stay aligned when new settings, visible strings, persistence migrations, canonical stores, behaviors, or release/version bumps are added.
24) For Python packaging changes, check `pyproject.toml` metadata, optional dependencies, packaged assets, console scripts, and `python -m` entrypoints. Flag changes that work in tests but would fail after `make install`, editable install, or packaged execution.
25) For server-rendered Python web apps, check route/action/render splits, redirect behavior, background work triggered by POST handlers, and whether tests cover the real entrypoint instead of only helper functions.
26) Find intended-vs-actual behavior gaps.
27) If an issue is plausible, report it even if not 100% sure.

Output format:

- Findings first (P1–P3).
- Each finding: file path, line(s), impact, scenario, concrete fix.
- If none, say “No issues found” and list what you checked.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
