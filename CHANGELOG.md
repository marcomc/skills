# Changelog

All notable changes to this repository are tracked here.

## Unreleased

### Added

- Add `update-release` for scoped TODO, changelog and version preparation with
  stable source IDs, issue links, optional chat coverage and fresh remote
  mainline/tag/release evidence, including already reconciled feature branches.
- Add a bound-plan handoff to `create-github-release` with a default publication
  lock shared across same-host worktrees and processes, plus an optional live
  external gate adapter for projects requiring multi-host exclusion.

### Fixed

- Stop ambiguous release reads and failed edits from falling back to creation;
  retain uncertain write outcomes for read-only reconciliation. Verify exact
  remote tag objects/peeled commits and preserve historical non-latest releases.

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
