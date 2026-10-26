---
name: create-github-release
description: Use when the user asks to create, publish, cut, tag, or update a GitHub release from a local repository changelog.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Create GitHub Release

Create a git tag and a GitHub release from the changelog. This skill is generic
and can be used in any repo with `CHANGELOG.md` following Keep a Changelog
format.

This is a lightweight publication skill. Do not run `$pre-pr-review-gate`,
linting, tests, remediation loops, broad repository scans, or code-quality
checks unless the user explicitly asks for them in the release request.

## Inputs to Ask For

Ask the user for these inputs if not provided:

1. **Version** (optional): if omitted, use the latest concrete version section
   from `CHANGELOG.md`
2. **Mark as latest** (optional): default is `yes`; only ask when the user explicitly wants a non-latest release

If the user does not specify a changelog path, assume `CHANGELOG.md` at repo root.

## Workflow

1. Confirm repository root with `git rev-parse --show-toplevel`.
2. Ensure the working tree is clean (`git status --porcelain` must be empty).
3. Fetch the tracked remote and ensure current `HEAD` exactly matches the branch
   upstream. Stop if the branch is detached, has no upstream, is ahead, or is
   behind.
4. Parse `CHANGELOG.md`.
5. Audit release-history continuity before resolving the new release: compare
   concrete changelog sections, local tags, and GitHub releases. When a
   requested or documented intermediate version is absent, stop rather than
   folding its changes into a later release. Publish or explicitly account for
   each missing version first; keep any historical release non-latest unless
   the user requests otherwise.
6. Resolve the release version:
   - If `--version` is provided, require that exact concrete changelog section.
   - If no version is provided, use the latest concrete version section.
7. Stop and report the missing changelog version if the resolved section does
   not exist or has no release notes. Do not move `Unreleased` entries, edit
   files, or create commits.
8. Create an annotated git tag `v<version>` at current `HEAD` if it does not
   already exist. If it exists, require it to point to current `HEAD`.
9. Push the tag to the tracked remote if needed.
10. Create or update the GitHub release using `gh`.
11. Mark it as the latest release by default unless the user explicitly opts out.
12. Verify publication with `gh release view v<version> --json
    url,name,tagName,publishedAt`.

## Command

Use the bundled script:

```bash
~/.agents/skills/create-github-release/scripts/create_release.py
```

Optional overrides:

```bash
~/.agents/skills/create-github-release/scripts/create_release.py --version 0.1.2
~/.agents/skills/create-github-release/scripts/create_release.py --no-latest
```

## Output

- Return the release URL from `gh`.
- Report the resolved version, tag, commit SHA, branch, and upstream used for
  the release.
- If any step fails, report the error and what to fix (dirty working tree, stale
  branch, missing upstream, missing versioned changelog section, tag mismatch,
  or missing `gh` authentication).
