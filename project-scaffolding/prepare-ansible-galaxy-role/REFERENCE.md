# Prepare Ansible Galaxy Role Reference

This reference supports the `prepare-ansible-galaxy-role` skill. It is generic
for standalone Ansible roles published to Ansible Galaxy.

## Evidence To Gather

Inspect the repository before making changes:

- local agent instructions: `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, or
  equivalent
- role metadata: `meta/main.yml`
- repository layout and whether the role is at root or in a monorepo subpath
- README and docs folder
- changelog or release notes
- license file
- defaults, vars, tasks, handlers, tests, and molecule configuration
- CI configuration
- command framework files: `Makefile`, `Justfile`, `Taskfile.yml`,
  `workspace.yml`, `package.json`, `tox.ini`, `noxfile.py`
- git remote URLs, default branch, branch state, and tags
- existing Ansible Galaxy role state when the role is already published

Prefer direct evidence over guesses. Examples:

```bash
git remote -v
git ls-remote --symref origin HEAD
git tag --list --sort=-v:refname
ansible-galaxy role info namespace.role_name
```

## Publication Facts Table

Maintain an internal table like this while working:

| Fact | Evidence | Confidence | Action |
| --- | --- | --- | --- |
| Namespace | `meta/main.yml`, Galaxy info, GitHub org | high/medium/low | use/ask |
| Role name | `meta/main.yml`, Galaxy info | high/medium/low | use/ask |
| Default branch | `git ls-remote --symref origin HEAD` | high | use |
| Version | changelog, tags | high/medium/low | use/ask |
| License | `LICENSE`, `meta/main.yml` | high/medium/low | use/ask |
| Supported platforms | role logic, tests, README, metadata | medium | confirm if risky |

Report the assumptions made in the final response.

## Required Role Metadata

For a standalone role, `meta/main.yml` should include:

- `galaxy_info.namespace`
- `galaxy_info.role_name`
- `galaxy_info.author`
- `galaxy_info.description`
- `galaxy_info.company` when applicable
- `galaxy_info.license`
- `galaxy_info.min_ansible_version`
- `galaxy_info.platforms`
- `galaxy_info.galaxy_tags`
- `dependencies`

Keep `galaxy_tags` search-oriented but honest. Avoid stuffing tags that the role
does not actually support.

## README Requirements

The README is the Galaxy landing page. Ensure it has:

- short description of what the role does
- table of contents for substantial README files
- requirements
- installation from Galaxy, including pinned version syntax when relevant
- role variables table
- example playbook
- supported platform matrix
- testing or validation instructions
- upgrade guide link for breaking releases
- changelog link
- repository, support, maintainer, and license details

Do not claim a Galaxy release exists before the tag has been published and
imported. Use wording such as "after the import is complete" when preparing
ahead of time.

## Changelog Requirements

For a release-ready changelog entry:

- use a dated release heading only when finalizing a release
- list breaking changes before general changes
- group large releases by scope
- link to upgrade guides for major or breaking releases
- mention documentation and publication helper changes
- keep entries concise and user-facing

For major releases, add an upgrade guide when users may need to change playbooks,
variables, supported platforms, credentials, privilege escalation, or install
commands.

## Upgrade Guide Requirements

Create `docs/upgrading-to-X.Y.Z.md` for major or breaking releases. Include:

- who needs the guide
- required changes
- before/after playbook examples
- variable rename table
- removed or changed defaults
- supported platform changes
- recommended rollout checklist
- compatibility notes for old variables that still work

## Release Runbook Requirements

Create or update a release runbook, usually `docs/releasing.md`, with:

- local preflight checks
- GitHub release/tag order
- Ansible Galaxy import command
- import status check
- role info check
- pinned install verification
- troubleshooting for stale branch, missing tag, stale metadata, or token
  issues

For standalone roles, Ansible Galaxy imports from GitHub. It does not require a
collection artifact upload. Version discovery comes from SemVer Git tags.

Useful command patterns:

```bash
ansible-galaxy role import <github_owner> <github_repo> \
  --branch <default_branch> \
  --role-name <role_name> \
  --token "$ANSIBLE_GALAXY_TOKEN"

ansible-galaxy role import --status <github_owner> <github_repo> \
  --token "$ANSIBLE_GALAXY_TOKEN"

ansible-galaxy role info <namespace>.<role_name>

tmp_dir="$(mktemp -d)"
ansible-galaxy role install --roles-path "${tmp_dir}" <namespace>.<role_name>,<version>
rm -rf "${tmp_dir}"
```

## Publication Helper Rules

Add a helper command only when the repository already has a command framework.
Do not introduce a new framework just for Galaxy publication unless the user
asks.

The helper should:

- use fixed repository publication values inferred from local metadata
- read the Galaxy token from an existing secret/config mechanism or
  `ANSIBLE_GALAXY_TOKEN`
- fail clearly when the token is missing
- default to printing or dry-running the publication flow unless the user asks
  for an executable publish action
- support `status` and `info`, plus `publish` only when the user approves a
  helper that can call Galaxy
- avoid accepting arbitrary user-controlled shell strings
- avoid pushing, tagging, or publishing to GitHub unless explicitly requested

If no command framework exists, document the commands in `docs/releasing.md`
instead.

## Validation Checklist

Run the commands required by local instructions. Common checks:

```bash
markdownlint -c ~/.markdownlint.json README.md CHANGELOG.md docs/*.md
yamllint meta/main.yml
ansible-lint .
shellcheck --enable=all path/to/script.sh
```

Prefer wrapper commands such as `make lint`, `just lint`, `task lint`, or
`ws ansible-lint` when the repo documents them.

Also verify:

- `meta/main.yml` parses as YAML
- README links resolve locally where possible
- changelog links to upgrade docs correctly
- release commands do not expose tokens
- generated helper commands fail safely without credentials
- no local-only absolute paths are committed
- Ansible tasks that transmit or receive sensitive values use `no_log: true`

## Final Response Template

Use a compact final response:

- changed files
- key publication improvements
- validation commands run
- assumptions made
- blockers or values still needing user confirmation
- exact next commands for GitHub release and Galaxy import

Never state that the role is published unless the user explicitly asked for
publication and the import succeeded.
