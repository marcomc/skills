---
name: project-context-rebuilder
description: Rebuild project context quickly at the start of a new chat by scanning a repo for AGENTS.md, specs files, progress/status docs, TODO.md, CHANGELOG.md, and any referenced files/paths. Use when asked to bootstrap understanding of the current project or to load the canonical specs and progress artifacts before work.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Project Context Rebuilder

## Workflow

1) Locate repo root.

- Use `git rev-parse --show-toplevel` when available; otherwise treat current working directory as root.

1) Load agent instructions.

- Find and read all `AGENTS.md` files with `rg --files -g 'AGENTS.md'` from the repo root.

1) Load core context files.

- Read: `README.md`, `TODO.md`, `CHANGELOG.md` if present.
- Read any `specs/` files (all files under `specs/`, or `rg --files specs`).

1) Load progress/status files.

- Read any root-level or docs-level files that look like progress snapshots, e.g. `Project_Summary.md`, `DevOps_Journey.md`, `Status*.md`, `Progress*.md`, `Roadmap*.md`, `Backlog*.md`.
- Use `rg --files -g '*Summary*.md' -g '*Journey*.md' -g 'Status*.md' -g 'Progress*.md' -g 'Roadmap*.md' -g 'Backlog*.md'` and read the matches.

1) Follow referenced files.

- From the files loaded in steps 2-4, extract likely file paths and read them if they exist and are not URLs.
- Suggested extraction command (adjust extensions as needed):

```bash
rg -o --no-filename "[A-Za-z0-9._/-]+\.(md|yml|yaml|sh|py|json|toml|txt)" <files> | sort -u
```

- For Markdown links, scan for `](path)` targets; prefer project-relative paths.

Optional automation:

- Run `scripts/collect-context.sh` from the repo root to print the full ordered list of files to read (core + referenced). Use the output as the read list.
- Run `scripts/collect-context.sh --block` to print a ready-to-paste Markdown block grouped by core vs referenced files.

1) Summarize compactly.

- Provide a short structured summary: purpose, architecture, current status, open tasks, and key operational commands.
- Note any missing/ambiguous references or files that could not be found.

## Guardrails

- Prefer `rg` for file discovery.
- Keep context lean: read only files identified by this workflow, and avoid loading large unrelated directories.
- If multiple `AGENTS.md` exist, follow the most local file first, then the repo root.
- If a referenced file is missing, call it out explicitly.
