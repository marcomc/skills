---
name: init-python-cli-project
description: Scaffold a new local Python CLI project under the user's Development workspace using the shared uv-based template, including README, AGENTS.md, Makefile, pyproject.toml, config example, tests, and standalone install flow. Use when the user asks to initialize, bootstrap, scaffold, or start a new Python CLI project.
---

# Init Python CLI Project

Use this skill when the user wants a new Python CLI project scaffolded from the
shared local template.

## What This Skill Does

- generates a new project from the canonical template at
  `/Users/mmassari/Development/templates/python-cli-template`
- fills in project placeholders for names, author, config path, Python version,
  and description
- optionally initializes Git
- optionally runs `uv sync --extra dev` in the generated project

## Default Assumptions

If the user does not specify otherwise:

- create the project under `/Users/mmassari/Development`
- derive `cli_name` from the requested project name in kebab-case
- derive `package_name` from `cli_name` in snake_case
- derive `config_name` from `cli_name`
- use Python `3.11`
- use MIT license
- infer author name and email from local Git config when available

## Required Steps

1. Infer or confirm the destination path and project name.
1. Run the scaffolder script:

```bash
python3 /Users/mmassari/.agents/skills/init-python-cli-project/scripts/init_python_cli_project.py \
  --destination /Users/mmassari/Development/<project-name>
```

1. Read the generated `README.md`, `AGENTS.md`, and `Makefile` to confirm the
   placeholders were resolved correctly.
1. Run at least:

```bash
cd /Users/mmassari/Development/<project-name>
make test
make lint
```

1. Report the generated path, inferred names, and any follow-up adjustments you
   made.

## Optional Flags

Use these when the user gives more detail:

```bash
python3 /Users/mmassari/.agents/skills/init-python-cli-project/scripts/init_python_cli_project.py \
  --destination /Users/mmassari/Development/<project-name> \
  --project-name "<Project Name>" \
  --cli-name "<cli-name>" \
  --package-name "<package_name>" \
  --description "<short description>" \
  --python-version 3.12 \
  --author-name "<Author Name>" \
  --author-email "<author@example.com>" \
  --config-name "<config-name>"
```

## Guardrails

- Prefer the shared template over inventing files from scratch.
- Do not remove the standalone `make install` flow unless the user explicitly
  asks for a different distribution model.
- Keep the generated `README.md`, `CHANGELOG.md`, `TODO.md`, and `AGENTS.md`
  intact unless the user asks for immediate customization.
- If the destination exists and is non-empty, stop unless `--force` is clearly
  appropriate.
