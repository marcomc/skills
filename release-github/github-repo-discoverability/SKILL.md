---
name: github-repo-discoverability
description: Audit and improve GitHub repository discoverability by analyzing repository content, README, metadata, language, dependencies, comparable repositories, topics, labels, description, public-readiness signals, and community promotion channels. Use when the user asks to add or refresh GitHub topics, labels, descriptions, repository metadata, SEO, discoverability, promotion, or public-facing positioning for one repository or many repositories.
---

# GitHub Repo Discoverability

Use this skill to make repositories easier to find and evaluate on GitHub
without adding misleading metadata. The goal is not to stuff tags; it is to
make the repository's public surface match its real purpose, audience,
ecosystem, and maturity.

Prefer an audit and proposal before applying metadata. Apply changes only when
the user explicitly asks to update GitHub or has clearly approved the proposed
scope.

## Discovery Surfaces

Optimize these surfaces in order:

1. Repository name and description: GitHub search uses these by default.
2. Topics: GitHub limits repositories to 20 topics; choose strong ones.
3. README first screen: converts visitors who arrive from search, stars,
   topics, profiles, or external links.
4. Labels: improve issue triage and contributor onboarding; they are not
   marketing topics.
5. Releases, license, quick start, screenshots, and examples: increase trust
   and conversion after discovery.
6. Community channels: point maintainers toward where the target audience
   already pays attention.

## Inputs to Inspect

For a local repository, read enough of the real project to infer the right
metadata:

- `README*`, docs index files, `CHANGELOG*`, `TODO*`, roadmap files,
  `AGENTS.md`, and contribution docs.
- Package manifests such as `pyproject.toml`, `package.json`, `Cargo.toml`,
  `go.mod`, gemspecs, plugin manifests, Dockerfiles, compose files, Ansible
  files, app manifests, and CI workflows.
- Entry points, CLI names, module names, executable scripts, tests, examples,
  and top-level source directories.
- Current GitHub metadata: description, homepage, topics, labels, visibility,
  archived state, fork state, stars, forks, pushed date, issues enabled, and
  license.

Use `rg` and focused file reads. Avoid broad scans of dependency directories,
build outputs, virtual environments, and vendored code.

## Public Readiness Gate

Before promoting a repository, classify it:

- `public-ready`: clear purpose, install or usage path, license, README,
  recent-enough activity, and no obvious private/local leakage.
- `usable but rough`: useful project, but README, release, examples, labels,
  or issue setup need small improvements.
- `internal-looking`: unclear audience, local paths, private assumptions,
  missing license, or incomplete setup.
- `not worth promoting yet`: experimental, unsafe to expose, secret risk, or
  missing the core user path.

For private, archived, forked, template, or internal-looking repositories,
default to audit-only unless the user explicitly asks to apply metadata anyway.
When leakage risk matters, run or recommend `$repo-publication-sanitizer` before
public promotion.

## Topic Selection

GitHub topics should describe the repository's purpose, subject area,
community, platform, and language. Topic names must be lowercase, use hyphens,
and stay within GitHub's limits. Never exceed 20 topics.

Build a candidate list from:

- Domain and ecosystem: `home-assistant`, `mqtt`, `ai-agent`,
  `cloudflare`, `ansible`, `openai`, `wordpress`.
- Use case: `home-automation`, `network-monitoring`, `backup`,
  `energy-monitoring`, `podcast`, `release-automation`.
- Platform and runtime: `macos`, `linux`, `raspberry-pi`, `docker`,
  `ios`, `swift`, `python`, `typescript`.
- Protocols and integrations: `mqtt-discovery`, `websocket`, `tailscale`,
  `samba`, `route53`, `github-actions`.
- Audience and distribution: `self-hosted`, `cli`, `developer-tools`,
  `open-source-agent`, `devops`, `iot`.

Score candidates with this model:

```text
score =
  relevance_to_actual_repo
  + ecosystem_or_community_value
  + known_github_topic_signal
  + comparable_repo_frequency
  + README_or_manifest_support
  + useful_specificity
  - misleading_or_aspirational_penalty
  - too_generic_penalty
  - dead_or_obscure_topic_penalty
```

Prefer a balanced set:

- 4-6 ecosystem or community topics,
- 4-6 language, framework, protocol, or integration topics,
- 3-5 use-case topics,
- 2-4 platform or runtime topics,
- 1-2 audience or distribution topics.

Do not force exactly 20 topics. Use 12-16 strong topics when the repository is
narrow. Use 20 only when every topic is defensible.

## Topic Validation

Validate important candidates before applying:

- Check whether `https://github.com/topics/<topic>` exists or has meaningful
  repository results.
- Search similar repositories using topic, language, and keyword combinations.
- Compare topic use across 5-10 relevant repositories, preferring active or
  starred examples over abandoned projects.
- Keep precise topics that users actually search for; drop invented synonyms
  that fragment discovery.

