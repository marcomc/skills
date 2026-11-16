---
name: pre-pr-review-backend-services
description: Reviews backend service, API, worker, persistence, and domain logic diffs before PR. Use when a pre-PR review area includes server-side application code, HTTP APIs, background jobs, database or file persistence, validation logic, queues, or service integrations.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Backend Services

Use this as a report-only reviewer profile for backend or service slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Behavior contracts for APIs, CLIs, workers, scheduled jobs, and service
  integration points. Provider request controls must match the exact API and
  configured model, including explicit pins, fallback, and cooldown routes;
  similarly named APIs may expose different supported controls.
- Paid or privileged failover requires explicit provider-specific terminal
  error evidence. Prefer documented error codes and typed violations; shared
  quota metrics, status codes, prose mentions and help links do not establish
  exhaustion. Exercise transient errors with terminal terminology, genuine
  terminal responses, opt-out, cooldown reuse and the fallback provider itself.
- Preserve missing provider accounting as unavailable, distinct from explicit
  zero counters. Test final events across every provider adapter, including
  cached counters and partial metadata. Derived cost estimates require all
  priced dimensions before defaults are applied; presence alone is insufficient.
- Error handling, retries, idempotence, partial failure, timeout, and cleanup
  paths. For journaled multi-step mutations, model every externally durable
  transition explicitly: persist each completed step before the next fallible
  action, repeat completed-state fields in fallback writes, and make recovery
  resume from the latest checkpoint instead of re-requiring an already-deleted,
  moved, renamed, or replaced resource. Test synchronous failure, hard
  interruption, retry, and recovery after each mutation boundary.
  Include immutable version creation: save its identity before inspection or
  promotion and resume without republishing source. Planned-only adoption
  requires complete paginated discovery; a truncated CLI list cannot prove
  absence or uniqueness. Keep read-only preflight before planned ownership.
- At a row-level read boundary, contain malformed-data conversion failures
  (including domain wrappers around converter exceptions) in the per-row error
  report, while explicitly re-raising schema or compatibility failures that
  invalidate the whole read. Exercise both paths.
- For large read-only reports, review pagination and expensive per-item history
  against the report deadline. A bulk current-state inventory must remain
  complete, while authorization paths retain their own exact history evidence.
- For recovery status projections, compare authenticated terminal role evidence,
  the original run deadline and route-specific retry eligibility separately.
  Exercise stale preparation messages and conflicting evidence; do not infer the
  original send outcome from a retry rejection or overwrite preserved controls.
- When admission relies on a checkpoint remaining fresh throughout a worker
  window, compare its expiry with the full proposed deadline before claiming.
- When closed tasks satisfy dependencies, distinguish completed work from a
  superseded or cancelled task; verify and rebind open dependents to an
  authorized replacement or hold them before closing the original.
- When recovery relies on a particular status return, verify its event lineage
  against later status changes. Preserve the original event and hold unsupported
  supersession rather than inventing a recovery path.
- Before withdrawing an unread execution marker, verify the exact terminal
  owner, marker identity and absence of a journal, attempt or invocation.
  Preserve markers with possible effects; a file access time alone is not proof
  of mutation or consumption.
- For private state lookup, avoid mutation serializers only when current owner,
  mode and path invariants already hold. Keep unsafe repair and creation
  serialized; exercise a safe lookup while the serializer is held.
- Validate private admission files with the actual runtime reader, including
  ownership, mode, size and link-count requirements. Keep evidence copies
  separate from the admitted file and preserve missed occurrences without replay.
- A frozen result object does not freeze nested collections. Publish reports
  with defensively copied immutable mappings or collections, then test that
  neither mutation of the input nor a cast of the exposed value can change the
  published evidence.
- Per-resource retry suppression or backoff must not mask aggregate service
  health checks or fleet-level recovery triggers; require tests for both
  single-resource degradation and all-resources-unreachable states (including
  mixed “timeout” and “not found” style failures across the entire enabled
  fleet). Optional notification-state failures must not suppress independently
  authorized recovery actions. Separate delivery barriers from recovery gates;
  test every recovery policy and fresh-process checkpoint reload while retaining
  fail-closed behavior for genuine authorization or checkpoint failures.
- Capture one absolute execution deadline at each public worker or service
  entrypoint and thread it through preprocessing, fallback, recovery, and
  retry calls; never let a helper start a fresh budget after work has already
  consumed invocation time.
  Keep bounded transport phases distinct from that fixed deadline and exercise
  slow non-transport checks before the final send and hard-limit revalidation.
- When retrying transient provider reads, bound retries to the identified
  transport error, original request and attempt budget. Test recovery and terminal failure,
  and prove mutation paths are not replayed by the read retry.
- When changing persisted metadata encoding, version new writes and preserve
  legacy decoding semantics. Test literal escapes, malformed tagged data and
  repeated round trips through real downstream consumers.
- When a retry receives malformed or empty output, retain the last fully
  normalized, schema-valid state for the next attempt and final failure context.
  A partial snapshot attached to a normalization error is fallback context only
  when no sanitized predecessor exists; exercise every such error producer.
  In validator-guided repair, preserve a value group only after all relevant
  checks passed; an earlier failure does not validate unreported fields.
  Derive preservation metadata from completed checks, reset it on each pass,
  and reopen linked aggregates when detail or alias validation fails.
- Treat output as successful only after validating the consumer-usable contract
  (for example, readable non-whitespace text). Apply that same predicate before
  retry/failover, cache reuse, finalization, persistence, and downstream
  consumers such as TTS; remove rejected temporary artifacts so later stages
  cannot bypass the check. Readiness and completeness flags require their
  documented explicit boolean value; missing, null, numeric, or string values
  must not establish permission to proceed. When acceptance depends on source
  coverage, derive it from original input through a shared consumer adapter and
  preserve prior incompleteness; a lossy projection or caller flag is not proof.
