---
name: pre-pr-review-security-boundaries
description: Reviews auth, authorization, secrets, trust boundaries, permission prompts, external delivery, and side-effect boundaries before PR. Use when a pre-PR review area includes privileged actions, credentials, tokens, web actions, telemetry, local device access, outbound notifications, or read-only paths that call capable helpers.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Security Boundaries

Use this as a report-only reviewer profile for security-sensitive slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Authentication and authorization checks for privileged or state-changing
  actions.
- Security-relevant remote collections must match the complete expected shape;
  do not accept one safe member while an additional public, privileged, or
  mismatched member remains. Test mixed safe-and-unsafe collections.
- Treat external responses as untrusted at both schema and identity boundaries:
  validate each root, nested collection, and record before access, then require
  the returned stable identity to match the requested resource before using its
  state. Cover missing, null, scalar, wrong-identity, and malformed nested forms.
- Before mutation, normalize, compare, and authenticate every configured read,
  verification, and mutation endpoint. Prove mismatched or unauthenticated
  endpoints stop before launch without exposing credentials or probe output.
- Revalidate remote ownership and identity immediately before every mutation or
  acknowledgement, not only during initial preflight. Journal a unique creation
  intent before remote creation and reconcile it after ambiguous results so a
  retry cannot duplicate the resource.
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
- Operator-facing structured text, email, and notification fields must
  normalize record delimiters and control characters so untrusted filenames or
  content cannot forge additional labels or records. Add a multiline-input
  regression for every plain-text report boundary.
- Formula-capable spreadsheet, CSV, and office-document sinks must write
  untrusted strings as literal data rather than formulas. Verify both standard
  fields and dynamic header/value maps, reject writes to formula-owned columns,
  and add a regression beginning with `=`, `+`, `-`, or `@`. Type conversion must
  follow the field contract rather than cell formatting; test leading-zero identifiers
  in numerically formatted supplementary columns through write and read-back.
- Multi-service mutations must persist a provenance-bearing journal before the
  first side effect, record durable outcomes and notification outbox entries
  before clearing it, and recover journals before sending success reports.
  Test hard stops between every remote mutation and marker write; ambiguous
  compensation must stop without deleting unprovenanced data.
- Read-only paths that accidentally call authorization, prompt-capable, or
  state-changing helper modes.
- Privileged shell snippets rendered from config must quote or strictly
  validate every interpolated path, selector, and argument before root or boot
  execution; absolute-path checks alone do not stop command substitution,
  backticks, globbing, option injection, or shell metacharacters.
- Authenticated validation probes that create refresh tokens, sessions, API
  keys, or equivalent credentials must release or revoke them through the
  service's documented cleanup flow. Verify the endpoint, required action
  parameters, and failure handling, and require a regression guard when the
  probe is intended to be repeatable.
- Installer-owned credential-capable CLIs must use installer-owned private
  state for every invocation, enforce restrictive directory and file modes,
  and remove or revoke only credentials whose ownership the installer tracked.
  Test with an isolated home directory and fail on writes outside staged state.
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
