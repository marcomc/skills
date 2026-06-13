#!/usr/bin/env python3
"""Safely move a Codex thread between existing projects."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ThreadRecord:
    id: str
    display_title: str
    db_title: str
    cwd: str
    rollout_path: str
    updated_at: int


def codex_home_from_env(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    return Path.home() / ".codex"


def load_global_state(codex_home: Path) -> dict:
    path = codex_home / ".codex-global-state.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def candidate_project_paths(codex_home: Path) -> list[Path]:
    state = load_global_state(codex_home)
    raw_paths: list[str] = []
    raw_paths.extend(state.get("electron-saved-workspace-roots", []))
    raw_paths.extend(state.get("active-workspace-roots", []))
    raw_paths.extend(state.get("project-order", []))

    seen: set[str] = set()
    result: list[Path] = []
    for raw in raw_paths:
        path = str(Path(raw).expanduser())
        if path in seen:
            continue
        seen.add(path)
        resolved = Path(path)
        if resolved.is_dir():
            result.append(resolved)
    return result


def resolve_project(name_or_path: str, codex_home: Path) -> Path:
    requested = Path(name_or_path).expanduser()
    if requested.is_absolute():
        if requested.is_dir():
            return requested
        raise SystemExit(f"Project path does not exist: {requested}")

    candidates = candidate_project_paths(codex_home)
    exact = [path for path in candidates if path.name.casefold() == name_or_path.casefold()]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        paths = "\n".join(f"- {path}" for path in exact)
        raise SystemExit(f"Project name is ambiguous:\n{paths}")

    names = sorted({path.name for path in candidates})
    suggestions = difflib.get_close_matches(name_or_path, names, n=5, cutoff=0.4)
    if suggestions:
        suffix = "\n".join(f"- {item}" for item in suggestions)
        raise SystemExit(
            "Project does not exist. Maybe you meant one of these?\n"
            f"{suffix}\nCreate the project first or use the correct name."
        )
    raise SystemExit("Project does not exist. Create the project first or use the correct name.")


def load_session_index(codex_home: Path) -> dict[str, str]:
    path = codex_home / "session_index.jsonl"
    if not path.exists():
        return {}

    result: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            thread_id = payload.get("id")
            thread_name = payload.get("thread_name")
            if thread_id and thread_name:
                result[thread_id] = thread_name
    return result


def state_db_path(codex_home: Path) -> Path:
    sqlite_db = codex_home / "sqlite" / "state_5.sqlite"
    if sqlite_db.exists():
        return sqlite_db
    return codex_home / "state_5.sqlite"


def load_threads(codex_home: Path) -> list[ThreadRecord]:
    db_path = state_db_path(codex_home)
    session_names = load_session_index(codex_home)

    query = """
        SELECT id, title, cwd, rollout_path, updated_at
        FROM threads
        WHERE archived = 0
    """
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(query).fetchall()

    threads: list[ThreadRecord] = []
    for thread_id, title, cwd, rollout_path, updated_at in rows:
        display_title = session_names.get(thread_id, title)
        threads.append(
            ThreadRecord(
                id=thread_id,
                display_title=display_title,
                db_title=title,
                cwd=cwd,
                rollout_path=rollout_path,
                updated_at=updated_at,
            )
        )
    return threads


def filter_threads_by_source(
    threads: list[ThreadRecord], source_project: Path | None
) -> list[ThreadRecord]:
    if source_project is None:
        return threads
    return [thread for thread in threads if Path(thread.cwd) == source_project]


def resolve_thread(
    codex_home: Path, chat_title: str | None, source_project: Path | None
) -> ThreadRecord:
    threads = filter_threads_by_source(load_threads(codex_home), source_project)
    if not threads:
        raise SystemExit("No matching threads were found.")

    if not chat_title:
        latest = max(threads, key=lambda item: item.updated_at)
        return latest

    lowered = chat_title.casefold()
    exact = [thread for thread in threads if thread.display_title.casefold() == lowered]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        payload = "\n".join(
            f"- {thread.display_title} [{thread.id}] ({Path(thread.cwd).name})" for thread in exact
        )
        raise SystemExit(f"Chat title is ambiguous:\n{payload}")

    partial = [thread for thread in threads if lowered in thread.display_title.casefold()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        payload = "\n".join(
            f"- {thread.display_title} [{thread.id}] ({Path(thread.cwd).name})"
            for thread in partial[:10]
        )
        raise SystemExit(f"Chat title matches multiple threads:\n{payload}")

    names = sorted({thread.display_title for thread in threads})
    suggestions = difflib.get_close_matches(chat_title, names, n=5, cutoff=0.35)
    if suggestions:
        suffix = "\n".join(f"- {item}" for item in suggestions)
        raise SystemExit(f"Chat was not found. Maybe you meant one of these?\n{suffix}")
    raise SystemExit("Chat was not found.")


def resolve_thread_by_id(
    codex_home: Path, thread_id: str, source_project: Path | None, chat_title: str | None
) -> ThreadRecord:
    threads = filter_threads_by_source(load_threads(codex_home), source_project)
    match = next((thread for thread in threads if thread.id == thread_id), None)
    if match is None:
        raise SystemExit(f"Thread id was not found: {thread_id}")
    if chat_title and match.display_title.casefold() != chat_title.casefold():
        raise SystemExit(
            "Thread id resolved to a different title than --chat. "
            f"Resolved={match.display_title!r}, Provided={chat_title!r}"
        )
    return match


def backup_sqlite(source: Path, destination: Path) -> None:
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)


def backup_targets(codex_home: Path, thread: ThreadRecord) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = codex_home / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_path = state_db_path(codex_home)
    backup_sqlite(db_path, backup_dir / "state_5.sqlite")
    shutil.copy2(thread.rollout_path, backup_dir / Path(thread.rollout_path).name)
    return backup_dir


def update_thread_cwd(codex_home: Path, thread_id: str, destination: Path) -> None:
    db_path = state_db_path(codex_home)
    query = "UPDATE threads SET cwd = ? WHERE id = ?"
    with sqlite3.connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(query, (str(destination), thread_id))
        connection.commit()


def patch_rollout_context(rollout_path: Path, destination: Path) -> int:
    lines = rollout_path.read_text(encoding="utf-8").splitlines()
    session_meta_updates = 0
    turn_context_updates = 0
    rewritten: list[str] = []
    destination_text = str(destination)
    for line in lines:
        payload = json.loads(line)
        payload_body = payload.get("payload")
        if payload.get("type") == "session_meta":
            if not isinstance(payload_body, dict):
                raise SystemExit(f"Invalid session_meta payload in rollout file: {rollout_path}")
            payload_body["cwd"] = destination_text
            session_meta_updates += 1
        elif payload.get("type") == "turn_context" and isinstance(payload_body, dict):
            if "cwd" in payload_body:
                payload_body["cwd"] = destination_text
            if isinstance(payload_body.get("workspace_roots"), list):
                payload_body["workspace_roots"] = [destination_text]
            turn_context_updates += 1
        rewritten.append(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))

    if session_meta_updates == 0:
        raise SystemExit(f"session_meta record not found in rollout file: {rollout_path}")

    rollout_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    return turn_context_updates


def rollout_session_meta_mismatches(rollout_path: Path, destination: Path) -> list[str]:
    expected = str(destination)
    seen = False
    mismatches: list[str] = []
    with rollout_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = json.loads(line)
            if payload.get("type") == "session_meta":
                seen = True
                payload_body = payload.get("payload")
                if not isinstance(payload_body, dict) or payload_body.get("cwd") != expected:
                    cwd = payload_body.get("cwd") if isinstance(payload_body, dict) else None
                    mismatches.append(f"line {line_number}: cwd={cwd!r}")
    if not seen:
        raise SystemExit(f"session_meta record not found in rollout file: {rollout_path}")
    return mismatches


def rollout_turn_context_mismatches(rollout_path: Path, destination: Path) -> list[str]:
    expected = str(destination)
    mismatches: list[str] = []
    with rollout_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = json.loads(line)
            if payload.get("type") != "turn_context":
                continue

            payload_body = payload.get("payload")
            if not isinstance(payload_body, dict):
                continue

            if payload_body.get("cwd") != expected:
                mismatches.append(f"line {line_number}: cwd={payload_body.get('cwd')!r}")
            workspace_roots = payload_body.get("workspace_roots")
            if isinstance(workspace_roots, list) and workspace_roots != [expected]:
                mismatches.append(f"line {line_number}: workspace_roots={workspace_roots!r}")
    return mismatches


def read_thread_cwd(codex_home: Path, thread_id: str) -> str:
    db_path = state_db_path(codex_home)
    query = "SELECT cwd FROM threads WHERE id = ?"
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(query, (thread_id,)).fetchone()
    if row is None:
        raise SystemExit(f"Thread not found after update: {thread_id}")
    return row[0]


def verify(thread: ThreadRecord, codex_home: Path, destination: Path) -> None:
    db_cwd = read_thread_cwd(codex_home, thread.id)
    expected = str(destination)

    if db_cwd != expected:
        raise SystemExit(f"Verification failed: database cwd is {db_cwd}, expected {expected}")
    session_meta_mismatches = rollout_session_meta_mismatches(Path(thread.rollout_path), destination)
    if session_meta_mismatches:
        details = "\n".join(session_meta_mismatches[:10])
        raise SystemExit(f"Verification failed: rollout session_meta mismatch:\n{details}")
    turn_context_mismatches = rollout_turn_context_mismatches(Path(thread.rollout_path), destination)
    if turn_context_mismatches:
        details = "\n".join(turn_context_mismatches[:10])
        raise SystemExit(f"Verification failed: rollout turn_context mismatch:\n{details}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat", help="Visible chat title. Omit to target the current chat.")
    parser.add_argument(
        "--thread-id",
        help=(
            "Exact Codex thread id. Recommended for applying a previously previewed resolution so "
            "the target cannot drift between runs."
        ),
    )
    parser.add_argument(
        "--source-project",
        help="Current project name or full path. Optional, but recommended when titles are ambiguous.",
    )
    parser.add_argument("--dest-project", required=True, help="Destination project name or full path.")
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME"),
        help="Override Codex home. Defaults to $CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the move. Without this flag the script only previews resolution.",
    )
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    codex_home = codex_home_from_env(args.codex_home)
    destination = resolve_project(args.dest_project, codex_home)
    source_project = (
        resolve_project(args.source_project, codex_home) if args.source_project else None
    )
    thread = (
        resolve_thread_by_id(codex_home, args.thread_id, source_project, args.chat)
        if args.thread_id
        else resolve_thread(codex_home, args.chat, source_project)
    )

    preview = {
        "thread_id": thread.id,
        "chat_title": thread.display_title,
        "source_project": thread.cwd,
        "destination_project": str(destination),
        "rollout_path": thread.rollout_path,
        "mode": "apply" if args.apply else "dry-run",
    }

    if not args.apply:
        print(json.dumps(preview, indent=2))
        return 0

    backup_dir = backup_targets(codex_home, thread)
    update_thread_cwd(codex_home, thread.id, destination)
    turn_context_updates = patch_rollout_context(Path(thread.rollout_path), destination)
    verify(thread, codex_home, destination)

    result = {
        **preview,
        "backup_dir": str(backup_dir),
        "turn_context_records_updated": turn_context_updates,
        "status": "ok",
        "restart_hint": "Restart Codex Desktop if the sidebar does not refresh immediately.",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
