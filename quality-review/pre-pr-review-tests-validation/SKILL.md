---
name: pre-pr-review-tests-validation
description: Reviews regression-test coverage, validation strategy, fixtures, CI signals, and local quality-gate completeness before PR. Use when a pre-PR review area includes tests, harnesses, smoke checks, fixtures, generated test inputs, validation scripts, or when another reviewer needs a focused test-gap pass.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Tests Validation

Use this as a report-only reviewer profile for test and validation slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Tests that prove the changed behavior, including negative paths, disabled
  defaults, read-only behavior, and failure handling. For dry-run or check-mode
  regressions, assert that the prohibited side-effect boundary reports skipped
  or was not called, not only that a preceding task predicted change. For
  pipelines that write durable outputs before optional external work, force a
  downstream timeout or transport failure and assert the earlier outputs remain
  usable.
- Retry-loop regressions should exercise every real entrypoint with a shared
  invocation deadline and a sequence such as valid-but-rejected, malformed or
  empty, then valid; assert no extra call occurs after the deadline and that
  the last schema-valid snapshot remains in repair context.
- For generated or normalized output, test the shared acceptance predicate
  across primary and backup attempts, fallback, cache reuse, finalization,
  persistence, and each real downstream consumer; include output that exists
  but is unusable (such as whitespace) and assert it is rejected and removed
  before another stage can consume it.
- Classification regressions must carry accepted boundary inputs through the
  final user-visible outcome, not stop at the admission helper; include a
  legacy downstream guard that would reject the same lexical or structural
  pattern if the contracts drift.
- When a successful validator produces authorization, eligibility, or other
  control metadata used by a later mutation, test the complete sequence of
  validation-stage wrappers and final consumer. A wrapper must preserve that
  metadata or explicitly transfer it, not replace success with only a generic
  `{valid: true, stage}` result.
- For aggregate inference, vary predicate order with irrelevant records that
  have unusable values and broken identity or provenance. Assert those records
  are discarded before trust checks and cannot manufacture a conflict.
- For source-to-artifact transformations, fixtures must cover an equivalent
  pattern in an unrelated scope and structurally similar but unsafe input (such
  as conditional cleanup), then assert the render preserves the former and
  rejects the latter without writing an artifact. For an identical rendered
  payload with drifted file metadata, assert that required permissions still
  reconcile. Perturb callback registration or replacement, definition shadowing,
  signatures, and evaluation semantics such as generators or exception causes.
- Rendered table, form, and terminal-UI tests should cover the minimum supported
  viewport, every adaptive layout breakpoint, and long or high-cardinality
  values; assert that distinct identifiers, actionable controls, and focus stay
  visible rather than merely asserting that rendering completes. Where
  readability is required, check complete label or row containment in the
  unobscured viewport; existence and hittability alone do not prove visibility.
- For rotation or pixel-based UI evidence, verify captured target, dimensions,
  orientation and coordinate mapping. Compare anomalous app crops with a
  full-display capture after geometry settles; normalize raster orientation
  before sampling. Retain contradictory images and distinguish functional
  assertions from visual acceptance before changing product layout.
- Recovery-flow tests must assert the predicate that lets the failing step
  yield control to recovery, such as `until` or `failed_when`, not only the
  accepted status list and presence of later recovery tasks. For first-time
  recovery sets, cover every artifact-publication stage plus retry, and
  distinguish clean sources from retained, partial, and already-managed states.
- Installer recovery fixtures must cover each durable phase, including before
  and after a temporary credential is persisted. Assert incomplete phases
  reject migrations, persisted credentials resume without reprovisioning, and
  resumed runs apply current configuration rather than stale saved settings.
- For structural migrations, test discovery and recovery at the supported scan
  boundary before and after each row or column shift. Reject an out-of-bound
  schema before mutation, or prove the retry path can rediscover it.
- Fixture and generated-data drift across schemas, templates, examples, and
  runtime config. Trace every fixture and static regression to the current
  authoritative implementation entrypoint and asserted task or symbol; renames
  and validator extraction must not leave a stale fixture testing dead logic.
  For vendored or runtime-specific dependencies, load the exact deployed artifact
  under its production export/global environment. A Node package or test
  substitute does not prove the deployed bytes initialize correctly.
