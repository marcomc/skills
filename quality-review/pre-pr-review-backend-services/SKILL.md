---
name: pre-pr-review-backend-services
description: Reviews backend service, API, worker, persistence, and domain logic diffs before PR. Use when a pre-PR review area includes server-side application code, HTTP APIs, background jobs, database or file persistence, validation logic, queues, or service integrations.
---

# Pre-PR Review Backend Services

Use this as a report-only reviewer profile for backend or service slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Behavior contracts for APIs, CLIs, workers, scheduled jobs, and service
  integration points.
- Error handling, retries, idempotence, partial failure, timeout, and cleanup
  paths.
- Per-resource retry suppression or backoff must not mask aggregate service
  health checks or fleet-level recovery triggers; require tests for both
  single-resource degradation and all-resources-unreachable states (including
  mixed “timeout” and “not found” style failures across the entire enabled
  fleet).
- Service probes, recovery paths, and readiness checks that must prove the same
  protocol handshake, authentication, authorization, and client identity used
  by the real workflow, not only transport reachability.
- Input validation, authorization boundaries, tenant or environment scoping,
  and safe handling of secrets or private values.
- Persistence compatibility: migrations, serialized formats, file paths,
  generated outputs, and backward compatibility with existing data.
- Config loading and default propagation into runtime behavior.
- Regression coverage for changed contracts, especially negative paths and
  cross-module behavior.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag frontend, infrastructure, release, and operator-doc impacts as overlap
  risks unless they are directly inside the assigned backend scope.
- Prefer findings tied to externally observable behavior or durable contracts.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command,
- possible overlap with another reviewer area.
