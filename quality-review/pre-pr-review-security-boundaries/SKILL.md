---
name: pre-pr-review-security-boundaries
description: Reviews auth, authorization, secrets, trust boundaries, permission prompts, external delivery, and side-effect boundaries before PR. Use when a pre-PR review area includes privileged actions, credentials, tokens, web actions, telemetry, local device access, outbound notifications, or read-only paths that call capable helpers.
---

# Pre-PR Review Security Boundaries

Use this as a report-only reviewer profile for security-sensitive slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Authentication and authorization checks for privileged or state-changing
  actions.
- CSRF, origin, local-network, webhook, and inter-service trust boundaries.
- Secret handling in templates, logs, examples, generated files, ignored files,
  process arguments, shell history, and CI or deployment variables. Operator
  examples must not expand credentials into process arguments; prefer a secure
  prompt or restrictive ephemeral file, remove it on every exit path, and add
  negative proof for history, argv, log, and persistent-file exposure.
- Generated configs or files containing host identity, local network facts,
  credentials, tokens, or other operator-specific values should be written
  atomically with restrictive permissions. Include a mode check when installer
  or renderer defaults move private values into first-run files.
- Safe defaults for external delivery, telemetry, notifications, destructive
  operations, and user-specific data.
- Read-only paths that accidentally call authorization, prompt-capable, or
  state-changing helper modes.
- Authenticated validation probes that create refresh tokens, sessions, API
  keys, or equivalent credentials must release or revoke them through the
  service's documented cleanup flow. Verify the endpoint, required action
  parameters, and failure handling, and require a regression guard when the
  probe is intended to be repeatable.
- Generated authorization policy drift: when IAM, RBAC, security-group, or
  provider permission documents change, compare generated statements with
  validators, readiness helpers, the CI identity policy resources per
  environment, and live read/write paths. Validators should assert every newly
  required resource and action explicitly, not only fail later through provider
  calls.
- Regression tests proving default or read-only paths stay inert and do not
  request permissions, prompt users, or leak private data.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- If the risk crosses multiple areas, mark it as cross-cutting so the main
  orchestrator can own the remediation.
- Use authorization-first wording for owned hardware, firmware, telemetry, and
  interoperability work.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command or negative-path proof,
- possible overlap with another reviewer area.