- CLI and hardware validation fixtures should mirror real output topology,
  indentation, multi-device blocks, and version-specific quirks; include
  positive and negative samples that prove parsers do not match the wrong
  device block or only the happy-path line.
- Rendered service-unit tests should assert escaped runtime syntax, including
  systemd `%` specifiers and literal shell `$`, and should exercise both the
  generated artifact and the template/source contract when boot ordering or
  oneshot readiness depends on shell snippets.
- Service lifecycle tests should distinguish an unavailable service manager,
  a loaded unit intentionally disabled for the active runtime, and the
  enabled/active steady state. Inspect real load, enablement, and activity facts
  before falling back to marker-file or shim assertions.
- Environment semantics that can invalidate tests, including container
  filesystems where `/tmp` is tmpfs and does not support ACL/xattrs, and
  bind-mounted temp directories whose host owner or `0700` mode blocks the
  container user from writing rendered artifacts. Prefer a compatible path such
  as `/var/tmp` or a container-owned temp path, and assert mount characteristics
  and permissions when diagnosing filesystem failures.
- Tests that require specific runtime configuration should set it in the test
  entrypoint (for example `@php -d phar.readonly=0 vendor/bin/phpunit`) instead
  of inheriting machine-global settings.
- CI and local gates that actually exercise the changed path rather than only
  syntax or happy-path checks.
- For declarative check mode, run both fresh and converged topologies with
  hostile pre-existing state. Assert predicted parents or artifacts are not
  consumed before they exist, privileged mutations do not launch, and each
  rejection is attributed to the intended validation task rather than any
  incidental earlier failure.
- Host-probe and installer regressions should include sibling negative paths
  for optional tool present without matching hardware, multiple candidate
  devices or interfaces, root-without-sudo execution, interactive prompts when
  stdout is captured for later parsing, unknown targets, partial uninstall, and
  dry-run/apply parity for shared payload cleanup. For installers that wrap
  third-party CLIs, cover isolated staging homes, copy-versus-link modes, failed
  copy preserving existing payloads, non-mutating dry-runs, parser output
  variants from the real CLI, malformed metadata, filtered-out invalid names,
  names containing spaces, and each supported shallow discovery topology.
- Narrow validation commands for each finding plus the repo's standard gate when
  available.
- Execution evidence must identify the required cases and parameter combinations,
  terminal assertion results, failures, and skips. Keep framework cases, process
  iterations, and produced outputs as separate counts; a successful command or
  helper return does not establish coverage or assertion success.
- Preserve the first relevant failed result and fixtures before cleanup. Keep
  failed or timed-out runs alongside retries; isolated passes establish only
  their own coverage, not a passing original suite or a clean environment.
- Prefer bounded compatible batches when setup is costly, with per-case results
  and required platform/configuration coverage intact. Verify successful builds
  and relevant input/environment identity before artifact reuse; isolate
  incompatible state while retaining sequences needed to reproduce defects.
- Live-test safety: use explicit opt-in inputs and avoid touching production or
  costly resources unless the user authorized it.
- Database-backed integration suites must remain import-safe with no configured
  database. Defer validation until explicit opt-in, skip selected integration
  items during collection, and assert invariants rather than private fixture
  identifiers.
- Flaky, order-dependent, environment-dependent, or stale-harness risks.
- When tests inject fake command runners or tool locators, require a separate
  availability model so fixtures can prove optional tools are absent without
  inflating supported capability detection.
- Fixture isolation: when a test sources generated command blocks after
  installing stubs, verify those blocks cannot reload dependencies and replace
  the stubs. Load dependencies before installing fakes, or omit the duplicate
  source line, and use an intentionally unavailable runtime value so a live
  resource cannot make the fixture pass accidentally.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag missing implementation changes as overlap risks instead of proposing
  broad rewrites.
- Prefer test gaps that would have caught a concrete bug in the diff.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command,
- possible overlap with another reviewer area.