- Service probes, recovery paths, and readiness checks that must prove the same
  protocol handshake, authentication, authorization, and client identity used
  by the real workflow, not only transport reachability.
- Input validation, authorization boundaries, tenant or environment scoping,
  and safe handling of secrets or private values.
  For model-derived records, require source evidence for every retained factual
  field, including free-text notes and conditions; grounded identity fields do
  not validate the rest. Missing evidence must clear the field or require review.
  Validate complete key sets, nested evidence shapes, and control types before
  projection; silently dropping unknown factual keys or misspelled fields must
  not produce an auto-accepted record. Discovered resource attributes are not
  inspected-resource evidence; preserve that separation through the consumer.
  Oversized structured fields must be cleared or rejected, not silently shortened
  into actionable identities or values. Keep explicitly marked descriptive
  previews separate from actionable data; review alone does not restore lost data.
  Test mixed grounded and invented fields through the final acceptance predicate.
- HTML extraction should share a standards-aware parse tree between text and
  embedded resource discovery. Preserve document/container context and wrapper
  attributes; test full documents and snippets before choosing a parsing mode.
  Test EOF inside tags or comments, raw-text and RCDATA contexts, inert templates,
  and script/comment cross-context strings;
  malformed attributes and hidden content must not become evidence or resource
  URLs. Apply visibility and exact-attribute filters to parsed nodes, preserving
  visible text and resource positives under the configured scripting mode.
  Map evidence eligibility across namespaces and subtree roles; HTML exclusions
  do not establish visibility for SVG definitions, symbols, or metadata. Test
  foreign-content boundaries and retain separate visible-content positives.
  Use standards-complete character-reference decoding once per original text
  span after lexical classification and before concatenation; decode attributes
  in their own context. Test references split across hidden markup, named-case
  and longest matches, legacy semicolons, numeric replacements, and double
  encoding. Never combine fragments into a new reference or reparse decoded markup.
- Multi-stage classification contracts: trace an admitted value through every
  downstream guard and consumer so a broader legacy veto cannot silently undo
  the upstream eligibility decision.
- Aggregate evidence filters: discard records with unusable payloads before
  identity, provenance, or trust checks; irrelevant malformed records must not
  turn otherwise valid evidence into conflict or failure. Define deduplication
  keys with the applicable scope, event kind, local identity and revision. Define
  checkpoint identity separately for its domain while retaining its scope;
  downstream grouping must preserve relevant scope and kind. Test equal local
  IDs across scopes and kinds, checkpoint isolation across scopes, and
  contradictory evidence for an exact key.
- Resource alias and destructive-target guards must compare stable provider
  identifiers, not in-memory service-wrapper identity. Test separate wrapper
  objects for the same remote resource and distinct resources with similar
  names before any clear, replace, move, or delete.
- Persistence compatibility: migrations, serialized formats, file paths,
  generated outputs, and backward compatibility with existing data.
  When a migration removes a database constraint still relied on by older
  writers, preserve the required admission invariant across rollback. Test an
  old write against the migrated database and any atomic replacement guard.
  Never adopt an unchanged cache as a durable baseline after a failed first
  checkpoint. Test absent and existing-empty files across unchanged retry
  cycles; preserve unsaved observations without overriding genuine peer ACKs.
- File-backed queues and outboxes: serialize the complete read, side effect,
  checkpoint, and removal transaction against concurrent producers; keep one
  writer/reader canonicalization invariant; normalize setup and cleanup errors;
  and require file fsync, atomic replace, then parent-directory fsync after
  replace or unlink. Test concurrent enqueue, every checkpoint failure, and
  crash-durability boundaries, including retries that accept an existing or
  idempotency-matched file after an earlier failed durable commit. Visible
  contents alone do not prove durability; reestablish the required barriers
  before acknowledging reused state. Pending-queue deduplication does not
  prevent replay after delivery removes an item: retain incident-scoped queue
  receipts when that guarantee is required, distinguish changed outcomes and
  later recovery attempts, and test successful delivery followed by restart.
  A summary must represent every retained item it acknowledges or removes;
  test beyond display caps with a unique early failure and retain unsent items
  when transport fails.
- Shared file-backed workflow state: atomic replacement protects one write,
  not a cross-process read-modify-write transaction. Check that every mutator
  uses a shared transaction lock and that concurrent remote operations are
  serialized for their whole workflow, not only each journal write. Require
  subprocess regressions for competing operations and retained concurrent updates.
- Asynchronous operation ownership must be released on thread-start failure
  and shutdown; initialization must refuse an active operation. Trace these
  lifecycle boundaries separately from durable transaction locking and test
  their failure paths.
- Config loading and default propagation into runtime behavior.
- Audit deduplication must respect incident boundaries: reset failure suppression
  after idle or recovery and record each distinct successful side effect. Test
  repeated identical failures, idle then recurrence, and consecutive successes.
  Persist the first observed recovery endpoint and freeze derived duration across
  queue and acknowledgement retries. Transfer an ended incident before a new
  failure replaces its identity; test delayed delivery, restart, and recurrence
  before acknowledgement.
  Keep cumulative incident age separate from retry pacing after completed
  recovery actions. Persist the new attempt origin without resetting it on
  ordinary process restarts; test completion handoff with the real evaluator,
  not only a stubbed transition, so old incident age cannot reauthorize work.
  Shared-helper failures must name the actual operation or caller, not an
  unrelated feature that also uses the helper.
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
