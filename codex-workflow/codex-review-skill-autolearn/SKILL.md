---
name: codex-review-skill-autolearn
description: Learn from completed GitHub Codex review remediations by distilling actionable findings into compact generic rules, then directly refine the relevant local review and remediation skills without adding redundant guidance.
---

# Codex Review Skill Autolearn

Use this skill after a `codex-pr-review-remediation-loop` pass completes. Its
job is to turn GitHub Codex findings into tighter local review skills so more
issues are caught before the next PR is sent to GitHub.

## Goal

Improve the local skill system by:

- extracting the generic failure classes behind the latest Codex findings,
- deciding which classes are general enough to teach to other skills,
- editing the most relevant skills directly,
- refining existing wording when possible instead of appending new bulk,
- keeping the skill corpus compact, non-redundant, and higher-signal over time.

## Default targets

Unless the repository or user requests otherwise, review these skills in this
order of leverage:

1. `pre-pr-review-gate`
2. `max-findings-review`
3. `diff-regression-check-planner`
4. `branch-qa-remediation`
5. `max-findings-relentless`
6. the smallest relevant specialized reviewer profile:
   `pre-pr-review-frontend`, `pre-pr-review-backend-services`,
   `pre-pr-review-infra-runtime`, `pre-pr-review-security-boundaries`,
   `pre-pr-review-tests-validation`, `pre-pr-review-docs-release`,
   `pre-pr-review-config-data-flow`, `pre-pr-review-cli-tooling`,
   `pre-pr-review-ci-actions`, or `pre-pr-review-agent-workflows`
7. `stack-best-practices-review`
8. `security-best-practices`
9. `repo-publication-sanitizer`
10. `code-quality-remediation`
11. `codex-pr-review-remediation-loop`

Do not edit every skill by default. Touch only the smallest set that materially
improves prevention for the learned class.

## Specialized Target Routing

Prefer the specialized reviewer profile when a lesson is domain-specific:

- UI, browser, templates, or client state:
  `pre-pr-review-frontend`.
- APIs, workers, persistence, validation, or service integrations:
  `pre-pr-review-backend-services`.
- Deploy, Docker, Workspace, Jenkins, service lifecycle, or packages:
  `pre-pr-review-infra-runtime`.
- Auth, secrets, privileged helpers, telemetry, permission prompts, or
  side-effect boundaries: `pre-pr-review-security-boundaries`.
- Tests, fixtures, smoke checks, CI signals, or coverage gaps:
  `pre-pr-review-tests-validation`.
- README, changelog, release notes, examples, or operator docs:
  `pre-pr-review-docs-release`.
- Config, defaults, schemas, generated artifacts, identifiers, or URL/path
  handling: `pre-pr-review-config-data-flow`.
- Shell, Makefile, installers, wrappers, argument pass-through, or local
  automation: `pre-pr-review-cli-tooling`.
- GitHub Actions workflows, matrices, caches, artifacts, or check logs:
  `pre-pr-review-ci-actions`.
- `AGENTS.md`, `SKILL.md`, prompt templates, learning hooks, or Codex
  automation guidance: `pre-pr-review-agent-workflows`.

Use `pre-pr-remediation-worker` only for lessons about edit-capable sub-agent
coordination, scope containment, or worker reporting. Do not put report-only
review heuristics there.

## Workflow

### 1. Collect the learning input

Gather the completed remediation loop context:

- the actionable Codex findings,
- the fixes that were applied,
- the tests or probes that proved the fixes,
- any sibling regressions found during remediation,
- whether the final pass was clean, summary-only, or ended with accepted gaps.

If the latest loop had no actionable findings, the skill may still conclude
that no changes are needed and exit cleanly.

### 2. Distill findings into generic classes

For each actionable finding:

- restate the issue as a reusable failure class, not a line-specific complaint;
- identify the contract that was violated;
- identify the narrowest pre-PR check that would have caught it;
- note whether the lesson belongs to correctness review, regression planning,
  security review, maintainability review, or remediation workflow.

Examples of transferable classes:

- negative-path semantics drifting from the intended user-visible status,
- tokenizing user input versus accidentally executing it,
- assuming only one valid input or content topology,
- wrapper-source changes that require rendered-artifact validation,
- runtime checks that only prove the happy path and miss malformed or missing
  input behavior.

### 3. Check whether the corpus already knows this

Before editing anything, inspect the current target skills and classify each
learned class as one of:

- `covered`: the rule already exists with adequate precision and emphasis;
- `weak`: the rule exists but is too vague, too narrow, or in the wrong place;
- `missing`: no suitable rule exists yet.

Prefer:

- tightening wording,
- merging overlapping bullets,
- moving a rule to a more effective section,

over:

- adding a brand-new paragraph or checklist item.

### 4. Edit in place with a compactness bias

When changes are needed:

- modify the smallest number of skills that will improve future prevention;
- refine existing bullets before adding new ones;
- replace weaker wording with stronger wording instead of duplicating both;
- avoid historical narration, examples tied to one repository, or append-only
  "lessons learned" logs inside the skill files;
- keep each edit generic enough to survive future repos and diffs.

If a finding teaches the same lesson to multiple skills, specialize each edit:

- review skills should gain sharper finding heuristics,
- regression planners should gain sharper validation requirements,
- remediation loops should gain sharper post-fix verification or feedback rules,
- orchestrators should gain sharper sequencing and gate conditions.

### 5. Apply direct skill updates

Edit the target `SKILL.md` files directly. Do not stop at a prose proposal.

When a finding is only locally specific and not clearly reusable, leave the
skills unchanged rather than forcing a generic rule.

### 6. Prevent uncontrolled growth

Before finalizing, review the modified skills and explicitly remove:

- duplicated bullets,
- overlapping examples that say the same thing twice,
- generic reminders that add no new decision signal,
- wording that can be folded into a nearby stronger rule.

The success criterion is not "more text." It is "higher prevention density per
line of guidance."

### 7. Validate the modified corpus

Run `markdownlint` on every changed `SKILL.md` using the user-standard config.

If a new edit made another rule obsolete or contradictory, fix that before
returning.

## Output requirements

Return:

- the distilled failure classes,
- which skills were edited,
- whether each edit was a `refine`, `merge`, `replace`, or `add`,
- any classes that were intentionally left unchanged because the corpus already
  covered them,
- confirmation that `markdownlint` passed on all changed skill files.

If no direct skill changes were warranted, say so explicitly and explain why.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
