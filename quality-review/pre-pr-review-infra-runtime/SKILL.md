---
name: pre-pr-review-infra-runtime
description: Reviews infrastructure, runtime, deployment, CI, Jenkins, container, package-manager, and service lifecycle diffs before PR. Use when a pre-PR review area includes Ansible, Terraform, Docker, Compose, Workspace helpers, Jenkinsfiles, systemd, installers, deployment scripts, or OS package support.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Infra Runtime

Use this as a report-only reviewer profile for infrastructure and runtime slices
of a broader pre-PR remediation. Do not edit files.

## Review Focus

- Real runtime boundaries: host versus container execution, service startup
  order, environment propagation, mounts, permissions, and generated files.
- Docker copy equivalence: when replacing `COPY` with mounted `cp` or another
  optimized transfer, compare paths and root-directory metadata as well as file
  content. Preserve the destination root mode deliberately, keep copy and
  permission normalization in one layer where practical, and exercise distinct
  source and destination modes in the regression fixture.
- Multi-runtime resource identity: when Apple machines, Docker containers, or
  other backends can share logical names, lifecycle and cleanup helpers must
  query the explicitly targeted backend and propagate status or ownership-probe
  failures before continuing. Require a regression with an active same-named
  resource in the other runtime and with each status read failing.
- Runtime probe cadence: when a service accepts cache or interval parameters
  for expensive host probes, repeated run-loop samples must honor that cadence
  rather than re-running network, device, or package-manager commands every
  fast telemetry loop.
- Host device and interface discovery: optional tools and broad sysfs or API
  listings must be filtered to real host resources, handle multiple candidates,
  and continue past disconnected or peripheral devices before reporting a
  supported capability unavailable.
- Generated artifacts from secrets: when changing how files are derived from a
  secret store (for example generating SSH host public keys from stored private
  keys), validate the generation path against every configured secret entry,
  including legacy or historical keys; keep unsupported legacy types out of
  active provisioning loops and remove their on-disk artifacts explicitly.
- Inventory-aware validators and preflight checks: ensure validation reads every
  inventory/group-var topology used by Jenkins and Workspace paths, not only a
  generic environment mapping; if architecture moved to name-based resolution,
  ban stale direct-ID keys rather than accepting compatibility overrides.
- Host ↔ container boundary regressions: ensure container validation does not
  consume host-generated caches (for example, `.ansible/` symlinks) and rerun
  the real container commands after host linters have populated ignored cache
  directories.
- CI and Jenkins control surfaces: typed operator inputs, checkout or workspace
  restoration after agent switches, credential binding scoped to only the
  stages that need it, cleanup behavior, and release toggles.
- Deployment safety: idempotence, rollback or retry behavior, stale manifests,
  ignored-but-required runtime inputs, and environment-specific overrides. For
  source transformations that render a managed runtime artifact, identify the
  target AST owner or lifecycle block before replacing a textual pattern; fail
  closed on an unknown source shape and verify same-shaped code elsewhere is
  preserved. Validate the exact rendered structure and its runtime contract,
  including the one effective callback definition, compatible callee signature,
  unshadowed event registration, and synchronous cleanup semantics.
- Privileged path separation: before mutating boot, recovery, or control state,
  compare resolved device/inode identities across controls, sources,
  destinations, backups, and manifests. Ownership, mode, and final-component
  symlink checks alone do not reject hard links or symlinked-parent aliases.
  Authenticate symlinks separately from writable files and directories: verify
  link ownership, canonical target containment, target type, ownership, mode,
  and every ancestor immediately before privileged consumption.
  Validate final install targets and every artifact required after the mutation
  before the first persistent change; trusted ancestors do not prove that an
  existing target has the required file type. For configurable private
  directories, keep missing-parent creation reachable and revalidate the
  created path. Before recursive `state: absent` or equivalent cleanup,
  require the expected target type on enabled, disabled, and rollback paths.
  Mark privileged staging as attempted before an ambiguous transport or copy can
  begin, and run bounded cleanup for every attempted stage. Preserve the primary
  failure while surfacing cleanup failure and retaining only private evidence.
  Treat first recovery-backup creation as a provenance boundary: an absent
  recovery set is valid only while all managed markers, selections, and managed
  artifacts are absent; never create a rollback baseline from managed state.
- Kubernetes opt-in or debug Deployments that must remain idle should encode
  `spec.replicas: 0` in Git-managed manifests; do not rely on a historical live
  scale-down that would be lost if the resource is pruned or recreated.
- Optional Kubernetes-generated resources must be validated with their rendered
  consumers: inspect default and explicitly disabled configurations for dangling
  workload references, preserve declared external-resource overrides, and check
  the controller's empty-resource semantics before treating empty data as a
  reason to omit the resource.
- Failure-handling semantics: avoid masking failures that a `rescue` block
  depends on (for example `failed_when: false` inside the protected block);
  prefer explicit assertions that re-fail with captured context when a failure
  must be tolerated. Optional notification hooks must not abort critical service
  activation under fail-fast shells: exercise both enable and start/restart
  failures in the executed activation path, preserve diagnostics, and retain
  fatal handling for critical-service failures. Arm shutdown hooks independently
  of fallible startup notification work.
- Lock and claim-file primitives must be safe on synced, network, removable,
  and macOS/Linux filesystems: do not evict active owners by mtime alone,
  avoid ownerless crash windows or recover malformed ownerless locks after a
  grace period, and include a fallback when optional filesystem features such
  as hard links are unavailable.
- Ansible task-file inclusion semantics: use `include_tasks` (not
  `import_tasks`) for conditional execution when the included file contains
  `register`, `set_fact`, or other stateful facts; static `import_tasks` can
  still expand and run skipped registered tasks in ways that overwrite
  previously valid values. For tagged `include_role` entrypoints, verify tags
  propagate to included tasks with `apply`, role defaults needed by play-level
  consumers are public or explicitly declared, and standalone playbooks render
  the same effective consumer overrides as normal convergence.
