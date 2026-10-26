#!/usr/bin/env python3
"""Install or update an MCP server in McpOne DB (URL-first workflow)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    backup = next_backup_path(path)
    shutil.copy2(path, backup)
    return backup


def next_backup_path(path: pathlib.Path) -> pathlib.Path:
    """Choose a timestamped unused backup path without replacing prior receipts."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    suffix = 1
    while backup.exists():
        backup = path.with_name(f"{path.name}.bak-{stamp}-{suffix}")
        suffix += 1
    return backup


def backup_sqlite_database(path: pathlib.Path) -> pathlib.Path:
    """Create a consistent SQLite backup, including committed WAL contents."""
    backup = next_backup_path(path)
    source = sqlite3.connect(str(path))
    destination = sqlite3.connect(str(backup))
    try:
        source.backup(destination)
    except Exception:
        destination.close()
        source.close()
        backup.unlink(missing_ok=True)
        raise
    destination.close()
    source.close()
    shutil.copystat(path, backup)
    return backup


def streamable_http_json_entry(
    app_name: str, url: str, headers: Dict[str, str]
) -> Dict[str, object]:
    """Render the remote-server shape expected by one JSON-based agent."""
    if app_name == "Gemini CLI":
        return {"httpUrl": url, "headers": headers}
    if app_name == "Antigravity":
        return {"serverUrl": url, "headers": headers}
    return {"type": "http", "url": url, "headers": headers}


def legacy_streamable_http_json_entry(
    app_name: str, url: str, headers: Dict[str, str]
) -> Dict[str, object]:
    """Render the previous local-source shape used to prove legacy ownership."""
    if app_name == "Gemini CLI":
        return {"url": url, "headers": headers}
    return streamable_http_json_entry(app_name, url, headers)


def redact_endpoint(value: str) -> str:
    """Hide URL credentials and query/fragment values in command output."""
    try:
        parsed = urllib.parse.urlsplit(value)
        host = parsed.hostname
        if host is None:
            return "<redacted endpoint>"
        if ":" in host:
            host = f"[{host}]"
        if parsed.port is not None:
            host = f"{host}:{parsed.port}"
        return urllib.parse.urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    except ValueError:
        return "<redacted endpoint>"


def config_server_name(name: str) -> str:
    """Return a stable JSON config key from a display name."""
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower()


def target_alias_pattern(config_name: str, server_id: str) -> re.Pattern[str]:
    """Match aliases that explicitly identify this target server ID."""
    name_forms = {
        config_name,
        config_name.replace("-", "_"),
        config_name.replace("_", "-"),
        config_name.replace("-", " ").replace("_", " "),
    }
    return re.compile(
        rf"^(?:{'|'.join(re.escape(name) for name in sorted(name_forms))})(?:_id_?{re.escape(server_id)}|\[id={re.escape(server_id)}\])$",
        re.IGNORECASE,
    )


