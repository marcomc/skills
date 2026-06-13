#!/usr/bin/env python3
"""Generate a Markdown PR description from git diff/log.

Usage:
  pr_description.py [--base main] [--head HEAD] [--max-files 50]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Command failed: " + " ".join(cmd))
    return result.stdout.strip()


def detect_repo_root() -> Path:
    try:
        root = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    except Exception as exc:
        raise RuntimeError("Not a git repository") from exc
    return Path(root)


def detect_default_base() -> str:
    # Prefer main, fallback to master if not present.
    for candidate in ("main", "master"):
        try:
            subprocess.run(["git", "rev-parse", "--verify", candidate], check=True, capture_output=True)
            return candidate
        except Exception:
            continue
    return "main"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=None)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--max-files", type=int, default=50)
    args = parser.parse_args()

    root = detect_repo_root()
    base = args.base or detect_default_base()
    head = args.head

    # Collect files changed
    diff_names = run(["git", "diff", "--name-status", f"{base}...{head}"] , root)
    files = [line for line in diff_names.splitlines() if line.strip()]

    # Collect commits
    commits = run(["git", "log", "--oneline", f"{base}..{head}"] , root)
    commit_lines = [line for line in commits.splitlines() if line.strip()]

    # Produce output
    print("## Summary")
    print("- (Fill in concise summary)\n")

    print("## Changes")
    if files:
        for line in files[: args.max_files]:
            print(f"- {line}")
        if len(files) > args.max_files:
            print(f"- ...and {len(files) - args.max_files} more files")
    else:
        print("- No file changes detected")
    print()

    print("## Testing")
    print("- Not run (add details)\n")

    print("## Notes")
    print("- (Optional)\n")

    print("## Commits")
    if commit_lines:
        for line in commit_lines:
            print(f"- {line}")
    else:
        print("- No commits found")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
