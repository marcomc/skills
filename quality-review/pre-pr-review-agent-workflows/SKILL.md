---
name: pre-pr-review-agent-workflows
description: Reviews agent instructions, Codex skills, AGENTS.md files, learning hooks, prompt workflows, and automation guidance before PR. Use when a pre-PR review area includes `AGENTS.md`, `SKILL.md`, prompt templates, agent-learning promotion, Codex automation instructions, or reusable workflow guidance.
---

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
- Safe separation between read-only, review, remediation, commit, push, PR, and
  release-publication flows.
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