Useful checks:

```bash
gh api "search/repositories?q=topic:home-assistant+language:Python&sort=stars&order=desc&per_page=10"
```

```bash
gh api repos/OWNER/REPO/topics -H 'Accept: application/vnd.github+json'
```

## Description

If the repository description is empty, vague, or missing the key ecosystem,
propose a short description before topics. Keep it under roughly 80-100
characters when possible.

Good description shape:

```text
<platform/use-case> <project type> for <ecosystem/protocol>
```

Examples:

- `macOS telemetry agent for Home Assistant MQTT discovery`
- `CLI for repairing RaiPlay Sound podcast filenames`
- `Raspberry Pi Home Assistant infrastructure automation`

## Labels

Labels are for issue and PR workflow, not search marketing. Add or refresh
labels when they help maintainers and contributors understand work.

Useful families:

- `area: <domain>` for code or product area.
- `integration: <system>` for external services and protocols.
- `platform: <runtime>` for operating systems, hardware, or deployment
  targets.
- `kind: <type>` for telemetry, command, docs, bug, task, or roadmap.
- `priority: high|medium|low`.
- `status: needs-triage|ready|blocked`.
- standalone `release`, `security`, `documentation`, `good first issue`,
  and `help wanted` when appropriate.

Preserve existing labels unless the user asks to standardize aggressively.
Use `gh label create --force` only for labels in the approved scope.

## README Discovery Patch

After choosing topics, check whether the README first screen supports them.
Report small README gaps such as:

- the main ecosystem or protocol is absent from the opening paragraph,
- there is no quick start or install command,
- the project lacks a screenshot, example output, or demo when visual output
  matters,
- the license, current status, or supported platform is unclear,
- the README reads like internal notes rather than a public project page.

Do not edit README files unless the user asks for documentation changes.

## Community Promotion Hints

For public-ready repositories, suggest 2-5 community channels where promotion
would be credible:

- ecosystem forums such as Home Assistant Community, Raspberry Pi forums, or
  Cloudflare community,
- relevant Reddit communities,
- GitHub topics and awesome lists,
- Hacker News or Show HN for polished developer tools,
- project-specific forums, Discords, or mailing lists,
- a short release note, blog post, or demo video when the repository benefits
  from explanation.

Do not recommend spammy broad posting. Match the channel to the project's real
audience and maturity.

## Single-Repository Workflow

1. Resolve the GitHub repository from local `git remote`, explicit repo name,
   or URL.
2. Read local project context and current GitHub metadata.
3. Run the public readiness gate.
4. Generate candidate description, topics, labels, README gaps, and promotion
   hints.
5. Validate high-value topics against GitHub topics or comparable repositories.
6. Present a concise proposal with reasons and any risky assumptions.
7. Apply only approved metadata:
   - `gh repo edit OWNER/REPO --description '...'`
   - `gh api repos/OWNER/REPO/topics -X PUT ...`
   - `gh label create ... --force`
8. Re-read remote metadata and report exactly what changed.

## Bulk Workflow

For "all my repositories" or organization-wide work:

1. List repositories with `gh repo list OWNER --limit N --json ...` or
   `gh api --paginate /user/repos`.
2. Exclude archived repositories, forks, mirrors, generated/template repos, and
   private repositories by default.
3. Batch the audit first. Produce a table:
   `repo`, `readiness`, `description action`, `topic action`, `label action`,
   `skip reason`.
4. Ask for approval before applying bulk writes unless the user explicitly
   requested immediate application.
5. Apply in small batches and verify after each batch to avoid rate-limit or
   permission confusion.

Never silently promote every accessible repository. Some accessible repos are
private, stale, forks, mirrors, or not intended for public discovery.

## GitHub API Notes

- Topics are replaced as a whole set via `PUT /repos/{owner}/{repo}/topics`;
  always merge intentional existing topics with approved new topics before
  sending the replacement.
- Reading topics uses `GET /repos/{owner}/{repo}/topics`.
- Creating or updating repository labels uses issue label endpoints such as
  `POST /repos/{owner}/{repo}/labels` and
  `PATCH /repos/{owner}/{repo}/labels/{name}`; `gh label create --force` is a
  practical wrapper.
- Fine-grained tokens need repository metadata administration write permission
  for topic updates and issue write permissions for label management. Classic
  `repo` scope is usually enough for owned repositories.
- Topic names are public even for private repositories.

## Output Requirements

For audit-only work, return:

- readiness classification,
- proposed description,
- proposed topics grouped by reason,
- proposed labels grouped by family,
- dropped candidates and why,
- README discovery gaps,
- community promotion hints,
- exact GitHub operations that would be run if approved.

For applied work, return:

- repositories changed,
- final description and topics,
- labels created or updated,
- repositories skipped and why,
- verification command/result,
- any permission or rate-limit gaps.
