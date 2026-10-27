---
name: code-quality-remediation
description: Review a codebase for performance, duplication, dead code, leftover artifacts, file/module organization, and stack-specific standards, then report safe, concrete cleanup recommendations. Use when the user wants a non-breaking quality review focused on elegance, maintainability, idiomatic library usage, and safer structure; do not change code unless the user explicitly asks for remediation.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Code Quality Remediation

Use this skill for cleanup-oriented engineering review work: identify optimization opportunities, duplication, stale code, weak module boundaries, poor file organization, and non-idiomatic stack usage, then report the safest high-value improvements without changing code by default.

## When to use

- The user asks to refactor, optimize, clean up, simplify, deduplicate, or modernize code.
- The repo has obvious dead code, leftover experiments, duplicate helpers, inconsistent patterns, or oversized files.
- The user wants the project to better match language/framework best practices.
- The task is primarily about maintainability, clarity, or structure, not shipping a new feature.
- The cleanup is preparing a repository for public publication; in that case, pair this skill with `$repo-publication-sanitizer`.

Do not use this skill for a findings-only bug hunt. If the main request is defect review, use a bug-focused review skill instead.

## Review priorities

Prioritize these categories in order:

1. Remove duplication and overlapping abstractions.
2. Remove unused, stale, or misleading code left behind by prior changes.
3. Improve file/module organization, ownership boundaries, and naming clarity.
4. Align implementation with the idioms of the current language, framework, and major libraries.
5. Improve performance where the code is clearly wasteful or structurally inefficient.
6. Identify accidental publication of local or personal data and route that work through `$repo-publication-sanitizer`.
7. Flag incidental bugs discovered during the review, but do not let bug finding take over the task unless the user redirects.

## Workflow

### 1. Establish local standards before changing code

- Read `AGENTS.md` and any repo-local contribution docs first.
- Detect the stack from repository evidence: package managers, build files, lint config, formatter config, framework files, and test setup.
- Treat existing linters, formatters, and project conventions as the first source of truth.
- When project conventions are weak or inconsistent, fall back to widely accepted language/framework guidance and primary library documentation.

### 2. Build a remediation map

Inspect the target scope and identify:

- duplicate logic, copy-pasted branches, and parallel helpers,
- unused exports, functions, types, variables, files, assets, or flags,
- commented-out code and obsolete compatibility paths,
- bloated files that should be split by responsibility,
- weak boundaries between UI, domain, data access, and infrastructure layers,
- non-idiomatic library usage,
- obvious performance waste such as repeated expensive work, redundant I/O, over-fetching, unnecessary allocations, or avoidable rerenders.
- hidden semantic coupling where null, empty, omitted, default, all, auto, or
  disabled values are expanded in one layer and later treated as concrete state,
- developer-local overrides or machine-specific example values that should stay
  empty, generated, or local-only instead of being committed as shared repo
  defaults,
- user-facing labels used as internal identity keys in maps, caches, joins,
  filenames, charts, or route lookups,
- duplicated min/max/enum limits across schema, validation, UI, docs, helpers,
  installers, and runtime code,
- background workers or status paths that duplicate logic instead of sharing
  existing single-flight, job-state, or side-effect boundary helpers.
- review or workflow guidance that duplicates nearby rules instead of
  strengthening an existing higher-leverage check in place.

Prefer high-confidence cleanup over speculative rewrites.

### 3. Prefer the smallest safe recommendation

- Preserve behavior in every recommendation unless the user asked for broader redesign.
- Prefer low-regression recommendations over ambitious rewrites.
- Prefer extracting shared logic over introducing a new abstraction layer too early.
- Prefer deleting unused code instead of keeping "maybe useful later" leftovers, but only when confidence is high.
- Split large files by coherent responsibility, not by arbitrary line count.
- Keep public APIs stable unless there is a clear payoff and the blast radius is manageable.
- If a piece of code looks unused but the evidence is incomplete, report it as a candidate instead of treating it as safe to remove.

### 4. Apply stack-aware standards

Adapt the review to the repo you are in:

- For typed languages, tighten type boundaries and remove unused types or weak escape hatches.
- For dynamic languages, reduce hidden coupling and make interfaces explicit.
- For UI code, improve state ownership, rendering boundaries, component composition, and accessibility-safe structure.
- For backend/services, tighten data flow, validation, error handling, and layering.
- For scripts/automation, simplify flow control, make shell/file handling safe, and remove fragile assumptions.
- For framework-heavy code, prefer the framework's recommended patterns over custom architecture unless the repo already has a better established pattern.

For Python repos, also look for:

- config drift across dataclasses, parsers, validators, example config files, docs, and install/bootstrap scripts,
- drift between validation rules and privileged/helper scripts that enforce
  stricter runtime limits,
- oversized modules that mix CLI parsing, runtime orchestration, rendering, and persistence concerns,
- hidden import-time side effects or optional imports that should be isolated behind runtime boundaries,
- weak typing boundaries that force `Any`-like escape hatches through large parts of the codebase,
- packaging drift between `pyproject.toml`, package data, optional extras, and actual runtime needs,
- duplicate HTML/string-building patterns in server-rendered code that should share helpers or page-family boundaries.

For public repositories, also call out cleanup targets that are not code style:

- copied local terminal output,
- hard-coded home directories or machine paths,
- local hostnames, IPs, usernames, device IDs, or account names,
- generated examples that expose the developer's actual environment.

Use `$repo-publication-sanitizer` for the detailed scan and remediation policy.

### 5. Assess regression risk for every recommendation

For each recommendation:

- state the expected regression risk,
- identify what tests, lint, typecheck, or build tasks should be run before and after applying it,
- call out affected interfaces, files, or runtime paths,
- distinguish high-confidence removals from items that need manual confirmation.

If no automated checks exist, do a targeted static review and state the validation gap explicitly.

## Decision rules

- Default to reporting recommendations only. Do not make cleanup changes unless the user explicitly asks for remediation.
- Keep refactors incremental when the codebase is fragile.
- Avoid speculative micro-optimizations without evidence from code structure, profiles, or obvious repeated work.
- Do not rewrite large subsystems just to satisfy a style preference.
- Do not replace established project patterns unless the existing pattern is actively harming maintainability.
- When multiple valid organizations exist, choose the one that best matches the surrounding codebase.
- Prefer findings and recommendations that are unlikely to introduce regressions.

## Output requirements

When asked to review only:

- list findings by priority,
- explain why the current structure is costly,
- recommend concrete refactors with file-level specificity,
- call out any validation gaps.

When explicitly asked to remediate:

- apply changes incrementally,
- validate after each meaningful step,
- avoid broad rewrites without tests or clear rollback paths,
- summarize structural improvements made,
- mention important deletions, consolidations, and file moves,
- report validation performed,
- call out any risky leftovers that should be handled in a later pass.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
