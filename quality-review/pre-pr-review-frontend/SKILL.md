---
name: pre-pr-review-frontend
description: Reviews frontend branch diffs for UI, browser behavior, state, accessibility, and client-side regressions before PR. Use when a pre-PR review area includes web app UI, client JavaScript or TypeScript, CSS, templates, frontend build wiring, browser tests, or user-facing interactions.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Frontend

Use this as a report-only reviewer profile for frontend slices of a broader
pre-PR remediation. Do not edit files.

## Review Focus

- User-facing behavior regressions across the changed flows, not just static
  component correctness.
- State, loading, empty, error, retry, disabled, and permission-denied states.
- Data rendering safety: avoid unsafe HTML injection, preserve escaping, and
  confirm identifiers or URLs are not normalized unintentionally.
- Responsive layout, text fitting, keyboard access, focus behavior, and basic
  accessibility semantics.
- Client/server contract drift in API payloads, discovery data, validation
  messages, cache keys, and generated assets.
- When managed charts or other user-adjustable presentation objects are rebuilt,
  inventory and preserve the complete public state surface: data ranges,
  geometry, formatting/options, null handling, series/category orientation, and
  builder-level properties outside the ordinary options map. If options are
  only key-addressable, audit the full provider option catalog instead of
  trusting a partial whitelist; include user-authored subtitles, annotations,
  and style objects. Test a customized object through refresh, failure rollback,
  and crash recovery.
- Frontend test coverage for the changed behavior, including negative paths and
  race-prone interactions.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Treat backend, infrastructure, security, and documentation impacts as overlap
  risks unless they are inside the assigned frontend scope.
- Prefer concrete reproduction paths over broad style commentary.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command or browser check,
- possible overlap with another reviewer area.
