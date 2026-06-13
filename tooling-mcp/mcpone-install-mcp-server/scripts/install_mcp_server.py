#!/usr/bin/env python3
"""Install or update an MCP server in McpOne DB (URL-first workflow)."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shlex
import shutil
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

DEFAULT_MCPONE_DB = (
    pathlib.Path.home()
    / "Library/Containers/com.ryankolter9.McpOne/Data/Library/Application Support/McpOne/McpOne.sqlite"
)


def apple_timestamp_now() -> float:
    return time.time() - 978307200.0


def backup_file(path: pathlib.Path) -> pathlib.Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, backup)
    return backup


def parse_blob_json(blob: bytes | None, default):
    if not blob:
        return default
    try:
        text = blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else str(blob)
        return json.loads(text)
    except Exception:
        return default


def parse_env(values: List[str]) -> Dict[str, str]:
    env = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Invalid --env '{item}', expected KEY=VALUE")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"Invalid --env '{item}', empty key")
        env[k] = v
    return env


def titleize(raw: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", raw).strip()
    if not cleaned:
        return "MCP Server"
    words = [w for w in cleaned.split() if w]
    return " ".join(w[:1].upper() + w[1:] for w in words)


def normalize_name_from_slug(slug: str) -> str:
    slug = re.sub(r"\.git$", "", slug, flags=re.IGNORECASE)
    slug = re.sub(r"(^|[-_])(mcp|server)([-_]|$)", " ", slug, flags=re.IGNORECASE)
    slug = re.sub(r"\s+", " ", slug).strip()
    return titleize(slug or "MCP Server")


def base36(num: int) -> str:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return "0"
    out = []
    while num > 0:
        num, rem = divmod(num, 36)
        out.append(chars[rem])
    return "".join(reversed(out))


def generate_id(seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).digest()
    value = int.from_bytes(digest[:6], "big")
    return base36(value).upper().rjust(6, "0")[:6]


def fetch_text(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "mcpone-installer/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        data = resp.read()
        return data.decode(charset, errors="replace")


def extract_command_candidate(text: str) -> Optional[str]:
    fences = re.findall(r"```(?:bash|sh|zsh|shell)?\n(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    candidates: List[str] = []

    for block in fences:
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"^\$\s*", "", line)
            if any(line.startswith(prefix) for prefix in ("npx ", "uvx ", "docker run", "python ", "python3 ")):
                candidates.append(line)

    if not candidates:
        inline = re.findall(r"(?:^|\n)\s*(npx\s+[^\n`]+|uvx\s+[^\n`]+|docker\s+run\s+[^\n`]+)", text, flags=re.IGNORECASE)
        candidates.extend([c.strip() for c in inline])

    if not candidates:
        return None

    for c in candidates:
        if "mcp" in c.lower():
            return c
    return candidates[0]


def parse_command_line(line: str) -> Tuple[str, List[str]]:
    parts = shlex.split(line)
    if not parts:
        raise ValueError("Unable to parse command line")
    return parts[0], parts[1:]


def infer_from_url(url: str) -> Tuple[str, str, List[str]]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    # Special-case iMCP app server
    if "github.com/loopwork/imcp" in url.lower() or url.lower().endswith("/imcp"):
        return "iMCP", "/Applications/iMCP.app/Contents/MacOS/imcp-server", []

    # Try documentation command extraction first
    text_candidates = [url]
    if "github.com" in host:
        parts = path.split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            text_candidates.extend(
                [
                    f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
                    f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md",
                ]
            )

    extracted_cmd: Optional[Tuple[str, List[str]]] = None
    for candidate_url in text_candidates:
        try:
            content = fetch_text(candidate_url)
        except Exception:
            continue
        line = extract_command_candidate(content)
        if line:
            try:
                extracted_cmd = parse_command_line(line)
                break
            except Exception:
                pass

    # Heuristics for package URLs
    if "npmjs.com" in host and (path.startswith("package/") or "/package/" in path):
        pkg = path.split("package/", 1)[1].split("/")[0]
        name = normalize_name_from_slug(pkg)
        return name, "npx", ["-y", pkg]

    if "pypi.org" in host and (path.startswith("project/") or "/project/" in path):
        pkg = path.split("project/", 1)[1].split("/")[0]
        name = normalize_name_from_slug(pkg)
        return name, "uvx", [pkg]

    if extracted_cmd:
        cmd, args = extracted_cmd
        if "github.com" in host and path:
            repo = path.split("/")[1] if len(path.split("/")) >= 2 else path.split("/")[-1]
            name = normalize_name_from_slug(repo)
        else:
            tail = path.split("/")[-1] if path else host
            name = normalize_name_from_slug(tail)
        return name, cmd, args

    # Fallback based on GitHub repo slug
    if "github.com" in host and path:
        parts = path.split("/")
        if len(parts) >= 2:
            repo = parts[1]
            name = normalize_name_from_slug(repo)
            guessed_pkg = re.sub(r"\.git$", "", repo, flags=re.IGNORECASE)
            return name, "npx", ["-y", guessed_pkg]

    raise RuntimeError("Could not infer install command from URL. Provide --command/--arg explicitly.")


def upsert_mcpone(
    db_path: pathlib.Path,
    server_id: str,
    name: str,
    command: str,
    args: List[str],
    env: Dict[str, str],
    source: str,
    server_type: str,
    version: str,
    app_name: str,
    cluster_name: str,
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT Z_PK FROM ZADDEDAPP WHERE ZNAME=?", (app_name,))
    app = cur.fetchone()
    if app is None:
        raise RuntimeError(f"McpOne app '{app_name}' not found in ZADDEDAPP")

    cur.execute(
        "SELECT Z_PK, ZENABLEDADDEDSERVERIDSDATA FROM ZCLUSTER WHERE ZAPP=? AND ZNAME=?",
        (app["Z_PK"], cluster_name),
    )
    cluster = cur.fetchone()
    if cluster is None:
        raise RuntimeError(f"Cluster '{cluster_name}' not found for app '{app_name}'")

    zargs = json.dumps(args).encode("utf-8")
    zenv = json.dumps(env).encode("utf-8")
    zparams = b"{}"
    now = apple_timestamp_now()

    cur.execute("SELECT Z_PK FROM ZADDEDSERVER WHERE ZID=?", (server_id,))
    existing = cur.fetchone()

    if existing is None:
        cur.execute("SELECT COALESCE(MAX(Z_PK), 0) + 1 AS next_pk FROM ZADDEDSERVER")
        next_pk = int(cur.fetchone()["next_pk"])
        cur.execute(
            """
            INSERT INTO ZADDEDSERVER (
              Z_PK,Z_ENT,Z_OPT,ZCREATEDAT,ZUPDATEDAT,
              ZCOMMAND,ZID,ZNAME,ZSERVERID,ZSOURCE,ZTYPE,ZURL,ZVERSION,
              ZARGS,ZPARAMETERS,ZENV
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                next_pk,
                2,
                1,
                now,
                now,
                command,
                server_id,
                name,
                "",
                source,
                server_type,
                "",
                version,
                zargs,
                zparams,
                zenv,
            ),
        )
        cur.execute(
            "UPDATE Z_PRIMARYKEY SET Z_MAX = CASE WHEN Z_MAX < ? THEN ? ELSE Z_MAX END WHERE Z_ENT = 2",
            (next_pk, next_pk),
        )
    else:
        cur.execute(
            """
            UPDATE ZADDEDSERVER
               SET Z_OPT = Z_OPT + 1,
                   ZUPDATEDAT = ?,
                   ZCOMMAND = ?,
                   ZNAME = ?,
                   ZSOURCE = ?,
                   ZTYPE = ?,
                   ZVERSION = ?,
                   ZARGS = ?,
                   ZPARAMETERS = ?,
                   ZENV = ?
             WHERE ZID = ?
            """,
            (now, command, name, source, server_type, version, zargs, zparams, zenv, server_id),
        )

    enabled_ids = parse_blob_json(cluster["ZENABLEDADDEDSERVERIDSDATA"], [])
    if server_id not in enabled_ids:
        enabled_ids.append(server_id)
        blob = json.dumps(enabled_ids).encode("utf-8")
        cur.execute(
            "UPDATE ZCLUSTER SET Z_OPT = Z_OPT + 1, ZUPDATEDAT = ?, ZENABLEDADDEDSERVERIDSDATA = ? WHERE Z_PK = ?",
            (now, blob, cluster["Z_PK"]),
        )

    conn.commit()
    conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/update MCP server in McpOne only")
    parser.add_argument("--url", help="MCP docs/repo/package URL (preferred)")
    parser.add_argument("--name", help="Display name (optional; inferred from URL)")
    parser.add_argument("--id", help="6-char MCP id (optional; auto-generated if omitted)")
    parser.add_argument("--command", help="Server command path/name (optional if --url is enough)")
    parser.add_argument("--arg", action="append", default=[], help="Server arg (repeatable)")
    parser.add_argument("--env", action="append", default=[], help="Env var KEY=VALUE (repeatable)")
    parser.add_argument("--source", default="imported", help="McpOne source value")
    parser.add_argument("--type", default="STDIO", help="McpOne transport type")
    parser.add_argument("--version", default="1.0.0", help="McpOne version label")
    parser.add_argument("--mcpone-db", default=str(DEFAULT_MCPONE_DB))
    parser.add_argument("--app-name", default="Codex")
    parser.add_argument("--cluster-name", default="Cluster A")
    parser.add_argument("--dry-run", action="store_true", help="Print inferred values and exit")

    args = parser.parse_args()

    if not args.url and not args.command:
        print("error: provide --url or --command", file=sys.stderr)
        return 2

    inferred_name = None
    inferred_command = args.command
    inferred_args = list(args.arg)

    if args.url and (not args.command):
        inferred_name, inferred_command, inferred_args = infer_from_url(args.url)

    if not inferred_command:
        print("error: could not determine command", file=sys.stderr)
        return 2

    final_name = args.name or inferred_name or normalize_name_from_slug(pathlib.PurePosixPath((args.url or "mcp-server")).name)

    if args.id:
        server_id = args.id.strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{6}", server_id):
            print("error: --id must be exactly 6 uppercase alphanumeric characters", file=sys.stderr)
            return 2
    else:
        seed = f"{final_name}|{args.url or ''}|{inferred_command}|{' '.join(inferred_args)}"
        server_id = generate_id(seed)

    mcpone_db = pathlib.Path(args.mcpone_db).expanduser()
    if not mcpone_db.exists():
        print(f"error: McpOne DB not found: {mcpone_db}", file=sys.stderr)
        return 2

    env = parse_env(args.env)

    if args.dry_run:
        print("Dry run")
        print(f"name={final_name}")
        print(f"id={server_id}")
        print(f"command={inferred_command}")
        print(f"args={json.dumps(inferred_args)}")
        print(f"env={json.dumps(env)}")
        print(f"mcpone_db={mcpone_db}")
        return 0

    db_backup = backup_file(mcpone_db)

    upsert_mcpone(
        mcpone_db,
        server_id,
        final_name,
        inferred_command,
        inferred_args,
        env,
        args.source,
        args.type,
        args.version,
        args.app_name,
        args.cluster_name,
    )

    print("Installed MCP server in McpOne")
    print(f"name={final_name}")
    print(f"id={server_id}")
    print(f"command={inferred_command}")
    print(f"args={json.dumps(inferred_args)}")
    print(f"mcpone_db={mcpone_db}")
    print(f"backup_mcpone={db_backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
