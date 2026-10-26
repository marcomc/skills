---
name: prepare-ansible-galaxy-role
description: Prepare a local standalone Ansible role repository for Ansible Galaxy publication. Use when the user asks to make an Ansible role publishable, Galaxy-ready, release-ready, or to audit role metadata, README, changelog, upgrade notes, and publication commands before publishing.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Prepare Ansible Galaxy Role

## Boundaries

- Prepare local files only unless the user explicitly asks to commit, push, tag,
  publish, or open a pull request.
- Do not publish to Ansible Galaxy or GitHub from this skill by default.
- Treat standalone roles and collections differently. If the repository is an
  Ansible collection with `galaxy.yml`, stop and explain that this skill covers
  standalone roles unless the user asks to adapt it.
- Keep the workflow generic. Do not copy assumptions from a previous project.

## Workflow

1. Read local instructions first: `AGENTS.md`, `CLAUDE.md`, README, changelog,
   `meta/main.yml`, role defaults, CI/workspace files, and git remotes/tags.
2. Classify the repository:
   - standalone role when `meta/main.yml` exists and there is no collection
     `galaxy.yml`
   - collection when `galaxy.yml` exists
   - monorepo or subrole when the role lives below the repository root
   - ambiguous when neither gives a clear answer
3. Build a publication facts table from evidence:
   - Galaxy namespace and role name
   - GitHub owner/repo and default branch
   - current version/tag strategy
   - author, license, support, repository URL
   - minimum Ansible version
   - supported platforms and Galaxy tags
   - required install, upgrade, test, release, and publication commands
4. Ask the user concise questions only for blocking facts that cannot be safely
   inferred. If a fact is inferred, record it as an assumption in the response.
5. Apply local edits to make the role publication-ready.
6. Run the repository-required linters and relevant role validation commands.
7. Finish with changed files, validations run, assumptions made, remaining
   blockers, and exact publish commands. Do not say it is published unless it
   was explicitly published.

## Required Outputs

The prepared role should have:

- valid `meta/main.yml` Galaxy metadata
- README that works as the Galaxy landing page
- changelog with a release-ready entry and breaking changes where applicable
- upgrade guide for major or breaking releases
- release/publishing runbook with GitHub release and Galaxy import commands
- install instructions for pinned Galaxy versions
- documented validation commands
- optional dry-run or explicitly invoked publication helper only if the
  repository already has a command framework such as Make, Just, Task,
  Workspace, or npm scripts

Use [REFERENCE.md](REFERENCE.md) for the full checklist and command patterns.

## Questions To Ask When Needed

Ask before editing when these cannot be inferred with high confidence:

- Galaxy namespace and role name
- public repository URL and intended default branch
- release version and whether the release is major/minor/patch
- supported Linux or platform matrix
- minimum supported Ansible version
- license, maintainer, support path, or organization ownership
- whether to add a local publication helper to an existing command framework
- whether publication automation should be dry-run only or allowed to call
  Galaxy when invoked with credentials

## Validation

Prefer repo-native commands. At minimum, validate changed Markdown, YAML, shell,
and Ansible files with the linters required by local instructions. For Ansible
role changes, prefer `ansible-lint` through the repository's documented wrapper
when one exists.

Also check that secrets, API keys, tokens, host data, and sensitive inventory
values are not logged or documented in committed examples.
