# Personal Agent Skills

Reusable AI-agent skills collected from local workflows and organized for the
`skills` CLI.

## Table of Contents

- [Install](#install)
- [Layout](#layout)
- [Skills](#skills)
- [Skill Relations](#skill-relations)
- [Maintenance](#maintenance)

## Install

Install every skill from this repository:

```bash
npx --yes skills@latest add marcomc/skills --all --full-depth
```

List skills without installing:

```bash
npx --yes skills@latest add marcomc/skills --list --full-depth
```

Install one skill:

```bash
npx --yes skills@latest add marcomc/skills --skill pre-pr-review-gate --full-depth
```

For local validation from this checkout:

```bash
npx --yes skills@latest add . --list --full-depth
```

## Layout

Skills are grouped by category at the repository root as `<category>/<skill>/SKILL.md`.
Use `--full-depth` so the CLI scans every category directory.

## Skills

### Codex Workflow

| Skill | Purpose |
| --- | --- |
| [`chatgpt-import`](codex-workflow/chatgpt-import/SKILL.md) | Import ChatGPT desktop conversations into Codex as coding-ready context. |
| [`codex-pr-review-remediation-loop`](codex-workflow/codex-pr-review-remediation-loop/SKILL.md) | Monitor and remediate GitHub PRs under Codex review. |
| [`codex-review-skill-autolearn`](codex-workflow/codex-review-skill-autolearn/SKILL.md) | Distill completed Codex review remediations into reusable skill improvements. |
| [`compact-agents-file`](codex-workflow/compact-agents-file/SKILL.md) | Compact AI-agent instruction files while preserving intent. |
| [`move-codex-chat`](codex-workflow/move-codex-chat/SKILL.md) | Move a Codex chat between local project contexts safely. |
| [`project-context-rebuilder`](codex-workflow/project-context-rebuilder/SKILL.md) | Rebuild project context from repo docs, instructions, specs, and status files. |
| [`sync-codex-skills`](codex-workflow/sync-codex-skills/SKILL.md) | Sync shared `~/.agents/skills` entries into Codex-facing skill mirrors. |
| [`update-agents-workflows`](codex-workflow/update-agents-workflows/SKILL.md) | Update repository agent instructions from observed workflows and commands. |

### Documentation

| Skill | Purpose |
| --- | --- |
| [`doc`](documentation/doc/SKILL.md) | Read, create, edit, and visually validate `.docx` documents. |
| [`document-project-flowcharts`](documentation/document-project-flowcharts/SKILL.md) | Add or refresh Mermaid flowcharts in project documentation. |

### Filesystem Organization

| Skill | Purpose |
| --- | --- |
| [`reorganize-folders`](filesystem-organization/reorganize-folders/SKILL.md) | Analyze and reorganize folders using safe move and rename operations. |

### Frontend UI

| Skill | Purpose |
| --- | --- |
| [`apply-liquid-glass-ui`](frontend-ui/apply-liquid-glass-ui/SKILL.md) | Refactor graphical app UI toward Apple's Liquid Glass design language. |

### Project Scaffolding

| Skill | Purpose |
| --- | --- |
| [`init-python-cli-project`](project-scaffolding/init-python-cli-project/SKILL.md) | Scaffold a local uv-based Python CLI project. |
| [`prepare-ansible-galaxy-role`](project-scaffolding/prepare-ansible-galaxy-role/SKILL.md) | Prepare an Ansible role repository for Galaxy publication. |

### Quality Review

| Skill | Purpose |
| --- | --- |
| [`branch-qa-remediation`](quality-review/branch-qa-remediation/SKILL.md) | Run a PR-style QA review against a base branch. |
| [`code-quality-remediation`](quality-review/code-quality-remediation/SKILL.md) | Review maintainability, duplication, performance, and cleanup opportunities. |
| [`diff-regression-check-planner`](quality-review/diff-regression-check-planner/SKILL.md) | Produce diff-aware regression checks and validation commands. |
| [`max-findings-relentless`](quality-review/max-findings-relentless/SKILL.md) | Repeat review, remediation, and test loops until no findings remain. |
| [`max-findings-review`](quality-review/max-findings-review/SKILL.md) | Maximize real PR or diff findings across any stack. |
| [`native-style-conformance-review`](quality-review/native-style-conformance-review/SKILL.md) | Review whether changes match the surrounding project's native style. |
| [`pre-pr-remediation-worker`](quality-review/pre-pr-remediation-worker/SKILL.md) | Guide edit-capable remediation sub-agents under a coordinator. |
| [`pre-pr-review-agent-workflows`](quality-review/pre-pr-review-agent-workflows/SKILL.md) | Review agent instructions, skills, prompts, and automation guidance. |
| [`pre-pr-review-backend-services`](quality-review/pre-pr-review-backend-services/SKILL.md) | Review backend services, APIs, workers, persistence, and domain logic. |
| [`pre-pr-review-ci-actions`](quality-review/pre-pr-review-ci-actions/SKILL.md) | Review GitHub Actions, CI checks, permissions, caches, and artifacts. |
| [`pre-pr-review-cli-tooling`](quality-review/pre-pr-review-cli-tooling/SKILL.md) | Review CLI, shell, Makefile, installer, and local tooling changes. |
| [`pre-pr-review-config-data-flow`](quality-review/pre-pr-review-config-data-flow/SKILL.md) | Review config, defaults, schemas, generated files, and data contracts. |
| [`pre-pr-review-docs-release`](quality-review/pre-pr-review-docs-release/SKILL.md) | Review docs, changelog, README, release, and PR-readiness text. |
| [`pre-pr-review-frontend`](quality-review/pre-pr-review-frontend/SKILL.md) | Review frontend UI, browser behavior, state, accessibility, and regressions. |
| [`pre-pr-review-gate`](quality-review/pre-pr-review-gate/SKILL.md) | Compose the local pre-PR review stack and report readiness. |
| [`pre-pr-review-infra-runtime`](quality-review/pre-pr-review-infra-runtime/SKILL.md) | Review infrastructure, runtime, deployment, containers, and service lifecycle. |
| [`pre-pr-review-security-boundaries`](quality-review/pre-pr-review-security-boundaries/SKILL.md) | Review auth, secrets, trust boundaries, and privileged side effects. |
| [`pre-pr-review-tests-validation`](quality-review/pre-pr-review-tests-validation/SKILL.md) | Review test coverage, validation strategy, fixtures, and quality gates. |
| [`scoped-pre-pr-remediation`](quality-review/scoped-pre-pr-remediation/SKILL.md) | Review and fix a scoped branch, commit range, diff, or working tree before PR. |
| [`stack-best-practices-review`](quality-review/stack-best-practices-review/SKILL.md) | Review idiomatic stack usage, maintainability, architecture fit, and modernization. |

### Release GitHub

| Skill | Purpose |
| --- | --- |
| [`create-github-release`](release-github/create-github-release/SKILL.md) | Create or update a GitHub release from a local changelog. |
| [`github-repo-discoverability`](release-github/github-repo-discoverability/SKILL.md) | Improve repository metadata, topics, labels, README, and discoverability. |
| [`pr-description-markdown`](release-github/pr-description-markdown/SKILL.md) | Generate a Markdown PR description from git diff and log. |
| [`repo-publication-sanitizer`](release-github/repo-publication-sanitizer/SKILL.md) | Sanitize a repository before public release or PR publication. |

### Spec Workflow

| Skill | Purpose |
| --- | --- |
| [`generate-speckit-constitution-prompts`](spec-workflow/generate-speckit-constitution-prompts/SKILL.md) | Generate prompt blocks for `/speckit.constitution`. |
| [`generate-speckit-specify-prompts`](spec-workflow/generate-speckit-specify-prompts/SKILL.md) | Generate prompt blocks for `/speckit.specify`. |
| [`speckit-kanban-sync`](spec-workflow/speckit-kanban-sync/SKILL.md) | Sync generated Speckit tasks into `TODO.kanban`. |

### Task Management

| Skill | Purpose |
| --- | --- |
| [`add-todo`](task-management/add-todo/SKILL.md) | Capture user ideas into the active project TODO artifact. |

### Tooling MCP

| Skill | Purpose |
| --- | --- |
| [`mcpone-install-mcp-server`](tooling-mcp/mcpone-install-mcp-server/SKILL.md) | Install or update an MCP server in McpOne and enable it in Codex Cluster A. |

## Skill Relations

Only skills with a detected `$skill-name` reference are shown. External nodes are
referenced by included skills but are intentionally not bundled in this repo.

```mermaid
flowchart TD
    classDef external fill:#f7f7f7,stroke:#999,stroke-dasharray: 4 4,color:#555;

    review_profiles["pre-pr-review-* profiles<br/>agent-workflows, backend-services, ci-actions,<br/>cli-tooling, config-data-flow, docs-release,<br/>frontend, infra-runtime, security-boundaries,<br/>tests-validation"]
    record_agent_learning["record-agent-learning<br/>(external)"]:::external
    security_best_practices["security-best-practices<br/>(external)"]:::external

    codex_pr_review_remediation_loop["codex-pr-review-remediation-loop"]
    codex_review_skill_autolearn["codex-review-skill-autolearn"]
    pre_pr_remediation_worker["pre-pr-remediation-worker"]
    scoped_pre_pr_remediation["scoped-pre-pr-remediation"]
    pre_pr_review_gate["pre-pr-review-gate"]
    branch_qa_remediation["branch-qa-remediation"]
    diff_regression_check_planner["diff-regression-check-planner"]
    max_findings_relentless["max-findings-relentless"]
    max_findings_review["max-findings-review"]
    code_quality_remediation["code-quality-remediation"]
    repo_publication_sanitizer["repo-publication-sanitizer"]
    project_context_rebuilder["project-context-rebuilder"]
    stack_best_practices_review["stack-best-practices-review"]
    create_github_release["create-github-release"]
    github_repo_discoverability["github-repo-discoverability"]

    codex_pr_review_remediation_loop --> codex_review_skill_autolearn
    codex_pr_review_remediation_loop --> pre_pr_remediation_worker
    codex_pr_review_remediation_loop --> scoped_pre_pr_remediation
    codex_pr_review_remediation_loop --> pre_pr_review_gate
    codex_pr_review_remediation_loop --> review_profiles
    codex_pr_review_remediation_loop --> record_agent_learning

    codex_review_skill_autolearn --> record_agent_learning

    branch_qa_remediation --> review_profiles
    branch_qa_remediation --> record_agent_learning

    diff_regression_check_planner --> review_profiles
    diff_regression_check_planner --> record_agent_learning

    max_findings_review --> review_profiles
    max_findings_review --> record_agent_learning

    max_findings_relentless --> pre_pr_remediation_worker
    max_findings_relentless --> review_profiles
    max_findings_relentless --> repo_publication_sanitizer
    max_findings_relentless --> record_agent_learning

    scoped_pre_pr_remediation --> max_findings_relentless
    scoped_pre_pr_remediation --> pre_pr_remediation_worker
    scoped_pre_pr_remediation --> pre_pr_review_gate
    scoped_pre_pr_remediation --> review_profiles
    scoped_pre_pr_remediation --> record_agent_learning

    pre_pr_review_gate --> project_context_rebuilder
    pre_pr_review_gate --> branch_qa_remediation
    pre_pr_review_gate --> max_findings_review
    pre_pr_review_gate --> diff_regression_check_planner
    pre_pr_review_gate --> code_quality_remediation
    pre_pr_review_gate --> repo_publication_sanitizer
    pre_pr_review_gate --> max_findings_relentless
    pre_pr_review_gate --> scoped_pre_pr_remediation
    pre_pr_review_gate --> pre_pr_remediation_worker
    pre_pr_review_gate --> codex_review_skill_autolearn
    pre_pr_review_gate --> stack_best_practices_review
    pre_pr_review_gate --> review_profiles
    pre_pr_review_gate --> security_best_practices
    pre_pr_review_gate --> record_agent_learning

    code_quality_remediation --> repo_publication_sanitizer
    code_quality_remediation --> record_agent_learning

    stack_best_practices_review --> record_agent_learning
    repo_publication_sanitizer --> record_agent_learning

    create_github_release --> pre_pr_review_gate
    github_repo_discoverability --> repo_publication_sanitizer
```

## Maintenance

Refresh from the installed local source only after rechecking provenance:

```bash
npx --yes skills@latest add . --list --full-depth
find . -name '*.md' -print0 | xargs -0 markdownlint --config /Users/mmassari/.markdownlint.json
find . -name '*.sh' -print0 | xargs -0 shellcheck --enable=all
```
