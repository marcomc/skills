#!/usr/bin/env python3
"""Read-only release proposals and freshness guards; never tags or publishes."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

PUBLICATION_GUARD_API = 1


class PlanError(RuntimeError):
    """A plan is ambiguous, unverifiable or stale."""


SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


def require(condition, message):
    if not condition:
        raise PlanError(message)


def run(root, *args):
    try:
        result = subprocess.run(
            args, cwd=root, capture_output=True, timeout=60, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PlanError(f"{args[0]} read unavailable; inspect tooling privately") from exc
    # Diagnostics can contain credential-bearing remote URLs. Never echo them.
    require(result.returncode == 0, f"{args[0]} read failed; inspect access privately")
    return result.stdout.decode("utf-8")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(file_path):
    return file_path.read_bytes().decode("utf-8")


def key(version):
    match = SEMVER.fullmatch(version)
    require(match is not None, f"Unsupported SemVer: {version}")
    prerelease = match[4]
    if prerelease:
        require(
            all(not (part.isdigit() and len(part) > 1 and part[0] == "0")
                for part in prerelease.split(".")),
            "Numeric prerelease identifiers must not have leading zeroes",
        )
    return tuple(int(match[i]) for i in (1, 2, 3))


def is_stable(version):
    match = SEMVER.fullmatch(version)
    return match is not None and match[4] is None


def version_of(tag, prefix):
    if not tag.startswith(prefix):
        return None
    value = tag[len(prefix):]
    if SEMVER.fullmatch(value):
        key(value)
        return value
    return None


def safe_path(root, value):
    require(isinstance(value, str) and bool(value), "Expected a relative file path")
    parts = PurePosixPath(value)
    require(
        not parts.is_absolute() and ".." not in parts.parts
        and ".git" not in parts.parts and "\\" not in value,
        "Paths must be repository-relative and outside .git",
    )
    result = root / value
    require(result.resolve().is_relative_to(root.resolve()), "Path escapes repository")
    require(not result.is_symlink(), "Planned files must not be symlinks")
    return result


def validate_config(root, config):
    require(isinstance(config, dict), "Config must be an object")
    require(set(config) <= {
        "remote", "target", "changelog", "tag_prefix", "version_sources", "github_host"
    }, "Unknown config field")
    config = {"changelog": "CHANGELOG.md", "tag_prefix": "v",
              "version_sources": [], **config}
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", config.get("remote", "")),
            "Configure a remote name")
    require(isinstance(config.get("target"), str), "Configure the authoritative target")
    run(root, "git", "check-ref-format", "refs/heads/" + config["target"])
    require(isinstance(config["tag_prefix"], str), "tag_prefix must be a string")
    paths = [config["changelog"]]
    for source in config["version_sources"]:
        require(set(source) == {"path", "pattern"}, "Version source needs path and pattern")
        paths.append(source["path"])
        pattern = re.compile(source["pattern"], re.M)
        require("version" in pattern.groupindex, "Regex needs a named version group")
    require(len(set(paths)) == len(paths), "Version source paths must be distinct")
    for value in paths:
        safe_path(root, value)
    return config


def headings(text):
    matches = list(re.finditer(r"^##[ \t]+[^\r\n]+\r?$", text, re.M))
    return [(m.group().rstrip("\r"), m.start(),
             matches[i + 1].start() if i + 1 < len(matches) else len(text), m.end())
            for i, m in enumerate(matches)]


def release_sections(text):
    releases = {}
    for title, start, end, _ in headings(text):
        match = re.match(r"##[ \t]+\[([^\]]+)\]", title)
        if match and SEMVER.fullmatch(match[1]):
            version = match[1]
            key(version)
            require(version not in releases, "Duplicate changelog version")
            releases[version] = text[start:end]
    return releases


def source_match(text, source):
    matches = list(re.finditer(source["pattern"], text, re.M))
    require(len(matches) == 1, f"Ambiguous version source: {source['path']}")
    match = matches[0]
    version = match.group("version")
    require(is_stable(version) and "+" not in version, "Version sources must contain a stable X.Y.Z")
    return match


def target_metadata(root, config, revision, todo_paths=()):
    changelog = run(root, "git", "show", f"{revision}:{config['changelog']}")
    sections = release_sections(changelog)
    stable = [v for v in sections if is_stable(v)]
    current = max(stable, key=key) if stable else None
    files = {config["changelog"]: digest(changelog)}
    contents = {config["changelog"]: changelog}
    versions = {config["changelog"]: current}
    for source in config["version_sources"]:
        text = run(root, "git", "show", f"{revision}:{source['path']}")
        files[source["path"]] = digest(text)
        contents[source["path"]] = text
        versions[source["path"]] = source_match(text, source).group("version")
    known = set(key(v) for v in versions.values() if v)
    require(len(known) <= 1, "Current target version sources disagree; reconcile first")
    for value in todo_paths:
        text = run(root, "git", "show", f"{revision}:{value}")
        files[value] = digest(text)
        contents[value] = text
    return {"files": files, "contents": contents, "versions": versions, "releases": sections}


def remote_identity(root, config):
    remote = config["remote"]
    urls = run(root, "git", "remote", "get-url", "--all", remote).splitlines()
    push_urls = run(root, "git", "remote", "get-url", "--push", "--all", remote).splitlines()
    require(len(urls) == len(push_urls) == 1, "Multiple remote destinations are ambiguous")

    def parse(value):
        if "://" in value:
            parsed = urlsplit(value)
            host, repo = parsed.hostname, parsed.path.lstrip("/")
        else:
            match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):([^:]+)", value)
            if not match:
                return None
            host, repo = match.groups()
        repo = repo.removesuffix(".git").rstrip("/")
        if not host or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            return None
        return f"{host.lower()}/{repo.lower()}"

    identity, push_identity = parse(urls[0]), parse(push_urls[0])
    same = identity == push_identity if identity else urls == push_urls
    host = identity.split("/", 1)[0] if identity else None
    github = identity if host in {"github.com", config.get("github_host")} else None
    return {"fetch_hash": digest(urls[0]), "push_hash": digest(push_urls[0]),
            "same_destination": same, "github": github}


def github_state(root, identity):
    if not identity["github"]:
        return {"status": "unavailable", "reason": "Remote GitHub identity unverified"}
    host, owner, repository = identity["github"].split("/")
    endpoint = f"repos/{owner}/{repository}"

    def api(path, *extra):
        return json.loads(run(root, "gh", "api", "--method", "GET", "--hostname", host,
                              path, *extra))

    try:
        info = api(endpoint)
        require(info["full_name"].lower() == f"{owner}/{repository}",
                "GitHub repository identity mismatch")
        pages = api(endpoint + "/releases?per_page=100", "--paginate", "--slurp")
        require(isinstance(pages, list) and all(isinstance(p, list) for p in pages),
                "Incomplete GitHub release pagination")
        records = []
        ids = set()
        for page in pages:
            for item in page:
                require(type(item["id"]) is int and item["id"] not in ids,
                        "Ambiguous GitHub release identity")
                require(type(item["draft"]) is bool and type(item["prerelease"]) is bool,
                        "Invalid GitHub release state")
                require(isinstance(item["tag_name"], str) and bool(item["tag_name"]),
                        "Missing GitHub release tag")
                require(item["draft"] or bool(item["published_at"]),
                        "Published release missing publication time")
                require(isinstance(item["updated_at"], str) and bool(item["updated_at"]),
                        "Release update identity unavailable")
                require(item["published_at"] is None or isinstance(item["published_at"], str),
                        "Invalid publication timestamp")
                ids.add(item["id"])
                records.append({name: item[name] for name in (
                    "id", "tag_name", "draft", "prerelease", "published_at", "updated_at"
                )})
        return {"status": "available", "draft_visibility":
                info.get("permissions", {}).get("push") is True,
                "releases": sorted(records, key=lambda r: r["id"])}
    except (PlanError, ValueError, KeyError, TypeError):
        return {"status": "unavailable", "reason": "GitHub read or identity/coverage failed"}


def remote_refs(root, config):
    output = run(root, "git", "ls-remote", "--heads", "--tags", config["remote"])
    refs = {}
    for line in output.splitlines():
        fields = line.split("\t")
        require(len(fields) == 2 and re.fullmatch(r"[0-9a-f]{40,64}", fields[0]),
                "Malformed remote refs")
        sha, ref = fields
        require(ref not in refs, "Duplicate remote ref")
        if ref == "refs/heads/" + config["target"]:
            refs[ref] = sha
        elif ref.startswith("refs/tags/"):
            tag = ref[len("refs/tags/"):].removesuffix("^{}")
            if version_of(tag, config["tag_prefix"]):
                refs[ref] = sha
    require("refs/heads/" + config["target"] in refs, "Remote release target missing")
    return refs


def collect_snapshot(root, config, todo_paths=()):
    identity = remote_identity(root, config)
    first_github = github_state(root, identity)
    try:
        refs = remote_refs(root, config)
    except PlanError:
        # Local metadata can support a provisional proposal, never a guard.
        return {"identity": identity, "remote_status": "unavailable", "refs": {},
                "target_sha": None, "github": first_github,
                "metadata": target_metadata(root, config, "HEAD", todo_paths)}
    target_sha = refs["refs/heads/" + config["target"]]
    run(root, "git", "fetch", "--no-tags", "--no-write-fetch-head", "--refmap=", config["remote"],
        "refs/heads/" + config["target"])
    metadata = target_metadata(root, config, target_sha, todo_paths)
    require(remote_refs(root, config) == refs, "Remote changed during observation; retry reads")
    require(github_state(root, identity) == first_github,
            "GitHub releases changed during observation; retry reads")
    return {"identity": identity, "remote_status": "available", "refs": refs,
            "target_sha": target_sha, "github": first_github, "metadata": metadata}


def release_versions(snapshot, prefix):
    records = snapshot["github"].get("releases", [])
    return [(r, version_of(r["tag_name"], prefix)) for r in records]


def baseline_summary(snapshot, prefix):
    versions = [v for v in snapshot["metadata"]["versions"].values() if v]
    for ref in snapshot["refs"]:
        if ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            value = version_of(ref[len("refs/tags/"):], prefix)
            if value and is_stable(value):
                versions.append(value)
    published, stable = [], []
    for record, version in release_versions(snapshot, prefix):
        if not record["draft"]:
            published.append(record)
            if not record["prerelease"] and version and is_stable(version):
                stable.append(record)
                versions.append(version)
    return {
        "version": max(versions, key=key) if versions else "0.0.0",
        "latest_published": max(published, key=lambda r: r["published_at"]) if published else None,
        "latest_stable": max(stable, key=lambda r: r["published_at"]) if stable else None,
    }


def validate_scope(root, scope):
    require(isinstance(scope, dict) and isinstance(scope.get("items"), list),
            "Scope needs an items array")
    chat = scope.get("chat", {"status": "unavailable", "coverage": "No context supplied"})
    require(chat.get("status") in {"available", "partial", "unavailable"}
            and isinstance(chat.get("coverage"), str) and bool(chat["coverage"].strip()),
            "Report chat coverage explicitly")
    scope = {**scope, "chat": chat}
    ids = set()
    for item in scope["items"]:
        require(isinstance(item, dict) and isinstance(item.get("id"), str)
                and item["id"].strip() and "\n" not in item["id"], "Stable source ID required")
        require(item["id"] not in ids, "Duplicate scoped source ID")
        ids.add(item["id"])
        require(type(item.get("completed")) is bool, "Completion must be explicit")
        require(item.get("kind") in {"breaking", "feature", "fix", "other"},
                "Unsupported change kind")
        require(isinstance(item.get("summary"), str) and bool(item["summary"].strip())
                and "\n" not in item["summary"], "Use a concise one-line summary")
        evidence = item.get("evidence", [])
        require(isinstance(evidence, list) and all(isinstance(e, str) and e.strip() for e in evidence),
                "Evidence must be a string array")
        require(not item["completed"] or evidence, "Completed work needs verified source evidence")
        require(isinstance(item.get("issues", []), list), "issues must be an array")
        for url in item.get("issues", []):
            parsed = urlsplit(url)
            require(parsed.scheme == "https" and parsed.hostname and not parsed.username
                    and not parsed.password and not parsed.query,
                    "Use stable public-safe issue URLs without credentials/query tokens")
        if item.get("todo"):
            safe_path(root, item["todo"]["path"])
    require(any(i["completed"] for i in scope["items"]), "No verified completed work in scope")
    return scope


def todo_paths(scope):
    return sorted({item["todo"]["path"] for item in scope["items"] if item.get("todo")})


def select_version(snapshot, prefix, scope, explicit=None, bump=None, policy_reason=None):
    baseline = baseline_summary(snapshot, prefix)["version"]
    kinds = {i["kind"] for i in scope["items"] if i["completed"]}
    if explicit:
        require(is_stable(explicit) and "+" not in explicit, "Explicit version must be stable X.Y.Z")
        candidate, reason = explicit, "Explicit requested version: " + explicit
    else:
        require(not bump or policy_reason, "A bump override needs documented policy evidence")
        selected = bump or ("major" if "breaking" in kinds else "patch" if kinds == {"fix"} else "minor")
        major, minor, patch = key(baseline)
        candidate = {"major": f"{major + 1}.0.0", "minor": f"{major}.{minor + 1}.0",
                     "patch": f"{major}.{minor}.{patch + 1}"}[selected]
        changed = ", ".join(i["id"] + ": " + i["summary"]
                            for i in scope["items"] if i["completed"])
        reason = f"{selected.upper()} ({policy_reason or ', '.join(sorted(kinds))}): {changed}"
    require(key(candidate) > key(baseline), "Requested version is not ahead of the baseline")
    # A prerelease or draft owns a release line without becoming a stable baseline.
    reserved = [v for _, v in release_versions(snapshot, prefix) if v]
    reserved += [version_of(r[len("refs/tags/"):].removesuffix("^{}"), prefix)
                 for r in snapshot["refs"] if r.startswith("refs/tags/")]
    reserved += list(snapshot["metadata"]["releases"])
    require(not any(v and key(v) == key(candidate) for v in reserved),
            "Candidate version is reserved by existing release metadata/tag; reconcile explicitly")
    return candidate, reason


def remove_block(text, block):
    require(isinstance(block, str) and block and block.endswith("\n"),
            "Scoped entries must be complete newline-terminated text blocks")
    require(text.count(block) == 1, "Scoped entry missing or ambiguous; reconcile source")
    start = text.index(block)
    require(start == 0 or text[start - 1] == "\n", "Scoped entry must start on a line boundary")
    return text[:start] + text[start + len(block):]


def remove_optional_block(text, block):
    require(isinstance(block, str) and block and block.endswith("\n"),
            "Scoped entries must be complete newline-terminated text blocks")
    return remove_block(text, block) if block in text else text


def pending_section(text):
    sections = [s for s in headings(text)
                if re.fullmatch(r"##[ \t]+(?:\[Unreleased\]|Unreleased)(?:[ \t].*)?", s[0], re.I)]
    require(len(sections) <= 1, "Expected at most one Markdown Unreleased section")
    return sections[0] if sections else None


def preserves_lines(before, after, label):
    # Additive local notes/tasks are safe; deleting or replacing unrelated
    # target lines is not. Ignore only blank separator lines, not note content.
    old = [line for line in before.splitlines() if line.strip()]
    new = [line for line in after.splitlines() if line.strip()]
    require(all(op in {"equal", "insert"} for op, *_ in difflib.SequenceMatcher(
        None, old, new, autojunk=False).get_opcodes()),
        f"Local release preimage differs from target: unrelated {label} content removed or reverted")


def preparation_evidence(root, config, scope, snapshot, edits):
    head = run(root, "git", "rev-parse", "HEAD").strip()
    target = snapshot["target_sha"] or head
    run(root, "git", "merge-base", "--is-ancestor", target, head)
    local = {edit["path"]: edit["before"] for edit in edits}
    for value in todo_paths(scope):
        local.setdefault(value, read_text(safe_path(root, value)))
    deltas = {}
    for value, text in local.items():
        committed = run(root, "git", "show", f"{head}:{value}")
        require(committed == text,
                f"Local release preimage differs from target: uncommitted {value}; review/commit scoped work first")
        before = snapshot["metadata"]["contents"][value]
        deltas[value] = "".join(difflib.unified_diff(
            before.splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile="target/" + value, tofile="local/" + value))
    changelog = config["changelog"]
    before, after = snapshot["metadata"]["contents"][changelog], local[changelog]
    old_pending, new_pending = pending_section(before), pending_section(after)
    # Everything outside Unreleased remains exact, including heading suffixes.
    def without_pending(text, section):
        return text[:section[1]] + text[section[2]:] if section else text
    require(without_pending(before, old_pending) == without_pending(after, new_pending),
            "Local release preimage differs from target: historical/preamble content changed")
    old_body = before[old_pending[3]:old_pending[2]] if old_pending else ""
    new_body = after[new_pending[3]:new_pending[2]] if new_pending else ""
    for item in scope["items"]:
        if item["completed"] and item.get("unreleased"):
            old_body = remove_optional_block(old_body, item["unreleased"])
            new_body = remove_optional_block(new_body, item["unreleased"])
    preserves_lines(old_body, new_body, "Unreleased")
    for value in todo_paths(scope):
        before, after = snapshot["metadata"]["contents"][value], local[value]
        for item in scope["items"]:
            if item["completed"] and item.get("todo", {}).get("path") == value:
                before = remove_optional_block(before, item["todo"]["entry"])
                after = remove_optional_block(after, item["todo"]["entry"])
        preserves_lines(before, after, "TODO")
    for source in config["version_sources"]:
        before = snapshot["metadata"]["contents"][source["path"]]
        after = local[source["path"]]
        old_match, new_match = source_match(before, source), source_match(after, source)
        old_plain = before[:old_match.start("version")] + before[old_match.end("version"):]
        new_plain = after[:new_match.start("version")] + after[new_match.end("version"):]
        require(old_plain == new_plain,
                "Local release preimage differs from target: non-version source content changed")
    return {"head": head, "target_sha": target, "target_to_local_diff": deltas,
            "diff_sha256": digest(json.dumps(deltas, sort_keys=True))}


def render_edits(root, config, scope, candidate, date):
    originals = {}

    def load(value):
        if value not in originals:
            originals[value] = read_text(safe_path(root, value))
        return originals[value]

    changelog_path = config["changelog"]
    changelog = load(changelog_path)
    newline = "\r\n" if "\r\n" in changelog else "\n"
    unreleased = pending_section(changelog)
    if unreleased:
        _, start, end, _ = unreleased
        pending = changelog[start:end]
    else:
        start = end = headings(changelog)[0][1] if headings(changelog) else len(changelog)
        pending = "## [Unreleased]" + newline * 2
    completed = [i for i in scope["items"] if i["completed"]]
    todo_outputs = {}
    moved_blocks = {}
    for item in completed:
        if item.get("unreleased"):
            if item["unreleased"] in pending:
                moved_blocks[item["id"]] = item["unreleased"]
            pending = remove_optional_block(pending, item["unreleased"])
        require(not re.search(r"(?<!\w)" + re.escape(item["id"]) + r"(?!\w)", pending),
                "Map the existing scoped Unreleased block explicitly before moving it")
        if item.get("todo"):
            todo = item["todo"]
            require(todo["path"] != changelog_path, "TODO and changelog must be separate")
            text = todo_outputs.get(todo["path"], load(todo["path"]))
            todo_outputs[todo["path"]] = remove_optional_block(text, todo["entry"])
    lines = [f"## [{candidate}] - {date}", ""]
    for kind, heading in (("breaking", "Changed"), ("feature", "Added"),
                          ("fix", "Fixed"), ("other", "Changed")):
        # Group the two Changed kinds together without duplicate headings.
        if kind == "other" and any(i["kind"] == "breaking" for i in completed):
            continue
        selected = [i for i in completed if i["kind"] == kind
                    or (kind == "breaking" and i["kind"] == "other")]
        if not selected:
            continue
        lines += ["### " + heading, ""]
        for item in selected:
            original = moved_blocks.get(item["id"], "")
            references = ([] if item["id"] in original else ["(" + item["id"] + ")"])
            references += [f"[issue]({url})" for url in item.get("issues", []) if url not in original]
            if original:
                # Preserve the complete selected block, including arbitrary
                # source-metadata comments and visible issue labels. Only add
                # missing references to its first bullet; never rebuild it.
                if references:
                    bullet = re.search(r"(?m)^[ \t]*[-*+][ \t]+[^\r\n]*", original)
                    if bullet:
                        original = original[:bullet.end()] + " " + " ".join(references) + original[bullet.end():]
                    else:
                        original = original.rstrip("\r\n") + newline + " ".join(references) + newline
                lines.append(original.rstrip("\r\n"))
            else:
                lines.append(f"- {item['summary']} " + " ".join(references))
        lines.append("")
    require(candidate not in release_sections(changelog), "Candidate section already exists locally")
    release = newline.join(lines) + newline
    outputs = {**todo_outputs, changelog_path:
               changelog[:start] + pending.rstrip("\r\n") + newline * 2 + release + changelog[end:]}
    for source in config["version_sources"]:
        text = load(source["path"])
        match = source_match(text, source)
        require(source["path"] not in outputs, "Version source overlaps another planned edit")
        outputs[source["path"]] = text[:match.start("version")] + candidate + text[match.end("version"):]
    # Incomplete scoped TODO blocks must remain byte-for-byte present.
    for item in scope["items"]:
        if not item["completed"] and item.get("todo"):
            todo = item["todo"]
            text = outputs.get(todo["path"], load(todo["path"]))
            require(text.count(todo["entry"]) == 1, "Incomplete TODO item is missing or changed")
    return [{"path": value, "before": originals[value], "after": after,
             "before_sha256": digest(originals[value]), "after_sha256": digest(after)}
            for value, after in sorted(outputs.items())]


def require_complete(snapshot):
    require(snapshot["remote_status"] == "available", "Unverifiable remote baseline")
    require(snapshot["identity"]["same_destination"], "Fetch/push destinations disagree")
    require(snapshot["github"]["status"] == "available", "Unverifiable GitHub releases")
    require(snapshot["github"].get("draft_visibility"), "Draft release coverage is unavailable")


def fingerprint(snapshot):
    return digest(json.dumps(snapshot, sort_keys=True))


def verify_edits(root, plan):
    for edit in plan["edits"]:
        require(digest(edit["before"]) == edit["before_sha256"]
                and digest(edit["after"]) == edit["after_sha256"], "Corrupt plan edit")
        require(read_text(safe_path(root, edit["path"])) == edit["after"],
                f"Prepared file differs from plan: {edit['path']}")
    after = next(e["after"] for e in plan["edits"] if e["path"] == plan["config"]["changelog"])
    sections = release_sections(after)
    for version, section in plan["baseline"]["metadata"]["releases"].items():
        require(sections.get(version) == section, "Mainline release history changed or missing")


def at_clean_target(root, config, snapshot):
    require(not run(root, "git", "status", "--porcelain"), "Publication target must be clean")
    require(run(root, "git", "rev-parse", "HEAD").strip() == snapshot["target_sha"],
            "HEAD is not the exact remote release target")
    require(run(root, "git", "rev-parse", "--symbolic-full-name", "@{upstream}").strip()
            == f"refs/remotes/{config['remote']}/{config['target']}",
            "Publication upstream differs from configured release target")


def publication_gaps(plan, snapshot):
    prefix = plan["config"]["tag_prefix"]
    published = {v for r, v in release_versions(snapshot, prefix)
                 if v and is_stable(v) and not r["draft"] and not r["prerelease"]}
    gaps = [v for v in snapshot["metadata"]["releases"]
            if is_stable(v) and key(v) < key(plan["candidate"]) and v not in published]
    require(not gaps, "Unaccounted intermediate changelog publications: " + ", ".join(gaps))


def make_plan(root, config, scope, date, explicit=None, bump=None, policy_reason=None):
    config = validate_config(root, config)
    scope = validate_scope(root, scope)
    require(dt.date.fromisoformat(date).isoformat() == date, "Use an ISO release date")
    snapshot = collect_snapshot(root, config, todo_paths(scope))
    candidate, reason = select_version(snapshot, config["tag_prefix"], scope,
                                       explicit, bump, policy_reason)
    edits = render_edits(root, config, scope, candidate, date)
    evidence = preparation_evidence(root, config, scope, snapshot, edits)
    return {"schema": 1, "state": "prepared", "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "config": config, "scope": scope, "baseline": snapshot,
            "baseline_fingerprint": fingerprint(snapshot),
            "baseline_summary": baseline_summary(snapshot, config["tag_prefix"]),
            "candidate": candidate, "reason": reason, "date": date,
            "selection": {"explicit": explicit, "bump": bump, "policy_reason": policy_reason},
            "preparation": evidence, "edits": edits}


def load_plan(root, file_path):
    plan = json.loads(read_text(file_path))
    require(plan.get("schema") == 1 and plan.get("state") in {"prepared", "bound"},
            "Unsupported plan")
    validate_config(root, plan["config"])
    validate_scope(root, plan["scope"])
    require(fingerprint(plan["baseline"]) == plan["baseline_fingerprint"], "Corrupt baseline")
    candidate, _ = select_version(plan["baseline"], plan["config"]["tag_prefix"], plan["scope"],
                                  **plan["selection"])
    require(candidate == plan["candidate"], "Plan candidate differs from recorded selection")
    return plan


def check_plan(root, plan, phase, owned_tag=None, owned_release=None):
    config = plan["config"]
    current = collect_snapshot(root, config, todo_paths(plan["scope"]))
    require_complete(current)
    baseline = plan["baseline"] if phase == "commit" else plan.get("publication_baseline")
    require(baseline is not None, "Publication requires binding after metadata integration")
    require_complete(baseline)
    comparable = copy.deepcopy(current)
    if owned_tag is not None:
        require(phase == "publish", "Owned publication state is not a preparation input")
        ref = "refs/tags/" + config["tag_prefix"] + plan["candidate"]
        require(ref not in baseline["refs"] and ref + "^{}" not in baseline["refs"],
                "Candidate tag was not absent in saved publication baseline")
        require(owned_tag["commit"] == current["target_sha"], "Owned tag target mismatch")
        expected = {ref: owned_tag["object"]}
        if owned_tag["object"] != owned_tag["commit"]:
            expected[ref + "^{}"] = owned_tag["commit"]
        actual = {r: sha for r, sha in comparable["refs"].items() if r in {ref, ref + "^{}"}}
        require(actual == expected, "Owned tag object/peeled commit changed")
        for value in expected:
            comparable["refs"].pop(value)
    if owned_release is not None:
        require(owned_tag is not None, "Owned release requires verified owned tag")
        require(owned_release["tag_name"] == config["tag_prefix"] + plan["candidate"]
                and not owned_release["draft"] and not owned_release["prerelease"],
                "Owned release state mismatch")
        require(all(r["id"] != owned_release["id"] for r in baseline["github"]["releases"]),
                "Owned release already existed in baseline")
        records = comparable["github"]["releases"]
        require(records.count(owned_release) == 1, "Owned release readback changed or missing")
        records.remove(owned_release)
    require(comparable == baseline, "Stale version plan: target, tags or releases changed; refresh")
    verify_edits(root, plan)
    if phase == "commit":
        require(plan["state"] == "prepared", "Use the preparation plan before committing")
        require(run(root, "git", "rev-parse", "HEAD").strip() == plan["preparation"]["head"],
                "Scoped code HEAD changed; refresh completion/review evidence")
        run(root, "git", "merge-base", "--is-ancestor", baseline["target_sha"], "HEAD")
    else:
        require(plan["state"] == "bound", "Publication needs a bound plan")
        at_clean_target(root, config, current)
        publication_gaps(plan, current)
    return {"status": "checked", "phase": phase, "candidate": plan["candidate"],
            "target_sha": current["target_sha"], "fingerprint": fingerprint(current),
            "publication_requires": "separate authorization and publisher-held gate with its reported host boundary"}


def bind_plan(root, plan):
    require(plan["state"] == "prepared", "Bind a preparation plan once")
    current = collect_snapshot(root, plan["config"], todo_paths(plan["scope"]))
    require_complete(plan["baseline"])
    require_complete(current)
    require(plan["baseline"]["identity"] == current["identity"], "Remote identity changed before binding")
    for ref, sha in plan["baseline"]["refs"].items():
        if ref.startswith("refs/tags/"):
            require(current["refs"].get(ref) == sha, "Existing tag changed before binding")
    current_releases = {r["id"]: r for r in current["github"]["releases"]}
    for record in plan["baseline"]["github"]["releases"]:
        require(current_releases.get(record["id"]) == record, "Existing release changed before binding")
    run(root, "git", "merge-base", "--is-ancestor", plan["baseline"]["target_sha"], current["target_sha"])
    at_clean_target(root, plan["config"], current)
    verify_edits(root, plan)
    for edit in plan["edits"]:
        text = run(root, "git", "show", f"{current['target_sha']}:{edit['path']}")
        require(text == edit["after"], "Remote target differs from prepared metadata")
    # Recompute against fresh evidence, excluding only this plan's exact,
    # independently verified integrated metadata. This lets an intermediate
    # publication catch up without treating our own candidate as a new base.
    effective = copy.deepcopy(current)
    sections = effective["metadata"]["releases"]
    require(plan["candidate"] in sections, "Integrated candidate section is missing")
    sections.pop(plan["candidate"])
    previous = [v for v in sections if is_stable(v)]
    previous_version = max(previous, key=key) if previous else None
    effective["metadata"]["versions"] = {
        value: (previous_version if value == plan["config"]["changelog"]
                else plan["baseline"]["metadata"]["versions"][value])
        for value in effective["metadata"]["versions"]
    }
    candidate, _ = select_version(effective, plan["config"]["tag_prefix"], plan["scope"],
                                  **plan["selection"])
    require(candidate == plan["candidate"], "Fresh baseline changes the candidate; reconcile and replan")
    result = copy.deepcopy(plan)
    result.update(state="bound", publication_baseline=current,
                  binding_selection_baseline=baseline_summary(effective, plan["config"]["tag_prefix"]),
                  bound_at=dt.datetime.now(dt.timezone.utc).isoformat())
    return result


def write_json(value, output):
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if output:
        # Exclusive creation makes accidental plan replacement an explicit error.
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
    else:
        print(text, end="")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("plan", help="Create a private provisional proposal")
    prepare.add_argument("--config", type=Path, required=True)
    prepare.add_argument("--scope", type=Path, required=True)
    prepare.add_argument("--date", required=True)
    prepare.add_argument("--version")
    prepare.add_argument("--bump", choices=("major", "minor", "patch"))
    prepare.add_argument("--policy-reason")
    prepare.add_argument("--output", type=Path)
    for name in ("diff", "check", "bind"):
        command = commands.add_parser(name)
        command.add_argument("--plan", type=Path, required=True)
        if name == "check":
            command.add_argument("--phase", choices=("commit", "publish"), required=True)
        if name == "bind":
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(run(args.repo, "git", "rev-parse", "--show-toplevel").strip()).resolve()
    if args.command == "plan":
        require(not (args.version and args.bump), "Use an explicit version or a bump policy")
        plan = make_plan(root, json.loads(read_text(args.config)), json.loads(read_text(args.scope)),
                         args.date, args.version, args.bump, args.policy_reason)
        write_json(plan, args.output)
    else:
        plan = load_plan(root, args.plan)
        if args.command == "diff":
            for edit in plan["edits"]:
                print("".join(difflib.unified_diff(
                    edit["before"].splitlines(keepends=True), edit["after"].splitlines(keepends=True),
                    fromfile="a/" + edit["path"], tofile="b/" + edit["path"]
                )), end="")
        elif args.command == "bind":
            write_json(bind_plan(root, plan), args.output)
        else:
            write_json(check_plan(root, plan, args.phase), None)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PlanError, OSError, ValueError, KeyError, TypeError, StopIteration, re.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