def prepare_streamable_http_json_configs(
    db_path: pathlib.Path,
    server_id: str,
    config_name: str,
    url: str,
    headers: Dict[str, str],
    app_name: str,
    cluster_name: str,
    all_active_clusters: bool,
) -> List[dict[str, object]]:
    """Validate and render every config update without writing any files."""
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(
        "SELECT ZID, ZNAME, ZTYPE, ZURL, ZHEADERS FROM ZADDEDSERVER WHERE ZTYPE='STREAMABLE_HTTP'"
    )
    remote_servers = cursor.fetchall()
    existing_server = next((item for item in remote_servers if item["ZID"] == server_id), None)
    cursor.execute(
        """
        SELECT a.ZNAME, a.ZAIAGENTJSONFILEPATH, a.ZAIAGENTJSONKEY,
               c.ZENABLEDADDEDSERVERIDSDATA, c.ZNAME AS cluster_name
          FROM ZADDEDAPP a
          JOIN ZCLUSTER c ON c.ZAPP = a.Z_PK AND c.ZID = a.ZACTIVECLUSTERID
         WHERE a.ZAIAGENTJSONFILEPATH IS NOT NULL
           AND a.ZAIAGENTJSONFILEPATH != ''
           AND a.ZNAME != 'Codex'
        """
    )
    agents = cursor.fetchall()
    connection.close()

    target_pattern = target_alias_pattern(config_name, server_id)
    alias_patterns = [target_pattern]
    if existing_server is not None:
        alias_patterns.append(
            target_alias_pattern(config_server_name(existing_server["ZNAME"]), server_id)
        )
    documents: dict[pathlib.Path, dict[str, object]] = {}
    plan: dict[pathlib.Path, dict[str, object]] = {}
    for agent in agents:
        enabled_ids = parse_blob_json(agent["ZENABLEDADDEDSERVERIDSDATA"], [])
        target_cluster = all_active_clusters or (
            agent["ZNAME"] == app_name and agent["cluster_name"] == cluster_name
        )
        if server_id not in enabled_ids and not target_cluster:
            continue

        config_path = pathlib.Path(agent["ZAIAGENTJSONFILEPATH"]).expanduser()
        if config_path.is_symlink():
            raise RuntimeError(
                f"Refusing symlinked agent config for '{agent['ZNAME']}': {config_path}"
            )
        if not config_path.is_file():
            raise RuntimeError(
                f"Agent config for '{agent['ZNAME']}' not found: {config_path}"
            )
        if config_path not in documents:
            try:
                original = config_path.read_bytes()
                document = json.loads(original.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise RuntimeError(
                    f"Cannot read valid JSON for '{agent['ZNAME']}' at {config_path}: {error}"
                ) from error
            if not isinstance(document, dict):
                raise RuntimeError(f"Agent config root is not an object: {config_path}")
            documents[config_path] = document
            plan[config_path] = {
                "path": config_path,
                "original": original,
                "apps": [],
            }
        document = documents[config_path]
        config_key = agent["ZAIAGENTJSONKEY"]
        if not isinstance(config_key, str) or not config_key:
            raise RuntimeError(f"Agent config key is missing for '{agent['ZNAME']}'")
        servers = document.setdefault(config_key, {})
        if not isinstance(servers, dict):
            raise RuntimeError(
                f"Agent config key '{config_key}' is not an object: {config_path}"
            )

        for existing_name in list(servers):
            if existing_name != config_name and any(
                pattern.fullmatch(existing_name) for pattern in alias_patterns
            ):
                del servers[existing_name]

        if existing_server is not None:
            old_name = existing_server["ZNAME"]
            old_entry = legacy_streamable_http_json_entry(
                agent["ZNAME"],
                existing_server["ZURL"],
                parse_blob_json(existing_server["ZHEADERS"], {}),
            )
            unqualified_old_names = {
                old_name.casefold(),
                config_server_name(old_name).casefold(),
                config_name.casefold(),
                config_name.replace("-", " ").casefold(),
                config_name.replace("-", "_").casefold(),
            }
            for old_config_name in list(servers):
                if (
                    old_config_name.casefold() in unqualified_old_names
                    and servers[old_config_name] == old_entry
                ):
                    del servers[old_config_name]

        # Repair explicitly ID-qualified legacy records only; matching on a
        # display name alone could overwrite an unrelated user-managed server.
        for remote_server in remote_servers:
            remote_id = remote_server["ZID"]
            if remote_id == server_id:
                continue
            matching_names = [
                existing_name
                for existing_name in servers
                if target_alias_pattern(config_server_name(remote_server["ZNAME"]), remote_id).fullmatch(existing_name)
            ]
            for existing_name in matching_names:
                servers[existing_name] = streamable_http_json_entry(
                    agent["ZNAME"],
                    remote_server["ZURL"],
                    parse_blob_json(remote_server["ZHEADERS"], {}),
                )

        rendered = streamable_http_json_entry(
            agent["ZNAME"],
            url,
            headers,
        )
        if config_name in servers and servers[config_name] != rendered:
            old_entry_matches_target = False
            if (
                existing_server is not None
                and existing_server["ZTYPE"] == "STREAMABLE_HTTP"
            ):
                old_entry = legacy_streamable_http_json_entry(
                    agent["ZNAME"],
                    existing_server["ZURL"],
                    parse_blob_json(existing_server["ZHEADERS"], {}),
                )
                old_entry_matches_target = servers[config_name] == old_entry
            if not old_entry_matches_target:
                raise RuntimeError(
                    f"Refusing to replace same-name config entry without matching ID alias: {config_path}#{config_key}.{config_name}"
                )
        servers[config_name] = rendered
        plan[config_path]["apps"].append(agent["ZNAME"])

    for config_path, item in plan.items():
        item["rendered"] = json.dumps(
            documents[config_path], ensure_ascii=False, indent=2
        ) + "\n"
    return list(plan.values())


def apply_streamable_http_json_configs(
    plan: List[dict[str, object]],
) -> List[tuple[str, pathlib.Path, pathlib.Path]]:
    """Back up and replace planned configs, restoring earlier files on failure."""
    prepared: list[tuple[pathlib.Path, pathlib.Path, pathlib.Path, str]] = []
    replaced: list[tuple[pathlib.Path, pathlib.Path]] = []
    try:
        for item in plan:
            path = item["path"]
            assert isinstance(path, pathlib.Path)
            if path.is_symlink() or path.read_bytes() != item["original"]:
                raise RuntimeError(
                    f"Agent config changed after preflight; refusing to overwrite: {path}"
                )
        for item in plan:
            path = item["path"]
            assert isinstance(path, pathlib.Path)
            backup = backup_file(path)
            temporary = path.with_name(
                f".{path.name}.mcpone-{os.getpid()}-{len(prepared)}.tmp"
            )
            prepared.append((path, temporary, backup, ", ".join(item["apps"])))
            temporary.write_text(str(item["rendered"]), encoding="utf-8")
            os.chmod(temporary, path.stat().st_mode & 0o777)
        for path, _, _, _ in prepared:
            item = next(entry for entry in plan if entry["path"] == path)
            if path.is_symlink() or path.read_bytes() != item["original"]:
                raise RuntimeError(
                    f"Agent config changed after preflight; refusing to overwrite: {path}"
                )
        for path, temporary, backup, _ in prepared:
            os.replace(temporary, path)
            replaced.append((path, backup))
        return [(apps, path, backup) for path, _, backup, apps in prepared]
    except Exception as error:
        rollback_errors = []
        for path, backup in reversed(replaced):
            try:
                shutil.copy2(backup, path)
            except OSError as rollback_error:
                rollback_errors.append(f"{path}: {rollback_error} (backup: {backup})")
        for _, temporary, _, _ in prepared:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        if rollback_errors:
            raise RuntimeError(
                f"Config sync failed ({error}); restore these files from backups: {'; '.join(rollback_errors)}"
            ) from error
        raise RuntimeError(f"Config sync failed and prior files were restored: {error}") from error


def restore_streamable_http_json_configs(
    files: List[tuple[str, pathlib.Path, pathlib.Path]],
) -> None:
    """Restore already-written JSON files from their retained backups."""
    failures = []
    for _, path, backup in reversed(files):
        try:
            shutil.copy2(backup, path)
        except OSError as error:
            failures.append(f"{path}: {error} (backup: {backup})")
    if failures:
        raise RuntimeError("Restore configs from backups: " + "; ".join(failures))


def parse_blob_json(blob: bytes | None, default):
    if not blob:
        return default
    try:
        text = blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else str(blob)
        return json.loads(text)
    except Exception:
        return default


def parse_key_values(values: List[str], option: str) -> Dict[str, str]:
    parsed = {}
    for index, item in enumerate(values, 1):
        if "=" not in item:
            raise ValueError(f"Invalid {option} item {index}; expected KEY=VALUE")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"Invalid {option} item {index}; key must not be empty")
        parsed[k] = v
    return parsed


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
    headers: Dict[str, str],
    url: str,
    source: str,
    server_type: str,
    version: str,
    app_name: str,
    cluster_name: str,
    all_active_clusters: bool,
    config_plan: Optional[List[dict[str, object]]] = None,
) -> tuple[List[str], List[tuple[str, pathlib.Path, pathlib.Path]]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if all_active_clusters:
        cur.execute(
            """
            SELECT c.Z_PK, c.ZENABLEDADDEDSERVERIDSDATA,
                   a.ZNAME AS app_name, c.ZNAME AS cluster_name
              FROM ZCLUSTER c
              JOIN ZADDEDAPP a ON a.Z_PK = c.ZAPP
             WHERE c.ZID = a.ZACTIVECLUSTERID
            """
        )
        clusters = cur.fetchall()
        if not clusters:
            raise RuntimeError("No active McpOne clusters found")
    else:
        cur.execute("SELECT Z_PK FROM ZADDEDAPP WHERE ZNAME=?", (app_name,))
        app = cur.fetchone()
        if app is None:
            raise RuntimeError(f"McpOne app '{app_name}' not found in ZADDEDAPP")

        cur.execute(
            """
            SELECT Z_PK, ZENABLEDADDEDSERVERIDSDATA,
                   ? AS app_name, ZNAME AS cluster_name
              FROM ZCLUSTER
             WHERE ZAPP=? AND ZNAME=?
            """,
            (app_name, app["Z_PK"], cluster_name),
        )
        clusters = cur.fetchall()
        if not clusters:
            raise RuntimeError(f"Cluster '{cluster_name}' not found for app '{app_name}'")

    zargs = json.dumps(args).encode("utf-8")
    zenv = json.dumps(env).encode("utf-8")
    zheaders = json.dumps(headers).encode("utf-8")
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
              ZARGS,ZPARAMETERS,ZENV,ZHEADERS
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                url,
                version,
                zargs,
                zparams,
                zenv,
                zheaders,
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
                   ZURL = ?,
                   ZVERSION = ?,
                   ZARGS = ?,
                   ZPARAMETERS = ?,
                   ZENV = ?,
                   ZHEADERS = ?
             WHERE ZID = ?
            """,
            (
                now,
                command,
                name,
                source,
                server_type,
                url,
                version,
                zargs,
                zparams,
                zenv,
                zheaders,
                server_id,
            ),
        )

    enabled_cluster_names = []
    for cluster in clusters:
        enabled_ids = parse_blob_json(cluster["ZENABLEDADDEDSERVERIDSDATA"], [])
        if server_id not in enabled_ids:
            enabled_ids.append(server_id)
            blob = json.dumps(enabled_ids).encode("utf-8")
            cur.execute(
                "UPDATE ZCLUSTER SET Z_OPT = Z_OPT + 1, ZUPDATEDAT = ?, ZENABLEDADDEDSERVERIDSDATA = ? WHERE Z_PK = ?",
                (now, blob, cluster["Z_PK"]),
            )
        enabled_cluster_names.append(f"{cluster['app_name']} -> {cluster['cluster_name']}")

    applied_configs = []
    try:
        if config_plan:
            applied_configs = apply_streamable_http_json_configs(config_plan)
        conn.commit()
    except Exception as error:
        conn.rollback()
        try:
            restore_streamable_http_json_configs(applied_configs)
        except RuntimeError as restore_error:
            conn.close()
            raise RuntimeError(f"Database transaction rolled back; {restore_error}") from error
        conn.close()
        raise
    conn.close()
    return enabled_cluster_names, applied_configs


def main() -> int:
    parser = argparse.ArgumentParser(description="Install/update MCP server in McpOne only")
    parser.add_argument("--url", help="MCP docs/repo/package URL (preferred)")
    parser.add_argument("--server-url", help="Streamable HTTP MCP endpoint URL")
    parser.add_argument("--name", help="Display name (optional; inferred from URL)")
    parser.add_argument("--id", help="6-char MCP id (optional; auto-generated if omitted)")
    parser.add_argument("--command", help="Server command path/name (optional if --url is enough)")
    parser.add_argument("--arg", action="append", default=[], help="Server arg (repeatable)")
    parser.add_argument("--env", action="append", default=[], help="Env var KEY=VALUE (repeatable)")
    parser.add_argument("--header", action="append", default=[], help="HTTP header KEY=VALUE (repeatable)")
    parser.add_argument("--source", default="imported", help="McpOne source value")
    parser.add_argument("--type", default="STDIO", help="McpOne transport type")
    parser.add_argument("--version", default="1.0.0", help="McpOne version label")
    parser.add_argument("--mcpone-db", default=str(DEFAULT_MCPONE_DB))
    parser.add_argument("--app-name", default="Codex")
    parser.add_argument("--cluster-name", default="Cluster A")
    parser.add_argument(
        "--all-active-clusters",
        action="store_true",
        help="Enable the server in every agent's active cluster",
    )
    parser.add_argument(
        "--sync-json-agent-configs",
        action="store_true",
        help="Merge a Streamable HTTP server into enabled JSON agent configs",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print inferred values and exit")

    args = parser.parse_args()

    if not args.url and not args.command and not args.server_url:
        print("error: provide --url, --server-url, or --command", file=sys.stderr)
        return 2

    if args.server_url and (args.command or args.url):
        print(
            "error: --server-url is mutually exclusive with --url and --command",
            file=sys.stderr,
        )
        return 2

    if args.sync_json_agent_configs and not args.server_url:
        print(
            "error: --sync-json-agent-configs requires --server-url",
            file=sys.stderr,
        )
        return 2

    inferred_name = None
    inferred_command = args.command or ("" if args.server_url else None)
    inferred_args = list(args.arg)

    if args.url and (not args.command):
        inferred_name, inferred_command, inferred_args = infer_from_url(args.url)

    if inferred_command is None:
        print("error: could not determine command", file=sys.stderr)
        return 2

    final_name = args.name or inferred_name or normalize_name_from_slug(
        pathlib.PurePosixPath((args.server_url or args.url or "mcp-server")).name
    )

    if args.id:
        server_id = args.id.strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{6}", server_id):
            print("error: --id must be exactly 6 uppercase alphanumeric characters", file=sys.stderr)
            return 2
    else:
        seed = (
            f"{final_name}|{args.server_url or args.url or ''}|"
            f"{inferred_command}|{' '.join(inferred_args)}"
        )
        server_id = generate_id(seed)

    mcpone_db = pathlib.Path(args.mcpone_db).expanduser()
    if not mcpone_db.exists():
        print(f"error: McpOne DB not found: {mcpone_db}", file=sys.stderr)
        return 2

    env = parse_key_values(args.env, "--env")
    headers = parse_key_values(args.header, "--header")
    server_type = "STREAMABLE_HTTP" if args.server_url else args.type

    if args.dry_run:
        print("Dry run")
        print(f"name={final_name}")
        print(f"id={server_id}")
        print(f"command={inferred_command}")
        print(f"url={redact_endpoint(args.server_url) if args.server_url else ''}")
        print(f"args={json.dumps(inferred_args)}")
        print(f"env_names={json.dumps(sorted(env))}")
        print(f"header_names={json.dumps(sorted(headers))}")
        print(f"type={server_type}")
        print(f"all_active_clusters={args.all_active_clusters}")
        print(f"sync_json_agent_configs={args.sync_json_agent_configs}")
        print(f"mcpone_db={mcpone_db}")
        return 0

    config_plan = None
    if args.sync_json_agent_configs:
        config_plan = prepare_streamable_http_json_configs(
            mcpone_db,
            server_id,
            config_server_name(final_name),
            args.server_url,
            headers,
            args.app_name,
            args.cluster_name,
            args.all_active_clusters,
        )

    db_backup = backup_sqlite_database(mcpone_db)

    enabled_clusters, synced_configs = upsert_mcpone(
        mcpone_db,
        server_id,
        final_name,
        inferred_command,
        inferred_args,
        env,
        headers,
        args.server_url or "",
        args.source,
        server_type,
        args.version,
        args.app_name,
        args.cluster_name,
        args.all_active_clusters,
        config_plan,
    )

    print("Installed MCP server in McpOne")
    print(f"name={final_name}")
    print(f"id={server_id}")
    print(f"command={inferred_command}")
    print(f"url={redact_endpoint(args.server_url) if args.server_url else ''}")
    print(f"args={json.dumps(inferred_args)}")
    print(f"enabled_clusters={json.dumps(enabled_clusters)}")
    print(f"mcpone_db={mcpone_db}")
    print(f"backup_mcpone={db_backup}")
    if config_plan is not None:
        print(
            "synced_json_configs="
            + json.dumps([f"{apps} ({backup})" for apps, _, backup in synced_configs])
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
