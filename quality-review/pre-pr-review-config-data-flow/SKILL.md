---
name: pre-pr-review-config-data-flow
description: Reviews configuration, defaults, examples, schemas, generated files, path or URL encoding, and data-contract propagation before PR. Use when a pre-PR review area adds or changes config keys, templates, override files, schemas, manifests, generated artifacts, identifiers, serialization, filenames, or URL/path handling.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Config Data Flow

Use this as a report-only reviewer profile for configuration and data-contract
slices of a broader pre-PR remediation. Do not edit files.

## Review Focus

- Every config key across load, write, validate, examples, docs, installers,
  generated files, and runtime use. Derived filename, period, identity, or
  eligibility parsers must consume the normalized effective value or canonical
  predicate instead of re-embedding a shipped default.
  When templates have separately maintained runtime copies, verify every
  changed rule against the effective installed copy and preserve installation
  overrides; checking only the reported paragraph can miss conflicting rules.
- For mode-dependent configuration lifecycles, trace downstream validation
  inputs even when the selected mode preserves or skips the writer. Test each
  supported mode against existing and missing config, validation enabled and
  disabled, and explicit versus generated companion credentials or metadata.
- When a selected mode declares a range or capacity, derive every client control
  from that effective mode value rather than a legacy global cap. Test the
  declared upper bound through the user-facing selector and runtime consumer.
- During bootstrap, keep validated pending configuration distinct from installed
  persisted configuration. Pass the pending effective values through every
  initializer and validator that runs before the persistence commit; add fresh
  install and resume regressions proving no early global config loader is used.
- Before creating derived dashboards, helper sheets, generated files, or other
  managed artifacts, validate the complete source schema and supported capacity.
  Missing prerequisites must fail clearly or no-op without leaving partial
  generated state; cover both complete and incomplete source contracts.
- When a new required field is added to persisted configuration, inventory
  previously serialized shapes before enforcing it. Keep new input strict, but
  provide an explicit compatibility or migration path before old scheduled or
  event-driven consumers load the field; test both uninterrupted legacy reads
  and the operation that persists the migrated value. A legacy pending or
  readiness flag does not prove that a newer identity field exists: normalize
  and durably persist missing identities before side effects, preserve existing
  identities and origins, and cover every supported phase on resume.
- Persisted version, migration, or readiness markers that skip target work must
  include the target resource identity, not only a global version. Test a
  legacy marker, a repeated run on the same target, and reconfiguration to a
  different target so the new resource cannot inherit stale completion state.
- When a changed shipped default was materialized in existing generated config,
  migrate only provenance-detectable generated values; never infer an explicit
  override solely from a matching former default. Test absent, known-generated,
  and explicit old-default values across repeated rewrites.
- Defaulting and diagnostic-suppression logic must require evidence aligned to
  the named field. Keep generated defaults distinct from explicitly printed
  equal values, and suppress a missing-field notice only when that exact field
  is empty and the complementary required identity is present. Test absent,
  literal-default, ambiguous, and contradictory populated-field paths.
  Distinguish authoritative overrides from inferred-value restrictions, and
  require every informational exception to consume the whole statement and
  corroborate concrete identifiers. Test blocking prefixes, suffixes, and
  embedded clauses across all exception predicates, even without punctuation.
  Pair stricter grammars with previously accepted equivalent wording and number
  formats through final admission and writes. Scope default-related field
  exclusions to the same target eligibility as the default producer.
- Notification recipient and disable settings across routine, error, and
  fallback delivery paths; require end-to-end custom-recipient and no-send
  tests when replacing a native notifier. For queued localized notifications,
  persist canonical facts rather than enqueue-time translations; render both
  templates and production diagnostic values in the current delivery locale.
  Test decoded output across supported locales, including locale changes after
  failed delivery and process restart. Migrate only recognized legacy payloads
  with unambiguous semantics; retain unknown freeform details and original
  incident identities.
- Identity and alias validators must use the exact normalization implemented by
  runtime lookup. Reject normalized canonical collisions, alias-to-alias
  collisions, canonical-shadowing aliases, empty normalized identities, and
  duplicate override tuples; test punctuation and diacritic variants.
  Exercise localized validators with every supported canonical identity and
  field alias. Remove optional qualifiers only in their verified component
  position; preserve substantive tokens that resemble codes or metadata.
  Extracted identifiers must preserve a complete source token or reject it,
  never emit a prefix ending at unsupported punctuation. Extraction and evidence
  checks must share whole-token interpretation, corroborating boundaries in both
  the quoted fragment and original source. Distinguish matching outer quotes from
  internal punctuation, and require a boundary after introducers. Test embedded
  introducer words, internal quotes, proper prefixes/suffixes, Unicode, and
  over-limit inputs. Define length units
  explicitly (bytes, UTF-16 units, code points, or graphemes) and test supplementary
  and combining characters at both limits. Permitted preview clipping must not
  split a surrogate pair; preserve whole identities or reject them.
  After a canonical rename, exercise historical lookup with untouched stored
  labels and migrated configuration; normalize both sides through that config.
  Migration must check the complete legacy/target match set before first-match
  selection or an already-current no-op; test both orders before any write.
- When one request carries schemas for multiple target types, preserve the
  target-to-schema relationship instead of flattening a union. Prompt or
  serialization contracts must select fields only from the resolved target,
  and runtime validation must enforce that same target-specific schema.