- Stateful service recovery and credential rotation: authenticate every
  durable input and runtime path before recovery can mutate or restart, validate
  saved state without coercing malformed values, and require a bounded
  application-level readiness or authentication probe before advancing the
  durable phase; service-manager `active` state alone is insufficient.
- Ansible role task shape: keep `tasks/main.yml` orchestration-only (phase
  ordering and `include_tasks`), and extract operational blocks (module calls,
  loops, `set_fact`, `assert`) into named task files per phase.
- AWS Elastic IP cutovers: when an Ansible `amazon.aws.ec2_eip` task may move an
  already-associated EIP during promotion or rollback, require
  `allow_reassociation: true` or an explicit prior disassociation; otherwise the
  module can fail with AlreadyAssociated-style errors mid-promotion.
- Promotion/owner verification should consume effective promoted IP facts (for
  example dynamic Reserved IP or Elastic IP values), not only configured stable
  IP variables; require explicit assertions that the effective IP is resolved
  before SSH, DNS, owner, health-check, and cleanup stages proceed.
- Route 53 routing-policy migrations: treat routing policy changes as DNS
  migrations; require an explicit removal or batch-replace step for legacy
  record sets (for example failover `PRIMARY`/`SECONDARY`) before creating
  incompatible new policy records (for example latency) for the same
  name/type.
- Boot-time services that deliver through an external DNS-dependent transport:
  treat `network-online.target` as insufficient readiness. Do not run an
  unbounded DNS lookup before the bounded delivery path; use a local identity
  or explicitly bound and budget the lookup in the service timeout. Retry only
  identified temporary delivery failures, and verify permanent failures remain
  visible to the service manager. Timestamp-sensitive boot producers likewise
  need the platform's concrete clock-wait service, not only a synchronization
  target or network readiness; verify the rendered dependency and keep critical
  services independent of an optional producer's wait.
- One-off migration cleanup: when deleting or rewriting legacy resources is only
  required for a release transition, keep it out of steady-state lifecycle
  roles; use a dedicated migration playbook/command and document operator
  timing.
- Operator-only or standalone playbooks that reuse promotion tasks: explicitly
  re-discover managed state (or derive required facts) for that execution path,
  and fail closed when shared tasks require inputs that only exist during a
  promotion run.
- Dynamic validation matrices and helper discovery: prefer building steady-state
  file sets from git-tracked sources (for example `git ls-files`) instead of
  live filesystem globs that can accidentally include untracked scratch or
  one-off migration playbooks.
- Treat source checkouts and installed artifacts as separate runtime
  topologies. Run the installed entrypoint, keep writable defaults and runtime
  data outside immutable bundles, assemble payloads from positive tracked
  manifests, and reject malformed decoded metadata before member access.
  Cover isolated installed-artifact regressions, ignored-data exclusion, and
  upgrade preservation.
- Workspace command-tree renames: search the repository for old command names,
  including `AGENTS.md`, `TODO.md`, Jenkinsfiles, docs, scripts, and current
  changelog notes, not only operator-facing documentation.
- Readiness proofs and simulation helpers that gate merges or deployments:
  fail closed when a required simulation cannot run (for example AccessDenied
  on an operator IAM simulation) rather than warning while still reporting
  readiness success.
- Package-manager support through every real target and documented manual path:
  preserve an already satisfied system capability before installing a
  conflicting provider, propagate global skip-package controls to every nested
  installer, and fail clearly when an explicitly requested integration is
  missing under that control. Cover existing-provider, fresh-install, and
  skipped-missing-package states across distro differences.
- macOS/BSD portability for host-side tooling when the repo is operated from
  macOS.
- Validation against the running service or container state after creation, not
  only static rendered config.
- Privileged package, boot, and refresh hooks must revalidate at execution time
  any earlier hook or artifact they trust; deployment-time validation does not
  cover later replacement or deletion. Keep durable diagnostic state owned by
  the same runtime path, update it atomically, and include state repair in
  idempotent change reporting.
- Generated systemd units and boot-time helpers: inspect the rendered unit, not
  only the template; for every configurable value substituted into a unit,
  require its canonical path spelling when systemd consumes it: reject dot
  segments, duplicate or trailing separators, and aliases that bypass overlap
  checks. Validate the full string before mutation and exercise the exact consuming
  directive with the target systemd parser. Cover control characters, trailing
  whitespace, length bounds, path components, unit-template semantics, and an
  alternate valid value; do not assume quoting rules transfer between condition
  directives and executable directives. Escape systemd specifiers such as `%`,
  preserve literal shell `$` where needed, and verify command postconditions
  instead of trusting helper exit codes that may mask device or management
  errors.
- Hardware CLI parser fidelity: when boot-time helpers parse multi-device
  output from tools such as `btmgmt`, `nmcli`, or similar host CLIs, validate
  the smallest observable contract needed by the feature before mirroring the
  external tool's evolving command grammar. When parsing remains necessary,
  validate against real positive and negative samples for the supported
  versions so the parser cannot match the wrong device block or treat a partial
  success message as proof of the desired state.
- Wrapper correctness: flag command-wrapper argument tokenization/quoting bugs
  (for example, percent-formatting or silently-corrupted quoted command
  strings) and require a negative-path check when rejecting unsupported
  pass-through quoting.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag application contract, security, CLI, and documentation impacts as
  overlap risks unless they are directly inside the assigned infra scope.
- Prefer operational failure modes over generic maintainability comments.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command or live-safe probe,
- possible overlap with another reviewer area.
