---
name: pr-description-markdown
description: Generate a Markdown PR description snippet from git diff/log for any repository. Use when the user asks for a PR description or a markdown snippet summarizing branch changes against a base branch.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# PR Description (Markdown)

Generate a Markdown PR description snippet by comparing the current branch to a base branch (default: `main`, fallback `master`).

## Workflow

1. Confirm repository is a git repo and determine base branch (default `main`).
2. Generate a Markdown snippet with Summary, Changes, Testing, Notes, and Commits.
3. Prefer short, actionable bullets in Summary and Testing.
4. Include a compact review contract in Notes: objective, in-scope behavior,
   non-goals/unsupported forms, finite acceptance cases, and what qualifies as
   an actionable finding. Keep the contract specific to the diff and bounded.

## Commands

Run the bundled script:

```bash
~/.Codex/skills/pr-description-markdown/scripts/pr_description.py --base main
```

Optional:

- `--head HEAD` (default)
- `--max-files 50`

## Output Rules

- Provide a Markdown snippet only.
- Keep Summary and Testing short.
- Include file list (name-status) and commit list.
- Include the review contract so remote reviewers can distinguish defects from
  intentionally unsupported scope.

## Notes

If the repo uses a non-standard base branch, pass it explicitly via `--base`.
