---
name: pre-pr-review-infra-runtime
description: Reviews infrastructure, runtime, deployment, CI, Jenkins, container, package-manager, and service lifecycle diffs before PR. Use when a pre-PR review area includes Ansible, Terraform, Docker, Compose, Workspace helpers, Jenkinsfiles, systemd, installers, deployment scripts, or OS package support.
---

# Pre-PR Review Infra Runtime

Use this as a report-only reviewer profile for infrastructure and runtime slices
of a broader pre-PR remediation. Do not edit files.

## Review Focus

- Real runtime boundaries: host versus container execution, service startup
  order, environment propagation, mounts, permissions, and generated files.
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
  ignored-but-required runtime inputs, and environment-specific overrides.
- Kubernetes opt-in or debug Deployments that must remain idle should encode
  `spec.replicas: 0` in Git-managed manifests; do not rely on a historical live
  scale-down that would be lost if the resource is pruned or recreated.
- Failure-handling semantics: avoid masking failures that a `rescue` block
  depends on (for example `failed_when: false` inside the protected block);
  prefer explicit assertions that re-fail with captured context when a failure
  must be tolerated.
- Lock and claim-file primitives must be safe on synced, network, removable,
  and macOS/Linux filesystems: do not evict active owners by mtime alone,
  avoid ownerless crash windows or recover malformed ownerless locks after a
  grace period, and include a fallback when optional filesystem features such
  as hard links are unavailable.
- Ansible task-file inclusion semantics: use `include_tasks` (not
  `import_tasks`) for conditional execution when the included file contains
  `register`, `set_fact`, or other stateful facts; static `import_tasks` can
  still expand and run skipped registered tasks in ways that overwrite
  previously valid values.
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
- Workspace command-tree renames: search the repository for old command names,
  including `AGENTS.md`, `TODO.md`, Jenkinsfiles, docs, scripts, and current
  changelog notes, not only operator-facing documentation.
- Readiness proofs and simulation helpers that gate merges or deployments:
  fail closed when a required simulation cannot run (for example AccessDenied
  on an operator IAM simulation) rather than warning while still reporting
  readiness success.
- Package-manager support through the real target path, including minimal
  package conflicts and distro differences.
- macOS/BSD portability for host-side tooling when the repo is operated from
  macOS.
- Validation against the running service or container state after creation, not
  only static rendered config.
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
