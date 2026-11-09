---
name: update-agents-file-templates
description: Use when mining existing AI-agent instruction files or promoting current-project rules into reusable template overlays
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" --> <!-- privacy_scan: allow -->
<!-- Public author attribution required by the shared skills collection. -->

# Update Agents File Templates

Mine and improve reusable templates from `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`.github/copilot-instructions.md` and `.github/instructions/*.instructions.md`.
Resolve the owning template repo through `--template-repo` or
`AGENTS_TEMPLATE_REPO`; the helper needs Python with PyYAML. Out-of-sync reporting
also requires the sibling `init-agents-file` skill; install both together.

## Workflow

1. Use the named project first. Scope broad scans before running them; when the
   user requests all projects without roots, infer a likely development root and
   ask before scanning. Keep paths configurable.
2. Before drafting or accepting promotion, read the installed consolidation
   skill's `references/coherence.md` and `references/integration.md`. One editor
   refines the full affected contract with proportionate local, peer or council
   review. Preserve superior policy, coverage and source-note history; assess
   overlap, routing and loaded-context cost.
3. Generate ignored `.work/` matrices/drafts, inspect detected instruction kinds,
   and review conflicts and privacy. For a novel approved clean learning, prepare
   a reviewed full-template replacement plus `--edit-plan` with
   `before_sha256`, `replacement_file`, `replacement_sha256`, `operation`,
   `integrated_rule`, `review_rationale`, `draft_sha256`, `candidate_rule` and
   `coverage_rationale`. Bind the exact approved draft and explain how the final
   rule preserves its intent. Refine/merge/supersede instead of blindly appending.
   An unchanged already-covered rule needs no replacement.
4. Preview the reviewed plan, then use `--apply` only under existing authority.
   Revalidate source/draft after concurrent edits. Keep actual user choices,
   ambiguous ownership and unresolved conflicts pending with evidence and next
   actions; leave conflict notes rather than forcing a merge.
5. Validate changed Markdown and run the privacy scanner. Refresh affected
   generated consumers while preserving local content, reconcile complete skill
   sources and configured copies, and require current coherence-bound integration
   receipts before declaring the handoff integrated. An out-of-sync report alone
   does not complete this work. Treat budget warnings as routing review, retaining
   directly loaded safety/validation rules and project-local requirements.

## Helper modes

All modes use this helper and the owning repository. For example, preview a
novel learning's reviewed plan:

```bash
python3 "${AGENTS_TEMPLATE_REPO}/skills/update-agents-file-templates/scripts/update_agents_templates.py" \
  --template-repo "${AGENTS_TEMPLATE_REPO}" \
  --apply-learning-draft "${AGENTS_TEMPLATE_REPO}/.work/learning-upstream/<lesson_family>.md" \
  --edit-plan "${AGENTS_TEMPLATE_REPO}/.work/<reviewed-edit-plan>.json"
```

Select arguments for the same helper:

| Mode | Arguments |
| --- | --- |
| Full mining | `--scan-root ROOT --max-depth 2` |
| One-template mining | `--scan-root ROOT --template python --max-depth 2` |
| Current-project draft | `--current-project . --template python` |
| Handoff summary | `--learning-upstream-summary` |
| Reviewed learning preview | `--apply-learning-draft DRAFT --edit-plan PLAN` |
| Reviewed apply | Same learning arguments plus `--apply` |
| Generated-file status/budget | `--scan-root ROOT --out-of-sync-report` |

Already-covered rules can be checked without a replacement plan. Mining creates
review material; curated source edits follow the review above.

## Publication boundaries

Keep `.work/` ignored and uncommitted. Curated templates must use public-safe
placeholders instead of personal paths, private domains, hostnames, IPs, secrets or account
identifiers. Keep unresolved conflict evidence in reports, not forced rules.
