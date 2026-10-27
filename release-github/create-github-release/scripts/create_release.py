#!/usr/bin/env python3
"""Publish prepared notes under a verified shared gate; never retry mutations."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import unquote, urlsplit
import uuid


class ReleaseError(RuntimeError):
    """A publication precondition could not be verified."""


class UnknownMutation(ReleaseError):
    """A write was attempted; read-only reconciliation is required."""


VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
RELEASE_FIELDS = ("id", "tag_name", "draft", "prerelease", "published_at", "updated_at")


def require(condition, message):
    if not condition:
        raise ReleaseError(message)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run(cmd, cwd=None, input_text=None):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, input=input_text, text=True, capture_output=True, timeout=60,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GH_PROMPT_DISABLED": "1"},
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"{Path(cmd[0]).name} unavailable; inspect access privately") from exc
    # Neither stderr nor command arguments are safe diagnostic output: they may
    # contain credential-bearing URLs or private adapter inputs.
    require(result.returncode == 0, f"{Path(cmd[0]).name} operation failed; inspect access privately")
    return result.stdout.strip()


def repository_identity(root, remote, github_host=None):
    urls = run(["git", "remote", "get-url", "--all", remote], root).splitlines()
    pushes = run(["git", "remote", "get-url", "--push", "--all", remote], root).splitlines()
    require(len(urls) == len(pushes) == 1, "Multiple remote destinations are ambiguous")

    def parse(value):
        if "://" in value:
            parsed = urlsplit(value)
            require(parsed.scheme in {"https", "ssh"}, "Unsupported publication transport")
            host, repository = parsed.hostname, parsed.path.lstrip("/")
        else:
            match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):([^:]+)", value)
            require(match is not None, "Remote GitHub identity is unverified")
            host, repository = match.groups()
        repository = repository.rstrip("/").removesuffix(".git")
        require(host in {"github.com", github_host} and host is not None,
                "Verify an Enterprise hostname with --github-host")
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository),
                "Invalid repository identity")
        return host.lower() + "/" + repository.lower()

    identity = parse(urls[0])
    require(identity == parse(pushes[0]), "Fetch/push repository identities differ")
    return {"repository": identity, "fetch_hash": digest(urls[0]), "push_hash": digest(pushes[0])}


def parse_refs(output):
    refs = {}
    for line in output.splitlines():
        parts = line.split("\t")
        require(len(parts) == 2 and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", parts[0]),
                "Malformed remote ref read")
        sha, ref = parts
        require(ref not in refs, "Duplicate remote ref read")
        refs[ref] = sha
    return refs


def target_sha(root, remote, target_ref):
    refs = parse_refs(run(["git", "ls-remote", "--heads", remote, target_ref], root))
    require(set(refs) == {target_ref}, "Authoritative upstream target unavailable")
    return refs[target_ref]


def remote_tags(root, remote):
    refs = parse_refs(run(["git", "ls-remote", "--tags", remote], root))
    require(all(ref.startswith("refs/tags/") for ref in refs), "Unexpected tag collection shape")
    return refs


def tag_from_refs(refs, tag):
    ref = "refs/tags/" + tag
    require(ref in refs or ref + "^{}" not in refs, "Peeled tag is missing its object")
    if ref not in refs:
        return None
    return {"object": refs[ref], "commit": refs.get(ref + "^{}", refs[ref])}


def local_tag(root, tag):
    # --list returns a successful empty collection for verified local absence.
    if not run(["git", "tag", "--list", tag], root):
        return None
    ref = "refs/tags/" + tag
    return {"object": run(["git", "rev-parse", ref], root),
            "commit": run(["git", "rev-parse", ref + "^{commit}"], root)}


def github_json(root, repository, endpoint, *options):
    host = repository.split("/", 1)[0]
    return json.loads(run(["gh", "api", "--method", "GET", "--hostname", host,
                           endpoint, *options], root))


def release_url_valid(url, repository, tag):
    parsed = urlsplit(url)
    host, owner, name = repository.split("/")
    return (parsed.scheme == "https" and parsed.hostname == host and not parsed.username
            and not parsed.password and not parsed.query and not parsed.fragment
            and unquote(parsed.path) == f"/{owner}/{name}/releases/tag/{tag}")


def github_releases(root, repository):
    _, owner, name = repository.split("/")
    endpoint = f"repos/{owner}/{name}"
    info = github_json(root, repository, endpoint)
    require(isinstance(info, dict) and info.get("full_name", "").lower() == f"{owner}/{name}",
            "GitHub repository identity mismatch")
    permissions = info.get("permissions")
    require(isinstance(permissions, dict) and permissions.get("push") is True,
            "Complete draft-release visibility requires push access")
    pages = github_json(root, repository, endpoint + "/releases?per_page=100", "--paginate", "--slurp")
    require(isinstance(pages, list) and all(isinstance(p, list) for p in pages),
            "Incomplete GitHub release pagination")
    records, ids, tags = [], set(), set()
    for page in pages:
        for record in page:
            require(isinstance(record, dict) and type(record.get("id")) is int,
                    "Invalid GitHub release identity")
            require(record["id"] not in ids and record.get("tag_name") not in tags,
                    "Ambiguous GitHub release identity/tag")
            require(isinstance(record.get("tag_name"), str) and bool(record["tag_name"]),
                    "Missing release tag identity")
            require(type(record.get("draft")) is bool and type(record.get("prerelease")) is bool,
                    "Unknown GitHub release state")
            require(record["draft"] or isinstance(record.get("published_at"), str),
                    "Missing publication evidence")
            require(isinstance(record.get("updated_at"), str), "Missing update identity")
            require(isinstance(record.get("body"), (str, type(None)))
                    and isinstance(record.get("name"), (str, type(None))), "Malformed release notes")
            require(isinstance(record.get("html_url"), str)
                    and release_url_valid(record["html_url"], repository, record["tag_name"]),
                    "Release URL does not match repository/tag")
            ids.add(record["id"])
            tags.add(record["tag_name"])
            records.append({field: record[field] for field in
                            (*RELEASE_FIELDS, "body", "name", "html_url")})
    return sorted(records, key=lambda r: r["id"])


def changelog_sections(changelog):
    text = changelog.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^##[ \t]+[^\r\n]+", text, re.M))
    sections = {}
    for i, heading in enumerate(headings):
        match = re.match(r"##[ \t]+\[([^\]]+)\]", heading[0])
        if match and VERSION.fullmatch(match[1]):
            version = match[1]
            require(version not in sections, "Duplicate concrete changelog section")
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            sections[version] = text[heading.end():end].strip()
    return sections


def version_key(version):
    require(VERSION.fullmatch(version), "Publisher supports stable X.Y.Z versions")
    return tuple(int(part) for part in version.split("."))


def history_gaps(sections, version, records):
    published = {r["tag_name"][1:] for r in records
                 if r["tag_name"].startswith("v") and not r["draft"] and not r["prerelease"]}
    gaps = [v for v in sections if version_key(v) < version_key(version) and v not in published]
    require(not gaps, "Missing intermediate changelog publications: " + ", ".join(gaps))


def load_guard():
    source = Path(__file__).resolve().parents[2] / "update-release/scripts/release_plan.py"
    require(source.is_file(), "Install the companion update-release skill for --plan")
    spec = importlib.util.spec_from_file_location("update_release_publication_guard", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(getattr(module, "PUBLICATION_GUARD_API", None) == 1,
            "Upgrade both release skills together: unsupported guard API")
    return module


def sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class Journal:
    def __init__(self, file_path, initial):
        self.path = file_path
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # The common Git directory already exists. Persist its new intent
        # directory entry before persisting the intent file inside it.
        sync_directory(self.path.parent.parent)
        for previous in self.path.parent.glob("*.json"):
            record = json.loads(previous.read_text(encoding="utf-8"))
            if record.get("repository") == initial["repository"] and record.get("tag") == initial["tag"]:
                require(record.get("status") in {"verified", "prepared", "reconciled"},
                        "A prior publication intent needs read-only reconciliation: " + str(previous))
        self.data = {"schema": 1, "intent": uuid.uuid4().hex, "status": "prepared", **initial}
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(self.data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        sync_directory(self.path.parent)

    def save(self, **fields):
        self.data.update(fields)
        descriptor, name = tempfile.mkstemp(dir=self.path.parent, prefix=".publication-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(self.data, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
            sync_directory(self.path.parent)
        finally:
            Path(name).unlink(missing_ok=True)


class SharedGate:
    mode = "external_shared_gate"
    def __init__(self, verifier, lease_id):
        require(verifier is not None and lease_id, "Publication requires a trusted live shared-gate verifier and lease")
        require(verifier.is_absolute() and verifier.is_file() and os.access(verifier, os.X_OK),
                "Gate verifier must be an explicitly configured absolute executable")
        require(not verifier.stat().st_mode & 0o022, "Gate verifier must not be group/world writable")
        self.verifier, self.lease_id = verifier, lease_id

    def check(self, binding, phase):
        request = {"schema": 1, "nonce": uuid.uuid4().hex, "lease_id": self.lease_id,
                   "phase": phase, **binding}
        proof = json.loads(run([str(self.verifier)], input_text=json.dumps(request)))
        require(isinstance(proof, dict) and all(proof.get(k) == v for k, v in request.items()),
                "Shared-gate proof is stale or belongs to another publication")
        require(proof.get("gate_key") == "release:" + binding["repository"],
                "Gate must serialize the repository across versions/worktrees")
        for field in ("held", "exclusive", "all_writers_gated", "target_fenced", "no_unresolved_publication"):
            require(proof.get(field) is True, f"Shared gate did not verify {field}")
        service = urlsplit(proof.get("service", ""))
        require(service.scheme == "https" and service.hostname and not service.username
                and not service.password and not service.query, "Unverified shared service identity")
        evidence = proof.get("evidence")
        require(isinstance(evidence, dict) and all(isinstance(evidence.get(k), str) and evidence[k]
                for k in ("lease_revision", "writer_policy_revision", "target_fence_revision")),
                "Shared gate must provide live lease/policy/fence evidence")
        now = dt.datetime.now(dt.timezone.utc)
        checked = dt.datetime.fromisoformat(proof["checked_at"].replace("Z", "+00:00"))
        expires = dt.datetime.fromisoformat(proof["expires_at"].replace("Z", "+00:00"))
        require(checked.tzinfo is not None and expires.tzinfo is not None,
                "Gate timestamps require timezone offsets")
        require(-2 <= (now - checked).total_seconds() <= 10 and (expires - now).total_seconds() >= 90,
                "Shared-gate evidence is stale or lease expires before a bounded mutation")
        return {"checked_at": proof["checked_at"], "service_sha256": digest(proof["service"]),
                "mode": self.mode, "evidence_sha256": digest(json.dumps(evidence, sort_keys=True))}

    def close(self):
        # The external controller owns acquisition, durable unknown-outcome
        # retention and release. The publisher never unlocks it on a failure.
        pass


class LocalGate:
    """One host, shared Git common directory, cooperating publisher processes."""

    mode = "same_host_common_git_lock"

    def __init__(self, common_dir, timeout=60):
        require(timeout >= 0, "Lock timeout must be nonnegative")
        self.path = common_dir / "release-publication.lock"
        self.descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        deadline = time.monotonic() + timeout
        try:
            while True:
                try:
                    fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    require(time.monotonic() < deadline, "Another same-host publisher holds the release lock")
                    time.sleep(0.05)
        except BaseException:
            self.close()
            raise

    def check(self, binding, phase):
        require(self.descriptor is not None, "Same-host release lock is no longer held")
        return {"mode": self.mode, "path": str(self.path), "pid": os.getpid(),
                "cross_host_exclusion": False, "bypassing_clients_excluded": False}

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None
        # Keep the inode in place: unlinking a lock file permits split locks.


class Publisher:
    def __init__(self, args):
        self.root = Path(run(["git", "rev-parse", "--show-toplevel"], args.repo)).resolve()
        self.common_dir = (self.root / run(["git", "rev-parse", "--git-common-dir"], self.root)).resolve()
        self.local_gate = LocalGate(self.common_dir, getattr(args, "lock_timeout", 60))
        self.gate = self.local_gate
        try:
            if args.gate_verifier is not None or args.gate_lease:
                self.gate = SharedGate(args.gate_verifier, args.gate_lease)
            self.prepare(args)
        except BaseException:
            self.gate.close()
            self.local_gate.close()
            raise

    def prepare(self, args):
        require(not run(["git", "status", "--porcelain"], self.root), "Working tree is dirty")
        self.branch = run(["git", "branch", "--show-current"], self.root)
        require(self.branch, "Detached HEAD; use a branch with a verified upstream")
        self.remote = run(["git", "config", "--get", f"branch.{self.branch}.remote"], self.root)
        self.target_ref = run(["git", "config", "--get", f"branch.{self.branch}.merge"], self.root)
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", self.remote), "Invalid upstream remote")
        require(self.target_ref.startswith("refs/heads/"), "Upstream must be a branch")
        run(["git", "check-ref-format", self.target_ref], self.root)
        self.head = run(["git", "rev-parse", "HEAD"], self.root)
        self.identity = repository_identity(self.root, self.remote, args.github_host)
        self.repository = self.identity["repository"]
        require(target_sha(self.root, self.remote, self.target_ref) == self.head,
                "HEAD does not match fresh authoritative upstream target")
        self.guard, self.plan = None, None
        if args.plan:
            self.guard = load_guard()
            self.plan = self.guard.load_plan(self.root, args.plan)
            require(self.plan["state"] == "bound", "Bind the prepared plan after verified merge before publishing")
            config = self.plan["config"]
            require(config["remote"] == self.remote and "refs/heads/" + config["target"] == self.target_ref
                    and config["tag_prefix"] == "v", "Plan/publisher remote, target or tag convention mismatch")
            baseline = self.plan["publication_baseline"]
            require(baseline["identity"]["github"] == self.repository
                    and baseline["target_sha"] == self.head, "Plan repository/target SHA mismatch")
            require(not args.version or args.version == self.plan["candidate"], "Requested version differs from plan")
            require(not args.changelog or args.changelog == config["changelog"], "Changelog differs from plan")
            self.version = self.plan["candidate"]
            changelog_path = config["changelog"]
        else:
            self.version, changelog_path = args.version, args.changelog or "CHANGELOG.md"
        changelog = (self.root / changelog_path).resolve()
        require(changelog.is_relative_to(self.root) and changelog.is_file(), "Changelog must be a repository file")
        self.sections = changelog_sections(changelog)
        self.version = self.version or next(iter(self.sections), None)
        require(self.version is not None, "No concrete changelog version")
        version_key(self.version)
        self.tag = "v" + self.version
        require(bool(self.sections.get(self.version)), "Requested changelog section is missing or empty")
        self.notes = self.sections[self.version]
        self.tags = remote_tags(self.root, self.remote)
        self.releases = github_releases(self.root, self.repository)
        history_gaps(self.sections, self.version, self.releases)
        existing = next((r for r in self.releases if r["tag_name"] == self.tag), None)
        require(not self.plan or existing is None, "Guarded plan cannot overwrite an existing release")
        require(not existing or not (existing["draft"] or existing["prerelease"]),
                "Draft/prerelease transition needs separately scoped publication handling")
        self.existing = existing
        higher = any(VERSION.fullmatch(r["tag_name"].removeprefix("v"))
                     and r["tag_name"].startswith("v") and not r["draft"] and not r["prerelease"]
                     and version_key(r["tag_name"][1:]) > version_key(self.version) for r in self.releases)
        self.latest = args.latest if args.latest is not None else not higher
        self.owned_tag, self.owned_release = None, None
        self.baseline_fingerprint = (self.guard.fingerprint(self.plan["publication_baseline"])
                                     if self.plan else digest(json.dumps(
                                         {"head": self.head, "tags": self.tags, "releases": self.releases}, sort_keys=True)))
        intent_dir = self.common_dir / "publication-intents"
        journal_path = args.journal or intent_dir / (uuid.uuid4().hex + ".json")
        journal_path = journal_path.resolve()
        require(journal_path.parent == intent_dir,
                "Keep journals in the shared Git common directory publication-intents folder")
        self.journal = Journal(journal_path, {"repository": self.repository, "target_ref": self.target_ref,
            "target_sha": self.head, "version": self.version, "tag": self.tag, "latest": self.latest,
            "notes_sha256": digest(self.notes), "plan_fingerprint": self.baseline_fingerprint,
            "existing_release": {k: existing[k] for k in RELEASE_FIELDS} if existing else None})

    def checkpoint(self, phase):
        require(not run(["git", "status", "--porcelain"], self.root), "Working tree changed during publication")
        require(run(["git", "rev-parse", "HEAD"], self.root) == self.head,
                "HEAD changed during publication")
        require(repository_identity(self.root, self.remote, self.repository.split("/")[0]) == self.identity,
                "Remote publication destination changed")
        require(target_sha(self.root, self.remote, self.target_ref) == self.head,
                "Authoritative target changed during publication")
        expected_tags = dict(self.tags)
        if self.owned_tag:
            expected_tags["refs/tags/" + self.tag] = self.owned_tag["object"]
            if self.owned_tag["object"] != self.owned_tag["commit"]:
                expected_tags["refs/tags/" + self.tag + "^{}"] = self.owned_tag["commit"]
        require(remote_tags(self.root, self.remote) == expected_tags, "Remote tag state changed")
        records = github_releases(self.root, self.repository)
        comparable = [r for r in records if not self.owned_release or r["id"] != self.owned_release["id"]]
        initial = [r for r in self.releases if not self.owned_release or r["id"] != self.owned_release["id"]]
        require(comparable == initial, "GitHub release state changed; reconcile read-only")
        if self.guard:
            self.guard.check_plan(self.root, self.plan, "publish", self.owned_tag,
                                  {k: self.owned_release[k] for k in RELEASE_FIELDS} if self.owned_release else None)
        binding = {"repository": self.repository, "target_ref": self.target_ref,
                   "target_sha": self.head, "version": self.version, "tag": self.tag,
                   "plan_fingerprint": self.baseline_fingerprint}
        self.local_gate.check(binding, phase)
        proof = self.gate.check(binding, phase)
        self.journal.save(phase=phase, gate=proof)

    def mutate(self, operation, cmd):
        self.checkpoint("before_" + operation)
        self.journal.save(status="attempting", operation=operation)
        try:
            output = run(cmd, self.root)
        except Exception as exc:
            self.journal.save(status="unknown", operation=operation)
            raise UnknownMutation(f"{operation} outcome unknown; reconcile read-only using {self.journal.path}") from exc
        self.journal.save(status="observed_success", operation=operation)
        return output

    def ensure_tag(self):
        remote = tag_from_refs(self.tags, self.tag)
        local = local_tag(self.root, self.tag)
        if remote:
            require(not self.plan, "Guarded candidate tag already exists; reconcile before a new attempt")
            require(remote["commit"] == self.head, "Remote tag points to a different commit")
            run(["git", "fetch", "--no-tags", "--no-write-fetch-head", "--refmap=", self.remote,
                 "refs/tags/" + self.tag], self.root)
            require(run(["git", "rev-parse", remote["object"] + "^{commit}"], self.root) == self.head,
                    "Remote tag object does not peel to the target commit")
            require(local is None or local == remote, "Local and remote tag objects differ; preserve both")
            self.journal.save(expected_tag=remote)
            if local is None:
                self.mutate("adopt_tag", ["git", "update-ref", "refs/tags/" + self.tag,
                                         remote["object"], "0" * len(self.head)])
            return
        require(not self.plan or local is None, "Local candidate tag already exists; reconcile the prior intent")
        if local:
            require(local["commit"] == self.head, "Local tag points to a different commit")
        else:
            self.mutate("create_tag", ["git", "tag", "-a", self.tag, self.head, "-m", "Release " + self.version])
            local = local_tag(self.root, self.tag)
            require(local is not None and local["commit"] == self.head, "Created tag readback mismatch")
        self.journal.save(expected_tag=local)
        self.mutate("push_tag", ["git", "push", "--porcelain", self.remote,
                                 f"{local['object']}:refs/tags/{self.tag}"])
        actual = tag_from_refs(remote_tags(self.root, self.remote), self.tag)
        require(actual == local, "Pushed tag object/peeled commit unverified; reconcile read-only")
        self.owned_tag = local
        self.journal.save(owned_tag=local)

    def publish(self):
        try:
            self.checkpoint("initial")
            self.ensure_tag()
            descriptor, filename = tempfile.mkstemp(dir=self.journal.path.parent, prefix=".release-notes-")
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(self.notes)
                operation = "edit_release" if self.existing else "create_release"
                cmd = ["gh", "release", "edit" if self.existing else "create", self.tag,
                       "--repo", self.repository, "--title", self.version, "--notes-file", filename,
                       "--target", self.head, "--verify-tag", "--latest=" + str(self.latest).lower()]
                output = self.mutate(operation, cmd)
            finally:
                Path(filename).unlink(missing_ok=True)
            records = github_releases(self.root, self.repository)
            found = [r for r in records if r["tag_name"] == self.tag]
            require(len(found) == 1, "Release write could not be verified; reconcile read-only")
            record = found[0]
            require(not record["draft"] and not record["prerelease"] and record["published_at"]
                    and record["name"] == self.version and (record["body"] or "").strip() == self.notes,
                    "Published release notes/state differ; reconcile read-only")
            if self.existing:
                require(record["id"] == self.existing["id"], "Edited release identity changed")
            else:
                require(record["id"] not in {r["id"] for r in self.releases}
                        and output == record["html_url"], "Created release identity is unverified")
            self.owned_release = record
            self.journal.save(owned_release={k: record[k] for k in RELEASE_FIELDS})
            self.checkpoint("verify_result")
            _, owner, name = self.repository.split("/")
            latest = github_json(self.root, self.repository, f"repos/{owner}/{name}/releases/latest")
            require(isinstance(latest, dict) and type(latest.get("id")) is int
                    and (latest["id"] == record["id"]) == self.latest,
                    "Latest-release state is unverified; reconcile read-only")
            self.journal.save(status="verified", release_url=record["html_url"])
            return {"release_url": record["html_url"], "version": self.version, "tag": self.tag,
                    "commit": self.head, "branch": self.branch, "upstream": self.remote + "/" + self.target_ref[11:],
                    "journal": str(self.journal.path), "latest": self.latest,
                    "serialization": self.gate.mode,
                    "cross_host_exclusion": self.gate.mode == "external_shared_gate"}
        except Exception:
            if self.journal.data["status"] not in {"unknown", "prepared"}:
                self.journal.save(status="requires_read_only_reconciliation")
            raise
        finally:
            self.gate.close()
            self.local_gate.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--version")
    parser.add_argument("--changelog")
    parser.add_argument("--latest", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--gate-verifier", type=Path)
    parser.add_argument("--gate-lease")
    parser.add_argument("--github-host")
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--lock-timeout", type=float, default=60)
    args = parser.parse_args(argv)
    result = Publisher(args).publish()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
