---
name: repo-publication-sanitizer
description: Review and sanitize a repository before GitHub or public release by finding personal data, local-system details, hostnames, IP addresses, machine-specific paths, secrets, tokens, private endpoints, and environment-specific artifacts. Use before opening or publishing a public PR/repository, and when pre-PR review needs to prevent accidental disclosure; preserve only intentional public author/package/license identity in appropriate metadata contexts.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Repo Publication Sanitizer

Use this skill before a repository, branch, PR, release, documentation set, or
package is published where other people can see the files. The goal is to
remove personal, local, machine-specific, secret, or environment-specific data
while preserving valid public author and package metadata.

## Default behavior

Default to review-only reporting unless the user explicitly asks to sanitize or
apply fixes. When remediation is requested, make conservative replacements and
validate the affected files afterward.

## Scope

Scan files that can be committed, reviewed, packaged, or published:

- tracked files in `git ls-files`,
- staged and unstaged files that are likely to be committed,
- docs, examples, scripts, tests, fixtures, config templates, CI files, package
  metadata, generated reports, and screenshots metadata when represented as
  text,
- filenames and directory names, not only file contents.

Do not scan `.git`, virtual environments, dependency caches, build outputs, or
ignored private files unless they are tracked or about to be committed.

## Allowed public identity

Preserve intentional public identity only in the right contexts:

- package metadata such as `pyproject.toml`, `package.json`, `Cargo.toml`,
  `go.mod`, plugin manifests, and app store/package descriptions,
- `LICENSE`, `NOTICE`, copyright headers, release notes, and formal attribution
  sections,
- README author, maintainer, credits, or contact sections,
- project URLs, organization names, or domains that are explicitly intended to
  be public.

Do not remove a public author name or public maintainer contact just because it
is personal. Do remove that same information when it appears as an accidental
local path, host, debug value, fixture, copied terminal output, or unrelated
example.

## Data to find

Treat these as findings unless they are clearly public and intentional:

- absolute home paths such as `/Users/name`, `/home/name`, `C:\Users\name`, and
  `/private/var/folders/...`,
- local workspace paths, mounted volumes, temporary directories, editor paths,
  shell history fragments, and machine-specific cache paths,
- hostnames, local device names, Bonjour names, SSH aliases, Wi-Fi names, and
  service URLs tied to a real private environment,
- public IP addresses and private network IP addresses that identify the user's
  actual network, unless they are RFC documentation addresses,
- email addresses, phone numbers, postal addresses, usernames, handles, and
  account IDs that are not part of intentional package or author metadata,
- secrets, tokens, API keys, passwords, cookies, authorization headers, private
  keys, certificates, OAuth client secrets, and signed URLs,
- cloud account IDs, bucket names, project IDs, organization IDs, database URLs,
  webhook URLs, Sentry DSNs, telemetry endpoints, and private registry URLs,
- real serial numbers, MAC addresses, Bluetooth identifiers, device IDs, and
  hardware inventory values when they belong to the user's equipment,
- screenshots or logs copied into Markdown that reveal local paths, hostnames,
  IPs, account names, shell prompts, or tool configuration.

Use RFC documentation examples when examples need concrete values:

- domains: `example.com`, `example.org`, `example.net`,
- IPv4: `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`,
- IPv6: `2001:db8::/32`,
- email: `user@example.com`,
- MAC: `00:00:5E:00:53:00`.

## Scan workflow

1. Read repo instructions such as `AGENTS.md`.
2. Determine publication target: public GitHub, private GitHub, package
   registry, release artifact, or internal-only PR.
3. Build the file set from `git ls-files` plus relevant untracked files the
   user intends to commit.
4. Search content and filenames for the finding categories above.
5. Classify each hit as allowed, redact, generalize, or ask-for-confirmation.
6. For each redact/generalize item, propose the replacement before editing
   unless the user already asked for remediation.
7. Apply replacements with the smallest change that preserves meaning.
8. Re-run the scans and the relevant format/lint checks for edited files.

Useful starting scans:

```bash
git ls-files -z | xargs -0 rg -n -I --hidden \
  '/Users/|/home/|C:\\Users\\|/private/var/|/Volumes/'
```

```bash
git ls-files -z | xargs -0 rg -n -I --hidden \
  '([0-9]{1,3}\.){3}[0-9]{1,3}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
```

```bash
git ls-files -z | xargs -0 rg -n -I --hidden \
  '(token|secret|password|passwd|api[_-]?key|authorization|bearer|cookie|dsn|webhook)'
```

Also inspect filenames:

```bash
git ls-files | rg '/Users/|/home/|C:\\Users\\|[0-9]{1,3}(\.[0-9]{1,3}){3}|@'
```

These scans are starting points, not a complete proof. Add targeted searches
for known user names, hostnames, domains, device names, and project-specific
config keys discovered in the repository.

## Remediation rules

- Replace home paths with `~`, `$HOME`, `<repo-root>`, or `/path/to/project`.
- Replace real hostnames with `<host>`, `<gateway-host>`, or
  `example.local`.
- Replace real IPs with RFC documentation addresses unless the project
  intentionally documents localhost or wildcard binds such as `127.0.0.1` or
  `0.0.0.0`.
- Replace real emails with `user@example.com`, except public maintainer email
  in package/license/README author contexts.
- Replace real secrets with placeholders such as `CHANGE_ME`,
  `<api-token>`, or `${ENV_VAR_NAME}`.
- Replace machine-specific usernames with `<user>`, `$USER`, or
  `${USER}`.
- Replace real device identifiers with stable examples such as
  `device_001`, `AA:BB:CC:DD:EE:FF`, or the RFC MAC example.
- Remove copied terminal prompts when the prompt reveals username, hostname,
  current directory, or local shell configuration.

Do not silently rewrite valid public identity metadata. If the same string is
both a public identity and a suspected accidental leak, preserve it only in the
allowed contexts and report the ambiguity.

## Output requirements

When reviewing only, return:

- publication target and file scope,
- findings grouped as `redact`, `generalize`, `allowed`, and `needs decision`,
- exact file and line references,
- recommended replacement for each non-allowed finding,
- validation gaps.

When sanitizing, return:

- files changed,
- data categories removed or generalized,
- public identity intentionally preserved,
- scans rerun,
- lint or test commands run after edits.

## Agent Learning Hook

<!-- BEGIN RECORD AGENT LEARNING HOOK -->
When this review workflow produces a real reusable finding, fix, regression, or
workflow correction, run `$record-agent-learning` before the final response.
Pass this skill name as `--source-skill`. Skip capture for clean/no-op reviews
and one-off repository trivia.
<!-- END RECORD AGENT LEARNING HOOK -->
