---
name: pre-pr-review-agent-workflows
description: Reviews agent instructions, Codex skills, AGENTS.md files, learning hooks, prompt workflows, and automation guidance before PR. Use when a pre-PR review area includes `AGENTS.md`, `SKILL.md`, prompt templates, agent-learning promotion, Codex automation instructions, or reusable workflow guidance.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Pre-PR Review Agent Workflows

Use this as a report-only reviewer profile for AI-agent instruction and skill
workflow slices of a broader pre-PR remediation. Do not edit files.

## Review Focus

- Instruction drift between global rules, project `AGENTS.md`, reusable skills,
  prompt templates, and automation guidance.
- Over-broad rules that should be narrowed to the smallest reusable skill.
- Duplicate, contradictory, stale, or append-only guidance that lowers signal.
- Missing learning hooks on review-oriented skills, or hooks added to skills
  that are not review workflows.
- When an automation launches an isolated reviewer, check that required skills
  and role-local checks are preflighted in the effective profile before the
  model turn. Keep coordinator-owned checks and no-model probes distinct from
  the independent review and its actual result.
- When role admission depends on sandbox or tool isolation, verify allowed and
  denied OS access and the effective tool inventory under the actual launcher,
  environment and profile. Bind the probe to the same configuration used by
  the worker thread; a projected policy alone does not establish access.
- For persisted session handoff, check exclusive writer release before another
  runtime resumes the session. Distinguish stored history and an idle turn from
  writer ownership; retain the original deadline and send evidence on conflict.
- When projecting live role status from a process observation, bind it to the
  owning connection and exact attempt, session and turn; keep missing evidence
  unknown. Reconcile conflicting app views against the owner runtime and
  original command receipt before projecting a state.
- For managed owner admission, retain durable identity and authority bindings
  while refreshing expiring readiness at each claim and activation. After a
  guidance change, verify the scheduled selector and preserve owner generation,
  session and run history when updating its supported reference.
- When a task requires a managed worker route, retain the task and technical
  hold if it cannot be admitted; do not represent an internal delegate as that
  worker. Use another route only with its own applicable authorization and
  report its actual identity and lineage.
- Safe separation between read-only, review, remediation, commit, push, PR, and
  release-publication flows.
- When same-authority user workflow instructions appear to conflict, check
  original authenticated items, timestamps and scope rather than reconstructed
  display order. Preserve the general instruction, any explicit narrower
  exception and unrelated holds; do not infer missing authority or override
  higher-priority policy.
- Before dispatch, compare intended behavior with normative policy and the
  approved file scope; if a policy change is needed, bind the revised scope
  and authorization before sending work.
- For role preparation, verify the existing canonical working directory and
  selected executable's actual configuration with the execution parameters for
  each role. Keep config-only probes distinct from entitlement and execution
  evidence; record the created session identity before subsequent effects.
- When a worker must use exact review bytes, provide a private machine-readable
  file in its permitted scope and verify its digest and effective-profile access
  before the model turn; do not rely on transcription of rendered diffs.
- Executable commands embedded in skills, prompts, and automation guidance must
  satisfy the current CLI contract, including required companion flags for
  strict validation modes.
- Markdown lint, frontmatter description quality, and skill trigger precision.

## Assignment Rules

- Review only the assigned pathspecs, commits, or diff range.
- Flag code, CI, docs, and security impacts as overlap risks unless the finding
  is about agent workflow guidance itself.
- Prefer findings that prevent future agent mistakes over style commentary.

## Report Contract

Return findings only when they are actionable.

For each finding include:

- severity: blocker, strong recommendation, cleanup, or validation gap,
- file reference and changed workflow behavior,
- evidence from the diff or current instruction text,
- proposed remediation,
- narrow validation command or manual consistency check,
- possible overlap with another reviewer area.
