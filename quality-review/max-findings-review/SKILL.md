---
name: max-findings-review
description: Review a requested PR or diff for evidence-backed bugs, regressions and operational risks across stacks. Report candidates and confirmed findings without editing or opening a remediation loop.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Max Findings Review

Review the supplied diff and relevant dependencies against user intent and
repository instructions. Prioritize observable failures and compatibility over
style. Give each finding a concrete trigger, code evidence and impact; mark an
unverified plausible issue as a candidate requiring proof, not a confirmed defect.

## Composed mode

When `$review-coordinator` supplies an assignment, use its scope, selected lenses,
policy revision and evidence. Review only outstanding coverage and affected
contracts; return findings/evidence to that coordinator. Do not start remediation,
run another gate, delegate again, update skills or capture learning independently.
Existing sufficient integrated review evidence can satisfy this lens.

## Standalone mode

For an explicitly broad review, inspect the complete requested diff and read
[conditional correctness checks](references/checks.md). For a focused request,
load only relevant checks/profiles. Follow reachable dependencies when needed to
establish a failure, without inventing new product requirements or unrelated work.

Use the smallest relevant `pre-pr-review-*` specialist profile for frontend,
backend, config/data flow, CLI, infra/runtime, CI, security, tests, docs or agent
workflows. Profiles provide focus; they do not require separate passes or agents.
Do not edit or delegate unless the user explicitly requests that workflow.

## Output

Return confirmed findings first, ordered by severity (P1-P3), then clearly marked
unverified candidates and optional suggestions. Include file/line, trigger,
impact, evidence and narrow validation/fix direction. If none are found, state
that with the reviewed scope and limitations; absence of findings is not proof
of test execution or a remote clean result. No exact output phrase controls exit.

## Agent Learning Hook

For a standalone review with a real reusable finding, use `$record-agent-learning`
once. In composed mode return candidates to the coordinator's terminal learning
step instead. Skip clean/no-op reviews and one-off trivia.