- When storage layouts expose aliases for semantic fields, accept only
  one-to-one mappings or a verified discriminator. Reject duplicate aliases as
  unsupported before parsing, and ensure compatibility errors cannot fall into
  best-effort malformed-record handling.
- When authoritative fields share a payload with extensible user or model
  values, define their precedence once and apply it consistently in
  normalization, writes, verification, and recovery. A generic overlay must
  not replace protected canonical fields; test both conflicting and absent
  overlay values.
- Structured overrides crossing CLI, wrapper, or serializer boundaries must
  preserve native types. Do not assume `key=value` parsers coerce booleans,
  numbers, nulls, or collections; prefer structured JSON or YAML input and
  assert the effective type at the consuming runtime.
- For configurable timeouts, watchdogs, retries, or caps, trace the effective
  value through every runtime phase and call-site default. A documented global
  control should not be shadowed by hard-coded per-call defaults, and an outer
  watchdog should bound setup, work, cleanup, notification, and other companion
  phases unless the docs explicitly narrow its scope. For fan-out work, carry
  one shared budget across every child item and nested container; consume it
  before each resource-using attempt, including failures, and test multiple
  children plus one child containing more work than the full run limit.
- When reconciling a durable scheduled resource whose provider metadata omits
  cadence, persist a canonical desired schedule and compare it during
  reconciliation. Baseline legacy resources without replacing them, preserve
  matching resources, replace only changed recorded schedules, and test fresh,
  legacy, unchanged, changed, and replacement-cleanup-failure paths.
- For templated numeric settings, especially Ansible role variables rendered
  into systemd units, commands, retries, or timeouts, require an explicit
  shape and range assertion before casting. Lossy filters such as `int` must
  not silently turn invalid input into `0` or another default.
  Numeric guards must compare downstream values and units, not lexical spelling.
  Test leading zeros, whitespace, and decoded attributes; distinguish absolute
  dimensions from percentages instead of treating equal digits as equal sizes.
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
  files and tracked placeholders. Static and syntax gates must run from a clean
  checkout without ignored overrides; a tracked fallback must be inert or fail
  closed at runtime. Example configs installed as runtime defaults should not
  contain enabled placeholder sources or unreachable values unless the consumer
  explicitly treats them as inert. For configurable managed paths, stat the
  parent and create only a missing role-owned parent; never change an existing
  system parent merely to prepare a child path.
- Schema, fixture, manifest, discovery payload, and generated-artifact drift.
  For structured provider output, compare the exact accepted type union across
  schema, prompt, runtime validation, persistence/write, and verification;
  retain native booleans, numbers, strings, nulls, and collections wherever the
  downstream contract supports them. Verify provider-specific nullable enum
  and union translations against the current API contract and outbound payload.
  Exercise validators with schemas emitted by the actual installer or template
  producer, including optional aggregate fields and complete component groups.
  Keep configured columns distinct from printed representations: accept a
  verified aggregate when its entire component breakdown is absent, and check
  weighted component totals even when rates differ. Carry validation-only
  evidence through provider schemas and repair without inventing output cells.
  A verified absent component must not disable reconciliation of the remaining
  configured partition or manufacture a persisted numerical zero.
  Numeric wrappers must delegate ambiguity decisions to the canonical parser
  and add only field-specific unit/sign constraints. Test native numbers and
  equivalent localized strings, including leading-zero and grouped forms,
  through admission, writes and verification; duplicate vetoes can reject
  values the shared parser intentionally accepts.
  At write verification, assert native cell type and exact text presentation;
  reserve monetary tolerance for monetary fields and preserve rate/quantity
  precision. Historical rollback must restore its original types and formats.
  For generated artifacts, verify every supported output variant and marker
  path is included in discovery, reporting, and stale-check paths, including
  specialized filenames, nested instruction locations, and configured depth
  limits. Shallow discovery modes should still cover every documented container
  topology and should distinguish container directories from actual leaf items.
- For generated or model-produced artifacts, define one consumer-usable
  acceptance predicate and apply it before retry or failover decisions, cache
  reuse, finalization, persistence, and every downstream consumer. Cover an
  existing-but-unusable artifact through each reachable boundary, including
  rejected-artifact cleanup and consumer non-invocation. Version promotion and
  pending-resource adoption must inspect the exact artifact against one complete
  public-entrypoint contract. If recognition is lexical, test guarded/nested
  declarations and function-like text in strings, regexes, and nested templates;
  compile without executing source and preserve valid declaration positives.
- Placeholder recovery for generated-artifact checks must round-trip
  user-supplied or template-specific values without recovering derived defaults
  such as project names, paths, dates, or other values that should change when
  the source context changes.
- URL, path, filename, escaping, and identifier changes that must preserve the
  stored representation and externally meaningful normalization. URL extraction
  must distinguish prose delimiters from legitimate path/query punctuation;
  test surrounding punctuation, valid internal punctuation, and proper-prefix
  mismatches without silently changing the destination. Require a leading scheme
  boundary so an embedded URL substring cannot become standalone evidence. For generated
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
  TLS materials or other filesystem artifacts). Before mutating a pre-existing
  output, verify a managed marker or exact schema/header; otherwise preserve it
  and allocate a collision-safe name that later runs can rediscover. When
  inputs are prefixes, suffixes, or fragments that become final hostnames,
  URLs, or identifiers, validate the fully composed output against downstream
  length and format limits, not only the fragment itself.
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
