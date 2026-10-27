# Agent Instructions

## Scope

This repository publishes reusable AI-agent skills for installation through
`skills@latest`.

## Skill Layout

- Keep skills grouped as `<category>/<skill>/SKILL.md` at the repository root.
- Mark every first-party skill in `SKILL.md`, immediately after YAML frontmatter,
  with this searchable HTML comment:
  `<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->`.
- For a third-party skill personalized at the user's request, use
  `provenance="adapted"`, retain its upstream attribution and license, and name
  the upstream skill in the marker. Do not import unmodified third-party skills
  or installed skills without this marker.
- For a skill generated from an external document or dataset, use
  `provenance="derived"`, name the source in the marker, retain its attribution,
  and check whether its contents are suitable for public redistribution before
  adding it here.
- Do not publish source-derived material from books, service manuals, parts
  catalogs, paid documents or restricted datasets unless the source license or
  other documented permission explicitly allows public redistribution. A
  user-provided copy, a request to create a private skill, attribution, or the
  `derived` marker does not itself grant that permission. When rights are unclear,
  keep the skill and its supporting files local and out of the public README and
  `skills@latest` collection. Check chapter notes, extracted text, tables, images,
  indexes and datasets, not only the top-level `SKILL.md`.
- Whenever a first-party skill is created or updated in another project, verify
  its origin from the user request and task history, then reconcile its complete
  folder here before considering the skill work complete. Include its references,
  scripts and agent metadata; place it in the appropriate category; update the
  README index, changelog and any affected relationship diagrams; add or refresh
  the marker; and run the applicable validation checks below.
- Treat a third-party skill as eligible only after the user explicitly asks to
  personalize it. Preserve upstream attribution and license when doing so.
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
- When updating a tracked skill with an active local counterpart, compare the
  two before publication and deliberately reconcile any drift.
- Run `markdownlint --config "$HOME/.markdownlint.json"` on changed Markdown.
- Run `shellcheck --enable=all` on changed shell scripts.
- Run `python3 -m compileall -q .` after changing Python helper scripts.
