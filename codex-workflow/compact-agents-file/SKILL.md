---
name: compact-agents-file
description: Compact and improve project AI-agent instruction files while preserving their behavioral meaning. Use when the user asks to reduce tokens, remove repetition, compress, rewrite, refactor, or improve AGENTS.md, CLAUDE.md, GEMINI.md, .github/copilot-instructions.md, agents/openai.yaml guidance, or similar repository agent instructions without changing the rules' intended result.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Compact Agents File

Compress agent instruction files so future agents spend fewer tokens and still
make the same operational decisions.

## Target Files

Default to the current project root. Detect likely instruction files with:

```bash
rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'GEMINI.md' -g '.github/copilot-instructions.md' -g 'agents/openai.yaml'
```

If more than one file is in scope, compact only the file the user named unless
they asked for a multi-agent pass.

## Workflow

1. Read the target file, nearby project docs, and any global/root instruction
   file it references.
2. Check git status and preserve unrelated user changes.
3. Identify behavior-bearing content:
   commands, validation gates, deploy safety rules, naming conventions, security
   wording, task tracking rules, environment facts, known failure lessons, and
   exact edge-case caveats.
4. Identify low-value content:
   duplicated rules, long rationale, stale status prose, generic project
   marketing, broad explanations already covered by linked docs, and examples
   that do not constrain future behavior.
5. Rewrite as compact contracts with clear headings, short bullets, command
   lists, and reference pointers.
6. Add only improvements that reduce future ambiguity, speed execution, or
   preserve known lessons. Do not add speculative process.
7. Validate edited files with the repo's required doc checks.
8. Report reduction metrics and any intentional semantic changes. If the goal
   was no behavior change, say whether that was preserved.

## Compression Rules

- Preserve decision outcomes, not phrasing.
- Replace repeated prose with one authoritative rule.
- Prefer "contract" bullets over narrative background.
- Keep exact commands when command syntax matters.
- Keep environment distinctions such as dev/prod, local/remote, active/standby,
  or generated/source paths.
- Keep negative rules that prevent known mistakes.
- Move deep detail to references only when a repo doc already exists and is
  trustworthy.
- Delete stale progress summaries, broad project pitches, and generic
  best-practice prose unless they drive agent behavior.
- Do not weaken safety rules to save words.
- Do not convert precise conditions into vague advice.

## Useful Structure

Use this shape unless the existing file strongly suggests another one:

1. Fast start
2. Project facts
3. Core commands
4. Work tracking
5. Safety and deployment rules
6. Authoring contracts
7. Service or domain contracts
8. Validation matrix
9. Known issues
10. References

Keep the first screen highly actionable: where to look, what not to do, and the
minimum validation expectations.

## Improvement Heuristics

Add or tighten rules when they clearly help future execution:

- Canonical wrappers instead of raw low-level commands.
- Targeted validation for common change classes.
- Dirty-state reset guidance before smoke tests.
- Generated-file boundaries.
- Secret-handling and log-leak checks.
- Timeout guidance for known long commands.
- Pointers from compact rules to detailed docs.
- One explicit "do not deploy/publish/delete unless asked" rule when relevant.
- A small command inventory if agents repeatedly rediscover the same commands.

Avoid adding:

- aspirational backlog not tied to agent behavior,
- broad architecture essays,
- complete command manuals when docs already exist,
- duplicate global rules already inherited from a parent instruction file.

## Validation

Run the required checks for edited instruction files. Prefer project rules; if
none are discoverable and the file is Markdown, run:

```bash
markdownlint --config "$HOME/.markdownlint.json" <file>
```

Also run `git diff --check -- <file>` when available.

If the edit touches shell snippets that are intended as scripts, validate the
actual shell files if they were edited; do not invent script validation for
plain documentation examples unless the repo requires it.

## Final Response

Include:

- file path changed,
- before/after size using `wc -w` or another clear metric,
- validation commands run,
- notable improvements added,
- confirmation that unrelated dirty files were left untouched when applicable.
