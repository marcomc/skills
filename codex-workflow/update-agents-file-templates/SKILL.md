---
name: update-agents-file-templates
description: Use when mining existing AI-agent instruction files or promoting current-project rules into reusable template overlays
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Update Agents File Templates

Use this skill to improve curated `AGENTS.md` templates from real project
instructions. It can mine `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`.github/copilot-instructions.md`, and
`.github/instructions/*.instructions.md`.

The Python interpreter running the helper must have PyYAML installed. Pass the
separate template repository with `--template-repo` or `AGENTS_TEMPLATE_REPO`.

## Modes

- Full mining: scan configured roots and build a project matrix.
- Single-template mining: update the draft for one template from matching
  projects.
- Current-project promotion: extract reusable rules from the current project and
  propose them for one or more templates.
- Learning-upstream review: summarize ignored draft handoffs created by the
  learning system.
- Reviewed draft apply: write approved clean drafts into curated templates only
  when `--apply` is passed.
- Out-of-sync reporting: identify generated project instruction files that need
  refresh after template changes.

Out-of-sync reporting uses the `init-agents-file` companion helper. Install
both skills under the same skills directory; if the companion is missing, the
report stops with an install hint before writing report artifacts.

## Workflow

1. Confirm scope before broad scans.
2. Run the helper script to create ignored `.work/` artifacts.
3. Review the matrix to see which instruction file kinds were found.
4. Review drafts for conflicts, overlap, and privacy risk.
5. Edit curated templates manually from the reviewed draft material.
6. Run Markdown validation and the privacy scanner.
7. Review the generated-file budget report before treating a large root file as
   a template problem; keep directly loaded safety and validation rules intact.

## Commands

Scan a known root:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --scan-root "${PROJECT_SCAN_ROOT}" \
  --max-depth 2
```

Draft one template:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --scan-root "${PROJECT_SCAN_ROOT}" \
  --template python \
  --max-depth 2
```

Promote from the current project:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --current-project . \
  --template python
```

Summarize learning-upstream drafts:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --learning-upstream-summary
```

Preview applying an approved clean learning draft:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --apply-learning-draft "${AGENTS_TEMPLATE_REPO}/.work/learning-upstream/<lesson_family>.md"
```

Apply after review:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --apply-learning-draft "${AGENTS_TEMPLATE_REPO}/.work/learning-upstream/<lesson_family>.md" \
  --apply
```

Report generated project files that need refresh:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --scan-root "${PROJECT_SCAN_ROOT}" \
  --out-of-sync-report
```

The report includes each generated file's instruction-budget status. Treat an
over-budget result as a routing review, not as permission to delete project
local or mandatory safety rules.

## Scope Rules

- If the user names a project, operate on that project first.
- If the user asks to learn from all projects but gives no roots, infer a likely
  development root from the current path and ask before scanning it.
- Do not hardcode another developer's folder layout.

## Safety Rules

- Never commit `.work/` artifacts.
- Never copy personal paths, private domains, hostnames, IPs, secrets, or
  account identifiers into curated templates.
- Prefer placeholders when a rule needs user-specific data.
- Leave conflict notes in reports instead of forcing a questionable merge.
