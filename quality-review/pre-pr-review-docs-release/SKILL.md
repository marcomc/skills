---
name: pre-pr-review-docs-release
description: Reviews documentation, changelog, README, release notes, operator runbooks, versioning, and PR-readiness text before PR. Use when a pre-PR review area includes Markdown docs, README updates, changelogs, install or upgrade instructions, release metadata, examples, or operator-facing workflow changes.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Docs Release

Use this as a report-only reviewer profile for documentation and release slices
of a broader pre-PR remediation. Do not edit files.

## Review Focus

- Docs that match the new behavior, flags, defaults, environment variables,
  installer flow, release toggles, and operator controls.
- When docs instruct operators to bypass a wrapper command (for example to pass
  extra tool flags), document every wrapper responsibility that must be
  replicated (credentials, environment sourcing, key material, and scoped
  cleanup) and include a matching cleanup snippet; prefer offering a wrapper
  subcommand for common ad hoc flags.
- When a change updates literal identifiers that appear in operator surfaces
  (for example image IDs, instance names, or build selectors), sweep the repo's
  docs, changelog, examples, and scripts for stale references and update them
  in the same change.
- Changelog entries that are reviewer-friendly, grouped, and placed under the
  correct version or `Unreleased` section.
- For release-prep branches where the "pending release body" is the latest
  concrete release section, prefer placing new entries in that section (and
  compacting repeated bullets) instead of creating a new `Unreleased` section
  or scattering duplicates.
- Concrete changelog release headings that use valid `YYYY-MM-DD` dates when a
  release entry is dated. If a heading includes an optional descriptive suffix
  after the date, preserve it unless the repository explicitly forbids that
  style. Older release headings may use a simpler legacy style; do not remove a
  newly introduced descriptive suffix solely for consistency. If the repository
  has a changelog parser or release-note generator, verify it tolerates the
  optional description field or update it; if no parser/tooling exists, do not
  invent a cleanup finding for the suffix alone.
- README table of contents when the README is materially changed.
- Installation examples that invoke a newly installed bare command must put the
  required default command directory on `PATH` before the first invocation, or
  use the installed command's absolute path. Check that custom-prefix examples
  verify through the matching command location.
- Copy, export, fixture, and sanitization procedures must name the source and
  destination mutation boundaries precisely. Do not call a read-only source
  disposable when only the generated destination may be modified.
- Release version synchronization: when a release version changes or a
  changelog heading becomes concrete or dated, verify the exact version across
  package manifests, runtime constants, bundle metadata, tracked lockfiles,
  generated protocol metadata, docs and contract examples, and exact-version
  tests. Use `MAJOR.MINOR.PATCH` unless the repo documents a different scheme.
- Examples and placeholders that are safe, non-private, and still deployable
  when meant to be defaults. For executable examples, evaluate the actual shell
  assignment and expansion order; do not assume a command-prefix assignment
  changes `$VAR` expansion in the same command. Check current CLI parsing too,
  so strict validation flags include required companion arguments. Parse
  multiline snippets with their declared shell to verify continuations remain
  one command with the intended flags.
- When a branch changes compatibility constraints (runtime versions, dependency
  bounds, or builder images), reconcile every public surface in one pass:
  dependency constraints (for example Composer), README requirements, CI/build
  matrix, container images, and PR notes/validation summaries.
- Public PR notes and validation summaries should avoid local-only project
  names, usernames, home paths, hostnames, IPs, or private command names.
  Describe real-project smoke evidence generically unless the project is
  intentionally public and relevant.
- Runbooks must label expected output separately from observed validation.
  Operational evidence should record the command, actual relevant result, and
  follow-up action; placeholders are examples, not proof of deployment.
- For GitHub release asset examples in docs, ensure `releases/download/<value>`
  uses a real tag (or switch to `releases/latest/download/...`) so copy-paste
  install commands do not point at non-existent assets.
- Markdown lint risks in changed documentation.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag code, config, security, and validation mismatches as overlap risks unless
  the fix is purely documentation.
- Prefer stale or misleading operator guidance over copyediting-only findings.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command,
- possible overlap with another reviewer area.
