#!/usr/bin/env python3
"""Create a git tag and GitHub release from an already prepared CHANGELOG.

Usage:
  create_release.py [--version 0.1.2] [--changelog CHANGELOG.md] [--no-latest]

Requires:
  - git
  - gh CLI authenticated
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import re


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Command failed: " + " ".join(cmd))
    return result.stdout.strip()


def repo_root() -> Path:
    root = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    return Path(root)


def ensure_clean_worktree(root: Path) -> None:
    if run(["git", "status", "--porcelain"], root):
        raise RuntimeError("Working tree is dirty; commit or stash changes before creating a release")


def ensure_synced_with_upstream(root: Path) -> tuple[str, str, str]:
    branch = run(["git", "branch", "--show-current"], root)
    if not branch:
        raise RuntimeError("Detached HEAD; check out a branch with an upstream before releasing")

    upstream_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if upstream_result.returncode != 0:
        raise RuntimeError(
            f"Branch {branch} has no upstream; push it or set an upstream before releasing"
        )

    upstream = upstream_result.stdout.strip()
    remote = upstream.split("/", 1)[0]
    run(["git", "fetch", "--tags", "--prune", remote], root)

    head = run(["git", "rev-parse", "HEAD"], root)
    upstream_head = run(["git", "rev-parse", "@{u}"], root)
    if head != upstream_head:
        ahead_behind = run(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], root)
        ahead, behind = ahead_behind.split()
        raise RuntimeError(
            f"Branch {branch} is not synchronized with {upstream} "
            f"(ahead {ahead}, behind {behind})"
        )

    return branch, upstream, remote


def latest_concrete_version(changelog: Path) -> str:
    text = changelog.read_text()
    matches = re.findall(r"^## \[(?!Unreleased\])([^\]]+)\]", text, re.M)
    if not matches:
        raise RuntimeError("No concrete release section found in changelog")
    return matches[0]


def infer_release_version(changelog: Path) -> str:
    return latest_concrete_version(changelog)


def extract_release_notes(changelog: Path, version: str) -> str:
    text = changelog.read_text()
    pattern = rf"## \[{re.escape(version)}\].*?(?=\n## \[|\Z)"
    m = re.search(pattern, text, re.S)
    if not m:
        raise RuntimeError(f"Version {version} not found in changelog")
    section = m.group(0).strip().splitlines()[1:]
    notes = "\n".join(section).strip()
    if not notes:
        raise RuntimeError(f"Version {version} exists in changelog but has no release notes")
    return notes


def tag_commit(root: Path, tag: str) -> str | None:
    if not run(["git", "tag", "-l", tag], root):
        return None
    return run(["git", "rev-list", "-n", "1", tag], root)


def remote_tag_exists(root: Path, remote: str, tag: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--tags", remote, f"refs/tags/{tag}"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 2:
        return False
    raise RuntimeError(result.stderr.strip() or f"Could not inspect remote tag {tag}")


def ensure_tag(root: Path, remote: str, tag: str, version: str) -> None:
    head = run(["git", "rev-parse", "HEAD"], root)
    existing_commit = tag_commit(root, tag)
    if existing_commit and existing_commit != head:
        raise RuntimeError(
            f"Existing tag {tag} points to {existing_commit}, not current HEAD {head}"
        )

    if not existing_commit:
        run(["git", "tag", "-a", tag, "-m", f"Release {version}"], root)

    if not remote_tag_exists(root, remote, tag):
        run(["git", "push", remote, tag], root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version")
    parser.add_argument("--changelog", default="CHANGELOG.md")
    parser.add_argument(
        "--latest",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Mark the release as latest (default: true)",
    )
    args = parser.parse_args()

    root = repo_root()
    ensure_clean_worktree(root)
    branch, upstream, remote = ensure_synced_with_upstream(root)
    changelog = root / args.changelog
    if not changelog.exists():
        raise RuntimeError(f"Changelog not found: {changelog}")

    version = args.version or infer_release_version(changelog)
    tag = f"v{version}"
    notes = extract_release_notes(changelog, version)
    ensure_tag(root, remote, tag, version)

    # Create or update release
    # If release exists, edit notes; otherwise create.
    try:
        run(["gh", "release", "view", tag], root)
        cmd = ["gh", "release", "edit", tag, "--title", version, "--notes", notes]
        if args.latest:
            cmd.append("--latest")
        run(cmd, root)
    except Exception:
        cmd = [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            version,
            "--notes",
            notes,
            "--verify-tag",
        ]
        if args.latest:
            cmd.append("--latest")
        else:
            cmd.append("--latest=false")
        run(cmd, root)

    release_url = run(["gh", "release", "view", tag, "--json", "url", "--jq", ".url"], root)
    head = run(["git", "rev-parse", "HEAD"], root)
    print(f"Release: {release_url}")
    print(f"Version: {version}")
    print(f"Tag: {tag}")
    print(f"Commit: {head}")
    print(f"Branch: {branch}")
    print(f"Upstream: {upstream}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
