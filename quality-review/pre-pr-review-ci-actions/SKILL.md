---
name: pre-pr-review-ci-actions
description: Reviews GitHub Actions, CI checks, workflow permissions, caches, artifacts, matrices, and log-derived failures before PR. Use when a pre-PR review area includes `.github/workflows`, GitHub Actions jobs, reusable workflows, check failures, CI scripts, build matrices, artifacts, caches, or workflow token permissions.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review CI Actions

Use this as a report-only reviewer profile for GitHub Actions and CI slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Workflow trigger, branch, path, matrix, and dependency ordering changes.
- Job permissions, secret exposure, checkout depth, artifact retention, cache
  keys, and upload/download paths.
- For Ansible in CI, ensure roles and collections are installed explicitly
  (`ansible-galaxy role install` vs `ansible-galaxy collection install`) and
  collection search paths are set (`ANSIBLE_COLLECTIONS_PATHS` / `collections_paths`)
  before running `ansible-playbook` or linters; FQCN resolution failures can be a
  missing collection cache, not a bad `requirements*.yml`.
- Commands that differ between CI and local wrapper paths.
- Missing setup steps for runtimes, package managers, generated assets, and
  services used by tests.
- Failure-log evidence that points to the real source line or command rather
  than a downstream symptom.
- Checks that can falsely pass because the workflow skips the changed surface.

## Assignment Rules

- Review only the assigned pathspecs, commits, logs, or diff range.
- Treat application, infra, security, CLI, and documentation impacts as overlap
  risks unless they are directly inside the assigned CI scope.
- Prefer findings that would block merge confidence or hide broken checks.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- workflow or log reference and changed behavior,
- evidence from the diff, current file, or check log,
- proposed remediation,
- narrow validation command or GitHub check to rerun,
- possible overlap with another reviewer area.
