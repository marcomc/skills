---
name: pre-pr-review-cli-tooling
description: Reviews CLI, shell, Makefile, helper script, installer, uninstall, and local developer-tooling diffs before PR. Use when a pre-PR review area includes shell scripts, Make targets, command wrappers, argument pass-through, install or teardown commands, local automation, or cross-platform host tooling.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review CLI Tooling

Use this as a report-only reviewer profile for CLI and local-tooling slices of a
broader pre-PR remediation. Do not edit files.

## Review Focus

- Shell safety: quoting, declared shell compatibility, `shellcheck --enable=all`
  findings, and justified suppressions only when necessary.
- Secret field parsing: when shell helpers read multiline secret fields (for
  example, SSH private keys) from 1Password, prefer a single `op item get`
  JSON read and extract the exact field with `jq` instead of line-based
  `--fields` output or JSON filters piped through `head` that can truncate
  values. If the field is concealed, the JSON read must include `--reveal`;
  add a fake-`op` or fixture check that fails when the value remains concealed.
- Raw pass-through argument handling as data, never via `eval` or shell parsing
  tricks.
- CLI options that use a config policy when omitted must keep omission distinct
  from an explicit value, resolve the effective value after config and target
  type are known, and test both default and override paths.
- Installer subprocess isolation: when wrappers call external installers or
  package managers, verify staged execution redirects `HOME`, XDG-style config
  roots, tool-specific config homes, caches, and generated side effects away
  from the real user environment before promoting results.
- Captured helper output: command substitutions and parsed stdout must contain
  only machine-readable return data. Prompts, progress text, menus, and
  operator hints belong on stderr or a terminal, with an interactive negative
  test when stdout is later tokenized as packages, flags, or commands. When a
  wrapper runs an interactive child CLI, verify output capture does not turn the
  child into a non-TTY and silently disable progress, prompts, or rich terminal
  rendering that users still expect.
- Command-substitution side effects: functions invoked through `$(...)` run in
  a subshell, so parent-shell state, cleanup registrations, and lock metadata
  do not survive. Flag helpers that allocate credential files or other durable
  resources while their stdout is captured. Prefer streaming secrets over
  stdin; otherwise allocate and register cleanup in the parent shell, with a
  regression that proves no secret-bearing artifact remains.
- Terminal prompt fallbacks: when TTY probes guard terminal-state setup, ensure
  failed probes do not leave uninitialized state that later restore, echo
  control, or cleanup code reads. Add a non-TTY smoke check for prompt-capable
  CLIs that may run under services, pipes, or captured stdin.
- Makefile side-effect ordering for install, uninstall, enable, disable, and
  teardown targets under parallel make.
- Privilege wrapper parity: Make targets and helper commands should use the
  same root-or-sudo dispatch as the scripts they wrap, so documented root paths
  still work on minimal systems where `sudo` is absent.
- Command lifecycle boundaries: narrow lint, validate, or exec subcommands
  should use the repository's existing Workspace wrapper boundary when one
  exists instead of bypassing it with raw Docker or shell orchestration.
  Startup, teardown, and environment forwarding should stay where the wrapper
  contract already defines them.
- Partial compatibility shims should resolve optional fallback executables only
  when an unhandled command actually delegates to them. Test both a handled
  command with the fallback absent and an unhandled command's clear failure or
  delegation path.
- Wrapper-path regression fidelity: when a change lands in a Workspace wrapper,
  generated service script, or similar user-facing command boundary, tests
  should keep that wrapper real and fake only the external side-effect binaries
  at the edge. If project-local discovery depends on `workspace.yml`, require a
  minimal fixture file so the test exercises the real override path instead of
  a synthetic no-project context.
- Nested wrapper executable parity: when a top-level command exports its own
  executable path for child helpers or generated service scripts, trace nested
  calls for plain tool-name fallbacks that can resolve a different binary from
  `PATH`. Add a regression that proves nested service or restart paths reuse the
  same executable path as the entrypoint.
- Exit-status propagation: nested Workspace, Docker, provider-CLI, and release
  helper commands that prove readiness must either use passthrough execution or
  explicitly return the child command status. Include a negative-path check for
  missing credentials or failing external CLIs when those checks gate release or
  CI readiness.
- `runpy` dispatcher parity: when a wrapper executes a Python script with
  `runpy.run_path`, restore direct-script sibling-import behavior by prepending
  the absolute script directory to `sys.path`. Require a subprocess regression
  from outside the repository.
- Subprocess lifecycle: when command runners start new sessions, process
  groups, or nested child commands, verify timeout, `SIGTERM`,
  `KeyboardInterrupt`, parent exit, and outer watchdog paths reap every
  descendant that can hold locks, temp files, ports, or other exclusive
  resources.
- Runtime/install parity for wrapped CLIs: when runtime code adds environment
  shims, cache-bypass variables, alternate binary paths, or wrapper functions
  around a third-party CLI, trace every installer, prerequisite, Makefile, and
  documented validation path for plain invocations of the same tool so
  `make install`, prereq checks, and operator smoke tests do not keep the old
  execution assumptions. Parsed CLI output should be checked against the exact
  supported output shapes, not only a hand-written or stale mock format.
- Lifecycle env parity: if a wrapper command forwards config through exported
  environment variables, inspect direct installer, dependency, and required-
  service paths for bypasses of the same variables. Add one regression for the
  user-facing wrapper path and one for the direct lifecycle path that starts the
  same service.
- Shell check-command fall-through: if a freshness, readiness, or stale-check
  loop ends with a `test`, `[` condition, or `&&` list, ensure the non-stale
  path exits explicitly with `exit 0` so a false final test does not turn a
  successful check into a failure.
- Subcommand contract clarity: lint or validate commands should not implicitly
  start services when the documented contract is to `exec` against an
  already-running service; keep lifecycle setup separate unless the repo
  explicitly documents auto-start behavior.
- Recovery and reauthentication commands that replace complete preferences or
  do not persist flags must reconstruct every current non-default setting or
  use a partial-update command. Test a configured-state path, and reserve reset
  semantics for explicit destructive intent.
- Idempotent install, uninstall, cleanup, and recovery behavior that preserves
  user data unless explicit destructive cleanup is requested. For installers
  with shared canonical payloads and per-tool fanout links, verify partial
  uninstalls distinguish selected links, legacy direct installs, ownership
  markers, and still-referenced shared payloads; dry-run cleanup output should
  match apply-mode destructive effects. Copy-mode promotion should be atomic
  enough that a failed copy leaves the previous canonical payload intact, and
  chained fanout links should point through the intended canonical layer.
- Host portability across macOS/BSD and Linux for commands used by operators
  and tests. Test helpers must invoke the required interpreter explicitly and
  avoid login shells unless profile loading is part of the contract; shadow
  the wrong shell in regressions when that makes interpreter drift fail
  deterministically.
- Failure summaries: when scripts tail stderr for context, also extract and
  prefer the most recent actionable error lines (for example Homebrew `Error:`
  blocks) so later cleanup warnings do not mask the real root cause; add a
  regression test for this classification behavior.
- Clear failure output, actionable remediation commands, and validation hooks.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag runtime, security, config, and documentation impacts as overlap risks
  unless they are directly inside the assigned tooling scope.
- Prefer findings that would break local operator workflows or CI execution.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed behavior,
- evidence from the diff or current file,
- proposed remediation,
- narrow validation command,
- possible overlap with another reviewer area.
