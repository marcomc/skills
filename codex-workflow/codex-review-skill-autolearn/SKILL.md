---
name: codex-review-skill-autolearn
description: Learn from completed GitHub Codex review remediations by distilling actionable findings into compact generic rules, then directly refine the relevant local review and remediation skills without adding redundant guidance.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Codex Review Skill Autolearn

Use this skill once after an integrated local or remote review run completes. Its
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

Prefer an executable regression or deterministic check in the owning project,
then the smallest relevant specialist profile. Use `$review-coordinator` only
for orchestration, routing or evidence-contract defects. Entry adapters should
not accumulate domain checklists. Never update every skill for one lesson.

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

For recurring PR drift, scope expansion, or review-loop termination errors,
route the prevention rule to `$review-coordinator` and the detection rule to
`codex-pr-review-remediation-loop` or the PR-description entrypoint as
appropriate. Keep the contract finite: objective, non-goals, acceptance cases,
and actionable-finding criteria must be explicit before a new review starts.

## Workflow

### 1. Collect the learning input

Gather the integrated terminal remediation context once. During intermediate
batches, record candidate lessons in the coordinator ledger. Reuse that compact
record at exit rather than rereading the full chat or repeatedly updating and
reinstalling the same skills. Keep the active policy revision stable. An urgent policy repair requires an
explicit run rebaseline and reconciliation of affected proofs; record the reason
so the terminal handoff does not repeat it. Otherwise apply changes to the next run.

Gather:

- the actionable Codex findings,
- the fixes that were applied,
- the tests or probes that proved the fixes,
- any sibling regressions found during remediation,
- the local `READY`/`NEEDS_WORK`/`BLOCKED` outcome and separate remote status.

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
  investigate routing, missing evidence, or non-application instead of adding
  another version of the rule;
- `weak`: the rule exists but is too vague, too narrow, or in the wrong place;
- `missing`: no suitable rule exists yet.

Prefer:

- tightening wording,
- merging overlapping bullets,
- moving a rule to a more effective section,

over:

- adding a brand-new paragraph or checklist item.

### 4. Improve prevention with a compactness bias

When changes are needed:

- first prefer an executable regression/check for a repeatable failure;
- use the coordinator calibration reference to distinguish actual escapes from
  speculative added coverage and retain missing usage metrics as unknown;

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

### 5. Apply source-first skill updates

Before editing, resolve whether each active target is the owning source, a
symlink, or an installed copy. When an owning repository exists:

1. edit and validate the owning source;
2. refresh the canonical installation through its documented installer;
3. refresh downstream mirrors;
4. verify source/install/fanout parity.

Edit an active `SKILL.md` directly only when it is the canonical source. Treat
installed-only changes as incomplete and non-durable. Do not stop at a prose
proposal.

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
- confirmation that owning sources and installed/fanout copies match.

If no direct skill changes were warranted, say so explicitly and explain why.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When the integrated run produces a reusable lesson, run `$record-agent-learning`
once with this skill as `--source-skill`, or reference its existing capture.
Tell the coordinator capture is complete. Skip clean/no-op reviews and trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
