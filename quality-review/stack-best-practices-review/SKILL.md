---
name: stack-best-practices-review
description: Review code against the best practices of the detected language, framework, libraries, and file organization patterns using repository evidence first and primary documentation when a rule is version-sensitive. Use when the user wants a review focused on idiomatic stack usage, maintainability, architecture fit, and non-breaking modernization; report findings only unless remediation is explicitly requested.
---

# Stack Best Practices Review

Use this skill to audit code against the conventions of the stack already in use. The goal is to catch non-idiomatic or high-friction patterns before a PR is opened, especially when the code technically works but fights the language, framework, libraries, or project structure.

## When to use

- The user asks for a standards review, idiomatic review, framework review, or library best-practices review.
- The diff introduces new patterns that may not fit the existing stack.
- The repo mixes inconsistent approaches to the same problem.
- The user wants non-breaking modernization guidance without turning the task into a feature rewrite.

Do not use this as the main bug/regression review. Pair it with a correctness-focused review skill.

## Workflow

### 1. Detect the stack from repository evidence

- Read `AGENTS.md` and repository docs first.
- Identify the languages, frameworks, runtimes, and major libraries in scope.
- Use concrete evidence: lockfiles, manifests, build files, lint config, formatter config, framework config, test config, and changed imports.
- Infer versions when possible, because best practices are often version-sensitive.

### 2. Establish the local standard hierarchy

Use this order of precedence:

1. Repo-local rules and established project conventions.
2. Linter, formatter, typechecker, and framework config already present in the repo.
3. Widely accepted language/framework/library guidance.
4. Primary documentation when a claim depends on framework or library version behavior.

If local conventions conflict with generic advice, prefer the local convention unless it is clearly causing maintainability or correctness problems.

### 3. Select the relevant best-practice layers

Review the code against the layers that actually apply:

- language idioms and error-handling style,
- framework lifecycle and data-flow patterns,
- library API usage and deprecated surfaces,
- test structure and test boundaries,
- module, folder, and ownership boundaries,
- naming and public API clarity,
- build and configuration organization where it affects the code path.
- state semantics that the stack tends to encode with null/empty/omitted values,
  defaults, feature flags, or form checkboxes.

For Python repositories, explicitly include:

- `pyproject.toml` packaging metadata, optional dependencies, and console scripts,
- `src/` layout and import boundaries,
- `pytest`, `ruff`, `mypy`, and `uv` conventions already enforced by the repo,
- config schema/load/write/validate symmetry,
- example-config, installer, bootstrap, and docs synchronization,
- server-rendered page/action separation when the app builds HTML in Python.

### 4. Review the changed code and its neighbors

Inspect the diff plus nearby files that define the surrounding pattern. Look for:

- non-idiomatic language usage,
- framework misuse or outdated patterns,
- library calls that bypass recommended abstractions,
- code placed in the wrong layer or file,
- oversized files that mix unrelated responsibilities,
- duplicated patterns that should share a single standard approach,
- anti-patterns that create maintenance drag even if they are not immediate bugs.
- negative-path behavior that does not match the stack's normal contract, such
  as expected misses surfacing as generic internal failures,
- wrapper or shell parsing choices that interpret user input instead of
  tokenizing it as arguments or config data,
- helpers, validators, or serving paths that only support one content topology
  even though the feature should work for multiple valid shapes,
- display labels used as identities where stable IDs are available,
- async/background work that bypasses the framework's existing job, lock, or
  single-flight pattern,
- status or redirect messages that are produced before checking whether the
  requested work actually started,
- config/schema/helper/UI limits that are duplicated instead of sharing a
  single standard source of truth.

Do not report style-only nits unless they point to a bigger maintenance or readability problem.

### 5. Verify version-sensitive claims

- When a finding depends on a specific framework or library rule that may have changed across versions, verify it against primary documentation if available.
- If you cannot verify it, state that the point is an inference and lower the confidence.
- Do not present a preference as a rule.

### 6. Keep recommendations low-regression

- Prefer recommendations that fit the current architecture.
- Avoid suggesting migrations just because a newer API exists.
- Do not force a new folder structure unless the existing one is materially harming navigation or ownership.
- Favor the smallest idiomatic change that reduces long-term friction.

## Python-specific review points

When the detected stack includes Python, check these areas deliberately:

1. Keep packaging behavior real:
   - imports introduced by the diff must be satisfied by base or optional dependencies,
   - new asset files must be shipped by package-data rules,
   - console scripts and `python -m` execution should still exercise the intended entrypoints.
2. Keep config changes synchronized:
   - new settings should be reflected in config models, load/write/validate paths, example configs, installer/bootstrap flows, tests, and docs.
3. Respect the repo's quality gate:
   - prefer the repository's canonical gate command over ad hoc Python commands when judging readiness,
   - use the lint/type/test config already present as the operational standard.
4. Prefer clear module boundaries:
   - keep CLI parsing, web actions, page rendering, persistence, and shell/system helpers separated when the repo already organizes them that way.
5. Be careful with appliance-style Python services:
   - if repo instructions require live validation for certain surfaces, treat that as part of the review result, not an optional note.
6. Preserve semantic defaults:
   - form handlers and config writers should keep empty/all/default/auto state as semantic state rather than serializing the current concrete expansion.

## Output requirements

Return:

- the detected stack and evidence used,
- the local conventions or config treated as authoritative,
- findings grouped by priority,
- why each finding is non-idiomatic or costly,
- the safer or more idiomatic direction,
- expected regression risk and what to validate if the change is later applied.

Default to findings only. Do not change code unless the user explicitly asks for remediation.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
