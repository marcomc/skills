---
name: pre-pr-review-cli-tooling
description: Reviews CLI, shell, Makefile, helper script, installer, uninstall, and local developer-tooling diffs before PR. Use when a pre-PR review area includes shell scripts, Make targets, command wrappers, argument pass-through, install or teardown commands, local automation, or cross-platform host tooling.
---

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
- Installer subprocess isolation: when wrappers call external installers or
  package managers, verify staged execution redirects `HOME`, XDG-style config
  roots, tool-specific config homes, caches, and generated side effects away
  from the real user environment before promoting results.
- Captured helper output: command substitutions and parsed stdout must contain
  only machine-readable return data. Prompts, progress text, menus, and
  operator hints belong on stderr or a terminal, with an interactive negative
  test when stdout is later tokenized as packages, flags, or commands.
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
- Exit-status propagation: nested Workspace, Docker, provider-CLI, and release
  helper commands that prove readiness must either use passthrough execution or
  explicitly return the child command status. Include a negative-path check for
  missing credentials or failing external CLIs when those checks gate release or
  CI readiness.
- Runtime/install parity for wrapped CLIs: when runtime code adds environment
  shims, cache-bypass variables, alternate binary paths, or wrapper functions
  around a third-party CLI, trace every installer, prerequisite, Makefile, and
  documented validation path for plain invocations of the same tool so
  `make install`, prereq checks, and operator smoke tests do not keep the old
  execution assumptions. Parsed CLI output should be checked against the exact
  supported output shapes, not only a hand-written or stale mock format.
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
- Host portability across macOS/BSD and Linux for commands used by operators.
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
