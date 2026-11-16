#!/usr/bin/env python3
"""Read-only preparation and verification for native Codex project moves."""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def destination(inventory, requested, host):
    require(isinstance(inventory, dict) and isinstance(inventory.get("projects"), list),
            "Expected a complete native list_projects result")
    require(not inventory.get("unavailableHosts") and not inventory.get("unavailableSources"),
            "Project inventory is incomplete; refresh it before moving")
    matches = []
    for project in inventory["projects"]:
        require(isinstance(project, dict), "Malformed project inventory entry")
        if project.get("projectKind") != "local" or project.get("hostId") != host:
            continue
        path = project.get("path")
        if (requested == project.get("projectId") or requested == project.get("label")
                or (path and Path(requested).is_absolute()
                    and Path(requested).expanduser().resolve() == Path(path).expanduser().resolve())):
            require(project.get("projectId") and path, "Incomplete project identity")
            matches.append(project)
    require(len(matches) == 1, "Destination missing or ambiguous in current app inventory")
    require(Path(matches[0]["path"]).expanduser().is_dir(), "Destination directory unavailable")
    return matches[0]


def execution(home, thread):
    require(thread.get("kind") == "codex" and thread.get("hostId") == "local",
            "This verifier supports local Codex chats only")
    require(thread.get("id") and thread.get("cwd"), "Missing thread identity or cwd")
    db = home / "sqlite/state_5.sqlite"
    if not db.is_file():
        db = home / "state_5.sqlite"
    require(db.is_file(), "Codex database unavailable; no state was created")
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        row = connection.execute("SELECT cwd, rollout_path FROM threads WHERE id = ?",
                                 (thread["id"],)).fetchone()
    require(row is not None and row[0] == thread["cwd"], "App/database identity mismatch")
    cwd, rollout = row
    require(Path(cwd).is_dir(), "Execution directory unavailable")
    git = subprocess.run(["git", "-C", cwd, "rev-parse", "--absolute-git-dir",
                          "--git-common-dir", "HEAD"], capture_output=True, text=True)
    worktree = git.stdout.splitlines() if git.returncode == 0 else None
    # A .git entry means failed Git inspection is unavailable evidence, not a non-Git chat.
    require(git.returncode == 0 or not any((p / ".git").exists()
            for p in [Path(cwd), *Path(cwd).parents]), "Git identity inspection failed")
    return {"id": thread["id"], "hostId": thread["hostId"], "cwd": cwd,
            "rollout_path": rollout,
            "rollout_sha256": hashlib.sha256(Path(rollout).read_bytes()).hexdigest(),
            "worktree": worktree}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread-json", required=True, help="Fresh exact thread record from list_threads")
    parser.add_argument("--projects-json", help="Fresh list_projects result")
    parser.add_argument("--dest-project", help="Exact project ID, label or full path")
    parser.add_argument("--before-json", help="Verify against a saved preview JSON")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home()/".codex")))
    parser.add_argument("--apply", action="store_true", help="Unsupported: use the native app control")
    args = parser.parse_args(argv)
    require(not args.apply, "No private metadata writes: use move_thread_to_project or the sidebar")
    thread = read_json(args.thread_json)
    current = execution(Path(args.codex_home).expanduser(), thread)
    if args.before_json:
        before = read_json(args.before_json)
        require(before.get("schema") == 1 and before.get("mode") == "membership-only", "Invalid snapshot")
        require(current == before.get("execution"), "Execution context changed; do not report a successful move")
        require(thread.get("projectId") == before["destination"]["projectId"],
                "Destination membership not proven; reconcile before any retry")
        print(json.dumps({"status": "verified", "execution": current,
                          "projectId": thread["projectId"]}, indent=2))
    else:
        require(args.projects_json and args.dest_project, "Preview requires current project inventory and destination")
        project = destination(read_json(args.projects_json), args.dest_project, thread["hostId"])
        require(thread.get("projectId"), "Source membership ambiguous; resolve through the app")
        print(json.dumps({"schema": 1, "mode": "membership-only", "execution": current,
                          "source_project_id": thread["projectId"],
                          "destination": {"projectId": project["projectId"], "path": project["path"]}}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
        sys.exit(str(exc))
