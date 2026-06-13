---
name: pre-pr-review-tests-validation
description: Reviews regression-test coverage, validation strategy, fixtures, CI signals, and local quality-gate completeness before PR. Use when a pre-PR review area includes tests, harnesses, smoke checks, fixtures, generated test inputs, validation scripts, or when another reviewer needs a focused test-gap pass.
---

# Pre-PR Review Tests Validation

Use this as a report-only reviewer profile for test and validation slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Tests that prove the changed behavior, including negative paths, disabled
  defaults, read-only behavior, and failure handling.
- Fixture and generated-data drift across schemas, templates, examples, and
  runtime config.
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
- Host-probe and installer regressions should include sibling negative paths
  for optional tool present without matching hardware, multiple candidate
  devices or interfaces, root-without-sudo execution, and interactive prompts
  when stdout is captured for later parsing.
- Narrow validation commands for each finding plus the repo's standard gate when
  available.
- Live-test safety: use explicit opt-in inputs and avoid touching production or
  costly resources unless the user authorized it.
- Flaky, order-dependent, environment-dependent, or stale-harness risks.
- When tests inject fake command runners or tool locators, require a separate
  availability model so fixtures can prove optional tools are absent without
  inflating supported capability detection.

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
