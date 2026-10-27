# Changelog

All notable changes to this repository are tracked here.

## Unreleased

### Fixed

- Recognize current and legacy Gemini configurations on server updates,
  accumulate matching coin specimens within a planned batch, and prevent
  template refreshes from silently discarding configured placeholder values.

## [0.3.0] - 2026-10-26

### Added

- Added nine locally authored skills confirmed from Codex task history:
  `moneywiz-reconcile`, `gmail-filter-consolidation`, `comic-database-importer`,
  `hd-riders-survey`, `macos-disk-cleanup`, `verify-data-preservation`,
  `consolidate-agent-learnings`, `init-agents-file`, and
  `update-agents-file-templates`.
- Added a searchable `MARCOMC-SKILL` provenance marker to every bundled
  first-party skill, with repository rules distinguishing original work,
  user-requested adaptations, source-derived work, and unmodified third-party
  skills.
- Added a publication guard for book-, manual-, catalog- and dataset-derived
  skills: require redistribution permission or keep the generated material local.
- Added `app-icon-design` for current Apple app icon design and integration across macOS, iOS, and iPadOS, with separate guidance for Finder/Dock and macOS menu bar assets.

- Added `minimal-pr-diff` for evidence-based reduction of implementation branches
  while preserving required behavior, project conventions, and user staging boundaries.
- Added `pr-remediation-coherence-audit` for cumulative review of remediation
  evidence and affected contracts before publication.
- Added `gmail-coupon-cataloguer` for agent-reviewed discount codes and links,
  same-day incremental Gmail scans, verified Sheets imports and twelve-month
  promotional-mail retention with protected purchase records and private profiles.
- Added `jev-gateway-codex-desktop` for portable Jev Gateway setup and Codex
  Desktop routing, with hidden key entry, backup, rollback, and Desktop-specific
  verification guidance.
- Added `version-breaking-change-analysis` for evidence-backed comparison of
  software or plugin releases and their concrete impact on a target project.
- A `world-coin-banknote-cataloguer` skill for evidence-backed photograph
  identification, exact-issue research, duplicate reconciliation, typed Google
  Sheets updates, and conservative post-write verification.
- A neutral `review-coordinator` owns local review/remediation, risk-selected
  coverage and one readiness contract. Existing entrypoints and old helper CLI
  paths remain available without opening nested review loops.
- A per-requirement evidence evaluator preserves current checks across unrelated
  changes and invalidates changed contracts, feedback, policy or dependencies;
  required gaps and recurrence stops remain non-success states.
- Head-bound cloud review evidence prevents stale reactions from ending newer
  passes or hiding quota blocks and location-linked issue-comment findings.
  Completed convergence sweeps clear resolved suspicion without consuming the
  recovery allowance; legacy free-text sweep records remain readable.
- Conditional review references replace repeated entrypoint checklists. Policy
  stays stable per run, with terminal learning and observed-outcome calibration
  aimed at total local/cloud usage per completed change.
- Stable remediation family IDs, shared-contract convergence signals and
  explicit recovery completion, with compatibility for existing ledgers.
- Shared pre-publication defect closure covering reachable siblings and valid
  compatibility cases; cumulative audit before cloud review and reuse of
  verified unchanged evidence after it.
- Content/environment fingerprints and mechanical audit preflight, separating
  bookkeeping gaps from stale validation; compact monitoring and per-category
  cost accounting without treating unknown usage as zero.
- Refined review checks for validation-derived repair preservation, localized
  field contracts, positional identity qualifiers, nullable provider schemas,
  historical aliases, installer-generated schemas, numeric parsing exceptions,
  typed readback, complete diagnostic matching with compatibility positives,
  API-specific model controls, scoped defaults, remaining-detail reconciliation,
  exact-version entrypoint admission, aggregate versus weighted component
  evidence, order-independent migration ambiguity checks, and immutable-version
  recovery with complete discovery, and provider-specific terminal evidence
  before paid failover. Numeric wrappers retain canonical parser acceptance;
  accounting distinguishes missing and partial usage from genuine zero, and
  runtime-policy verification covers every changed template rule.
- Detect current-head, location-linked findings in submitted Codex review
  bodies, including feedback without inline threads; keep resolved inline
  duplicates and older-head feedback from reopening completed work.
- Added a generic loop-health circuit breaker to the Codex PR remediation
  workflow, including deterministic recurrence analysis, one bounded recovery
  epoch per finding family, and a non-clean safety stop for pathological loops.

### Changed

- Reconciled eight existing skills with their active local sources:
  `codex-pr-review-remediation-loop`, `pre-pr-review-backend-services`,
  `pre-pr-review-cli-tooling`, `pre-pr-review-infra-runtime`,
  `pre-pr-review-tests-validation`, `scoped-pre-pr-remediation`,
  `create-github-release`, and `mcpone-install-mcp-server`.
- Hardened GitHub release creation to detect missing intermediate versions and
  avoid accidentally marking historical releases as latest.
- Extended the McpOne installer and guidance for authenticated Streamable HTTP
  servers, multi-cluster enablement, JSON-agent synchronization, and Codex's
  separate HTTP configuration path.

### Fixed

- Preserve existing unmanaged instruction files when applying generated
  templates, and report missing template-report companion skills explicitly.
- Keep macOS cleanup dry runs free of cache mutations, handle filenames
  containing newlines safely, and preserve targets when `lsof` emits diagnostics.
  Resolve package-manager cache locations before cleanup and preserve caches on
  unsupported or inconclusive discovery. NPM integrity-check failures now
  propagate after authorized cleanup.
- Validate McpOne JSON sync targets and server identity before changes, preserve
  WAL-aware database backups, and restore replaced files on caught write failures.
  Migrate prior Gemini configuration shapes without duplicate servers, reject
  stale config plans, and redact credentials from command output.
- Preserve TOML statement boundaries and comments when the Jev configurator
  changes the root provider immediately before a table.

## [0.2.0] - 2026-07-21

### Added

- Expanded CLI and installer review guidance for isolated staging, safe cleanup,
  atomic promotion, parser-shape checks, and recovery semantics.
- Added configuration and data-flow checks for native override types, inert
  defaults, shallow discovery topologies, and filter-before-validation order.
- Strengthened documentation, security, and validation guidance for shell
  expansion, credential exposure, negative-path coverage, and dry-run parity.
- Synchronized the updated review profiles with their installed source-of-truth
  copies to retain existing lifecycle, migration, and fixture-isolation checks.

## [0.1.0] - 2026-06-13

### Added

- Added the initial personal agent skills collection.
- Grouped 43 skills by root-level category for `skills@latest` discovery.
- Added install, listing, maintenance, and relationship documentation.
- Added public-repository hygiene files.
- Added repository agent instructions for public-safe skill maintenance.
- Removed hard-coded maintainer-machine paths from public docs and helpers.
