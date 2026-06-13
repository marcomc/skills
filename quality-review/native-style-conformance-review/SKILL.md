---
name: native-style-conformance-review
description: Reviews a branch, diff, or changed files for conformance with the surrounding project's existing coding, testing, documentation, and tooling style. Use when the user asks whether new code looks like it was written by the same maintainer, avoids unfamiliar components, follows native conventions, or is stylistically defensible before PR review.
---

# Native Style Conformance Review

Use this as a report-only reviewer when the main question is whether a change
fits the host project. This is not a general best-practices review and not a
modernization pass.

## Quick Start

Example invocation:

```text
Use $native-style-conformance-review on this branch against origin/main.
Check only whether the changed code follows the project's existing style and
APIs. Do not edit files.
```

## Workflow

1. Read applicable project instructions first, including `AGENTS.md`,
   contribution docs, test docs, style docs, and local README guidance.
2. Resolve the requested scope:
   - branch versus base branch,
   - explicit commit range,
   - staged or unstaged changes,
   - selected files or pathspecs.
3. Inventory the changed files and identify the nearest native prior art:
   similar commands, classes, handlers, helpers, shell scripts, tests, fixtures,
   docs, or config files already in the project.
4. Compare the new code against that prior art. Prefer concrete project-local
   evidence over generic language or framework preferences.
5. Report only actionable deviations that would make the change hard to defend
   as native to the project.
6. If no issues are found, say that clearly and list any residual checks that
   were not run.

## Review Focus

- File placement, naming, namespace, module boundaries, and command wiring.
- Constructor, dependency access, helper usage, data structures, and error
  handling style.
- CLI argument and option style, output format, exit behavior, and messages.
- Config loading, defaults, override precedence, serialization, and generated
  file conventions.
- Test style, fixture shape, assertion granularity, setup and teardown patterns,
  and whether tests avoid touching real user or machine state.
- Shell, Makefile, Docker, CI, and installer changes that should use existing
  wrappers or lifecycle boundaries.
- Documentation tone, examples, heading structure, and cheatsheet or README
  placement.

## Guardrails

- Do not recommend replacing the project's established style with a preferred
  modern style.
- Do not flag legacy project patterns as findings unless the new change applies
  them inconsistently or breaks behavior.
- Do not introduce new frameworks, dependencies, linters, formatters, or broad
  abstractions just to satisfy style concerns.
- Do not expand into architecture, security, performance, or deprecation review
  unless the style mismatch directly creates that risk.
- Treat runtime deprecation warnings from an unsupported local interpreter as
  out of scope unless the changed code caused them.
- Default to read-only review. Edit files only if the user explicitly asks for
  remediation.

## Finding Contract

Lead with findings, ordered by severity. For each finding include:

- changed file and line reference,
- native project pattern used as evidence,
- why the new code deviates,
- smallest style-aligned fix,
- validation command or check if relevant.

Use this severity scale:

- `blocker`: likely to be rejected, break behavior, or violate project
  contracts.
- `strong recommendation`: stylistic or integration mismatch that should be
  fixed before PR.
- `cleanup`: defensible but less native than nearby code.
- `validation gap`: style-sensitive behavior lacks the same kind of proof used
  elsewhere in the project.

Also include an `Acceptable Deviations` section when the change intentionally
uses a slightly different shape and the reason is defensible within the
project's existing constraints.
