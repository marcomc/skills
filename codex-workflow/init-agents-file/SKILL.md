---
name: init-agents-file
description: Use when initializing or refreshing project AI-agent instruction files from reusable global and project-type templates
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Init Agents File

Use this skill to create or refresh a project AI-agent instruction file from an
`agents-file-templates-and-skills` repository.

This skill is meant to be invoked through the active coding agent. The bundled
Python script is the deterministic helper to run after deciding the target
project, template repository, output filename, and apply mode.

The Python interpreter running the helper must have PyYAML installed. The
template repository supplies `templates.yml` and the template files; these are
external prerequisites, not bundled skill resources.

## Workflow

1. Identify the target project and template repository.
2. Identify the target agent when the user wants an agent-specific filename.
3. Detect project types from files and existing instructions.
4. Run a dry run first.
5. Review generated content for relevance and privacy.
6. Apply only when the user asked to create or update the project file.
7. Use the budget report when the rendered root file is large; route conditional
   detail to a task-relevant document or skill without moving mandatory safety
   and validation boundaries out of directly loaded instructions.

The script preserves content between:

```text
<!-- BEGIN PROJECT LOCAL -->
<!-- END PROJECT LOCAL -->
```

When `--apply` targets an existing file without the generated marker, it stops
without changing the file. Review or move that file before applying generated
instructions. On a managed refresh, if template changes prevent recovery of
placeholder values, `--apply` stops without changing the file until you supply
each missing value with `--set KEY=VALUE`. Directly recorded project name,
project description, and global policy path values are recovered separately.
Changes with no unrecovered placeholders can still be applied. Dry-run output
remains available for comparison and warns when explicit values are needed.

## Commands

Manual fallback dry run for the current project:

```bash
python3 /path/to/agents-file-templates-and-skills/skills/init-agents-file/scripts/init_agents_file.py \
  --project .
```

Manual fallback apply after review:

```bash
python3 /path/to/agents-file-templates-and-skills/skills/init-agents-file/scripts/init_agents_file.py \
  --project . \
  --apply
```

Check whether a generated project instruction file is current:

```bash
python3 /path/to/agents-file-templates-and-skills/skills/init-agents-file/scripts/init_agents_file.py \
  --project . \
  --check \
  --json
```

Review the generated instruction budget without modifying the project:

```bash
python3 /path/to/agents-file-templates-and-skills/skills/init-agents-file/scripts/init_agents_file.py \
  --project . \
  --budget-report \
  --json
```

Generate an agent-specific instruction filename:

```bash
python3 /path/to/agents-file-templates-and-skills/skills/init-agents-file/scripts/init_agents_file.py \
  --project . \
  --agent claude \
  --output-mode specific \
  --apply
```

Force project types:

```bash
python3 /path/to/agents-file-templates-and-skills/skills/init-agents-file/scripts/init_agents_file.py \
  --project . \
  --types python,ansible,workspace
```

Agent-specific output names:

- `--agent openai --output-mode specific`: `AGENTS.md`
- `--agent opencode --output-mode specific`: `AGENTS.md`
- `--agent claude --output-mode specific`: `CLAUDE.md`
- `--agent gemini --output-mode specific`: `GEMINI.md`
- `--agent copilot --output-mode specific`: `.github/copilot-instructions.md`

## Scope Rules

- Do not scan sibling projects unless the user asked for broader analysis.
- If the user says only "initialize this project", operate on the current
  project and default to `AGENTS.md`.
- If the user asks for a specific agent, use `--output-mode specific` only after
  confirming they want the agent-specific filename instead of portable
  `AGENTS.md`.
- If the user implies a broader initialization but gives no scope, inspect the
  current path and ask before scanning a parent development directory.
- Prefer the installed skill config file for locating the template repository.
  If it is missing, search upward from the current project and script location;
  if still unresolved, ask the user where the repository was cloned.

## Privacy

Generated files may reference `${HOME}/AGENTS.md`, but they must not copy
personal global policy content wholesale. Keep project-specific secrets,
hostnames, IP addresses, and private domains out of reusable sections.
