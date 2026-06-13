---
name: pre-pr-review-config-data-flow
description: Reviews configuration, defaults, examples, schemas, generated files, path or URL encoding, and data-contract propagation before PR. Use when a pre-PR review area adds or changes config keys, templates, override files, schemas, manifests, generated artifacts, identifiers, serialization, filenames, or URL/path handling.
---

# Pre-PR Review Config Data Flow

Use this as a report-only reviewer profile for configuration and data-contract
slices of a broader pre-PR remediation. Do not edit files.

## Review Focus

- Every config key across load, write, validate, examples, docs, installers,
  generated files, and runtime use.
- Config file parsers must treat values as data rather than shell. If a format
  documents variable expansion, require explicit expansion code and a negative
  regression proving command substitution or other shell syntax remains inert.
  Also test variable-name boundaries so `$HOME_BACKUP`, `$USER_NAME`, or similar
  longer literal names are not partially expanded.
- For command-managed registries or generated config maps, compare the registry
  view to the effective runtime configuration (including later/override config
  files) and ensure commands reject operations they cannot make effective; add
  tests proving commands do not claim success when a different config source
  shadows the same key.
- Inventory-aware validators must inspect every inventory and group-var
  topology used by the changed runtime path, including Jenkins-specific or
  generated inventories, not only the default local environment.
- If the architecture resolves resources through names, selectors, or logical
  keys, validators should reject stale direct-ID override keys instead of
  accepting them as compatibility paths.
- Cloud or provider identifiers should not be pre-cast with lossy filters that
  convert invalid values into defaults before the provider client or module
  argument validation can reject them.
- Safe defaults versus private or local-only values, including ignored override
  files and tracked placeholders.
- Schema, fixture, manifest, discovery payload, and generated-artifact drift.
  For generated artifacts, verify every supported output variant and marker
  path is included in discovery, reporting, and stale-check paths, including
  specialized filenames, nested instruction locations, and configured depth
  limits.
- Placeholder recovery for generated-artifact checks must round-trip
  user-supplied or template-specific values without recovering derived defaults
  such as project names, paths, dates, or other values that should change when
  the source context changes.
- URL, path, filename, escaping, and identifier changes that must preserve the
  stored representation and externally meaningful normalization. For generated
  public URLs, verify scheme, host, port, and path against the endpoint actually
  exposed in each environment, not only the canonical hostname.
- JSON contracts where fields may be scalar-or-list (for example policy fields
  that accept either `"Action": "x"` or `"Action": ["x"]`): normalize shapes
  before membership checks; preserve parsed empty arrays as empty, not as raw
  string targets; and add tests/fixtures that cover both forms plus a negative
  path.
- Case-insensitive collision checks for user-provided domains, hostnames, and
  derived local filenames across all output paths (especially when generating
  TLS materials or other filesystem artifacts).
- Disabled or opt-in features whose templates, defaults, helpers, and discovery
  surfaces must remain inert.
- Index-only, list-only, preview, and other read-side generators that reuse
  sync code must not prune, rewrite, or delete published artifacts unless that
  destructive behavior is explicitly requested and covered by regressions.
- Tests proving propagation, absence of stale defaults, and backward
  compatibility for existing data.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag application, infra, security, and documentation impacts as overlap risks
  when a config or data contract crosses ownership boundaries.
- Prefer end-to-end propagation gaps over local naming preferences.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command,
- possible overlap with another reviewer area.
