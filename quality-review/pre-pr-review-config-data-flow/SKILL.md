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
- When a new required field is added to persisted configuration, inventory
  previously serialized shapes before enforcing it. Keep new input strict, but
  provide an explicit compatibility or migration path before old scheduled or
  event-driven consumers load the field; test both uninterrupted legacy reads
  and the operation that persists the migrated value.
- When a changed shipped default was materialized in existing generated config,
  migrate only provenance-detectable generated values; never infer an explicit
  override solely from a matching former default. Test absent, known-generated,
  and explicit old-default values across repeated rewrites.
- Notification recipient and disable settings across routine, error, and
  fallback delivery paths; require end-to-end custom-recipient and no-send
  tests when replacing a native notifier.
- Identity and alias validators must use the exact normalization implemented by
  runtime lookup. Reject normalized canonical collisions, alias-to-alias
  collisions, canonical-shadowing aliases, empty normalized identities, and
  duplicate override tuples; test punctuation and diacritic variants.
- When one request carries schemas for multiple target types, preserve the
  target-to-schema relationship instead of flattening a union. Prompt or
  serialization contracts must select fields only from the resolved target,
  and runtime validation must enforce that same target-specific schema.
- Structured overrides crossing CLI, wrapper, or serializer boundaries must
  preserve native types. Do not assume `key=value` parsers coerce booleans,
  numbers, nulls, or collections; prefer structured JSON or YAML input and
  assert the effective type at the consuming runtime.
- For configurable timeouts, watchdogs, retries, or caps, trace the effective
  value through every runtime phase and call-site default. A documented global
  control should not be shadowed by hard-coded per-call defaults, and an outer
  watchdog should bound setup, work, cleanup, notification, and other companion
  phases unless the docs explicitly narrow its scope.
- When reconciling a durable scheduled resource whose provider metadata omits
  cadence, persist a canonical desired schedule and compare it during
  reconciliation. Baseline legacy resources without replacing them, preserve
  matching resources, replace only changed recorded schedules, and test fresh,
  legacy, unchanged, changed, and replacement-cleanup-failure paths.
- For templated numeric settings, especially Ansible role variables rendered
  into systemd units, commands, retries, or timeouts, require an explicit
  shape and range assertion before casting. Lossy filters such as `int` must
  not silently turn invalid input into `0` or another default.
- Config file parsers must treat values as data rather than shell. If a format
  documents variable expansion, require explicit expansion code and a negative
  regression proving command substitution or other shell syntax remains inert.
  Also test variable-name boundaries so `$HOME_BACKUP`, `$USER_NAME`, or similar
  longer literal names are not partially expanded.
- For command-managed registries or generated config maps, compare the registry
  view to the effective runtime configuration (including later/override config
  files) and ensure commands reject operations they cannot make effective; add
  tests proving commands do not claim success when a different config source
  shadows the same key. When metadata records multiple config sources, resolve
  the effective source by the declared precedence semantics, not insertion order
  or string-sorted numeric keys.
- For global commands that can run from arbitrary working directories, verify
  required defaults come from an always-loaded config source rather than only
  the active project file. Add a regression from inside a minimal project so
  cwd-dependent config precedence cannot hide global defaults.
- Inventory-aware validators must inspect every inventory and group-var
  topology used by the changed runtime path, including Jenkins-specific or
  generated inventories, not only the default local environment.
- If the architecture resolves resources through names, selectors, or logical
  keys, validators should reject stale direct-ID override keys instead of
  accepting them as compatibility paths.
- For config values resolved by a runtime registry or host database, validate
  successful resolution rather than syntax alone, and make direct or internal
  consumers handle invalid persisted values predictably.
- Cloud or provider identifiers should not be pre-cast with lossy filters that
  convert invalid values into defaults before the provider client or module
  argument validation can reject them.
- Safe defaults versus private or local-only values, including ignored override
  files and tracked placeholders. Example configs that are installed as runtime
  defaults should not contain enabled placeholder sources or unreachable values
  unless the consuming command explicitly treats them as inert.
- Schema, fixture, manifest, discovery payload, and generated-artifact drift.
  For structured provider output, compare the exact accepted type union across
  schema, prompt, runtime validation, persistence/write, and verification;
  retain native booleans, numbers, strings, nulls, and collections wherever the
  downstream contract supports them.
  For generated artifacts, verify every supported output variant and marker
  path is included in discovery, reporting, and stale-check paths, including
  specialized filenames, nested instruction locations, and configured depth
  limits. Shallow discovery modes should still cover every documented container
  topology and should distinguish container directories from actual leaf items.
- Placeholder recovery for generated-artifact checks must round-trip
  user-supplied or template-specific values without recovering derived defaults
  such as project names, paths, dates, or other values that should change when
  the source context changes.
- URL, path, filename, escaping, and identifier changes that must preserve the
  stored representation and externally meaningful normalization. For generated
  public URLs, verify scheme, host, port, and path against the endpoint actually
  exposed in each environment, not only the canonical hostname. Ensure proxy
  host allowlists and direct-host catalogs admit every advertised address, and
  test the actual URL transport; a loopback request with a synthetic `Host`
  header is insufficient. When an address depends on a conditionally created
  endpoint or route, gate it on the same feature and lifecycle conditions and
  use a verified reachable fallback when that endpoint is disabled.
- Include/exclude filters should be applied before validating the remaining
  effective names. Reject path separators, traversal, and empty path components,
  but do not reject valid display names merely because they contain spaces if
  the downstream format supports them.
- JSON contracts where fields may be missing, null, scalar, or list (for
  example policy fields that accept either `"Action": "x"` or
  `"Action": ["x"]`): normalize shapes before sorting, iteration, or membership
  checks; preserve parsed empty arrays as empty, not as raw string targets; and
  add tests or fixtures that cover every accepted form plus a negative path.
- Case-insensitive collision checks for user-provided domains, hostnames, and
  derived local filenames across all output paths (especially when generating
  TLS materials or other filesystem artifacts). When inputs are prefixes,
  suffixes, or fragments that become final hostnames, URLs, or identifiers,
  validate the fully composed output against downstream length and format
  limits, not only the fragment itself.
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
