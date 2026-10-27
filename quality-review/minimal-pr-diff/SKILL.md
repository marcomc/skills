---
name: minimal-pr-diff
description: Reduce an implementation branch to the smallest reviewable diff that still meets its feature contract and project conventions. Use when auditing or simplifying a branch before review or commit.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Minimal PR Diff

Help make a feature branch easy to review by removing only changes proven unnecessary. Preserve behavior required by the feature, project conventions, and explicit user decisions. A smaller diff is not better if it weakens required behavior or coverage.

## Establish scope and evidence

1. Read the applicable `AGENTS.md`, contributor guidance, and the user's constraints. Identify the requested feature and its acceptance conditions.
2. Inspect `git status`, staged and unstaged diffs separately, and the branch diff against its actual target base. Preserve existing staged work and unrelated edits. Do not stage, commit, push, or modify remote review state without separate authorization.
3. If available and relevant, review maintainer comments on this branch and comparable project changes. Treat comments as evidence of project expectations; distinguish explicit requirements from preferences and context-specific remarks.
4. Trace each changed file and meaningful code block to a feature requirement, compatibility need, regression risk, or project convention. Look for repeated constants/data sources, duplicated logic, defensive code, tests, and changes to existing code that may be avoidable.

## Decide what stays

For each candidate change, record its purpose, evidence, and disposition: required, useful but optional, or removable. Prefer removing optional scope when the user wants a minimal PR. Keep changes that establish required behavior, protect an evidenced boundary, or test a necessary regression. Do not remove safeguards or tests merely to lower line count.

Prefer the smallest local change that follows established patterns. Reuse an existing source of truth when doing so avoids repeated hard-coded values without adding broad abstractions. Avoid renaming, reformatting, type tightening, cleanup, or architectural reshaping of original code unless the feature cannot work correctly without it. Put new behavior in the narrowest existing module or owner that matches repository conventions; do not add public methods or abstractions solely for neatness.

When uncertainty depends on a design choice, explain the alternatives and trade-offs, complete independent inspection, and ask only about the unresolved decision. A request to assess or explain is not permission to edit. When edits are authorized, make the focused reductions while preserving the user's staged/unstaged boundary; never stage automatically.

## Validate and report

After edits, inspect the final staged and unstaged diffs independently and verify that unrelated work and staging are preserved. Run the project's relevant validation for changed behavior; do not run broad or expensive checks without a reason. Report:

- what was removed or retained and why, tied to concrete evidence;
- files and change areas still needed for the feature;
- validation run and its result;
- any remaining optional scope or unresolved uncertainty.

Do not claim the branch is ready to commit unless the current diff, relevant checks, and requested review criteria have actually been verified.
