# Agent Instructions

## Scope

This repository publishes reusable AI-agent skills for installation through
`skills@latest`.

## Skill Layout

- Keep skills grouped as `<category>/<skill>/SKILL.md` at the repository root.
- Keep category names stable unless the README skill index and relationship
  diagrams are updated in the same change.
- Do not add external skills unless they are intentionally forked or clearly
  attributed.

## Public-Safe Content

- Avoid absolute maintainer-machine paths such as `/Users/<name>/...` in tracked
  docs, skills, and scripts.
- Prefer `$HOME`, `Path.home()`, environment variables, or paths relative to the
  skill directory.
- Use obvious placeholders for examples, such as `<project-name>`,
  `old-project`, `new-project`, and `user@example.com`.

## Validation

- Run `npx --yes skills@latest add . --list` after changing skill layout or
  frontmatter.
- Run `markdownlint --config "$HOME/.markdownlint.json"` on changed Markdown.
- Run `shellcheck --enable=all` on changed shell scripts.
- Run `python3 -m compileall -q .` after changing Python helper scripts.
