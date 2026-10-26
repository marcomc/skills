#!/usr/bin/env python3
"""Prepare content fingerprints and ledger checks; never execute validation or approve code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
    ).stdout


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def fingerprint(path: Path) -> dict[str, Any] | None:
    """Hash file content, mode and symlink identity without exposing content."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    result: dict[str, Any] = {"mode": stat.S_IMODE(info.st_mode)}
    if stat.S_ISLNK(info.st_mode):
        result["link"] = os.readlink(path)
        target = path.resolve(strict=True)
        if not target.is_file():
            raise ValueError(f"Cannot fingerprint directory symlink: {path}")
        result["target"] = fingerprint(target)
    elif stat.S_ISREG(info.st_mode):
        with path.open("rb") as handle:
            checksum = hashlib.sha256()
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                checksum.update(block)
        result["sha256"] = checksum.hexdigest()
    else:
        raise ValueError(f"Cannot fingerprint non-file input: {path}")
    return result


def snapshot(
    repo: Path, base: str, environment: str, inputs: list[str]
) -> dict[str, Any]:
    if not environment.strip():
        raise ValueError("An explicit environment fingerprint is required")
    root = Path(
        os.fsdecode(git(repo, "rev-parse", "--show-toplevel")).strip()
    ).resolve()
    base_oid = (
        git(root, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}")
        .decode()
        .strip()
    )
    for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, _, stage = metadata.split()
        if mode == b"160000" or stage != b"0":
            raise ValueError(
                f"Cannot fingerprint submodule or unmerged index entry: {os.fsdecode(name)}"
            )
    paths = {
        os.fsdecode(p)
        for p in git(
            root, "ls-files", "--cached", "--others", "--exclude-standard", "-z"
        ).split(b"\0")
        if p
    }
    files = {}
    for name in sorted(paths):
        value = fingerprint(root / name)
        if (
            value is not None
        ):  # A staged deletion and the committed deletion have the same content tree.
            files[name] = value
    extra = {}
    for name in inputs:
        path = Path(name).expanduser()
        if not path.is_absolute():
            path = root / path
        value = fingerprint(path)
        if value is None:
            raise ValueError(f"Required additional input is missing: {name}")
        extra[str(path.absolute())] = value
    material = {
        "version": 1,
        "repository": str(root),
        "base": base_oid,
        "environment": environment,
        "files": files,
        "additional_inputs": extra,
    }
    return {
        **material,
        "digest": digest(material),
        "head": git(root, "rev-parse", "HEAD").decode().strip(),
    }


def compare(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "version",
        "repository",
        "base",
        "environment",
        "files",
        "additional_inputs",
    )
    prior = {k: previous.get(k) for k in fields}
    if previous.get("version") != 1 or previous.get("digest") != digest(prior):
        raise ValueError("Previous snapshot is incomplete or its digest does not match")
    changed = [field for field in fields if prior[field] != current[field]]
    paths = sorted(
        name
        for name in set(prior["files"]) | set(current["files"])
        if prior["files"].get(name) != current["files"].get(name)
    )
    return {
        "snapshot_matches": not changed,
        "changed_components": changed,
        "changed_paths": paths,
    }


def bookkeeping(
    data: dict[str, Any], batch_id: str, snapshot_digest: str
) -> dict[str, list[str]]:
    """Separate missing metadata from missing or stale execution evidence."""
    if not isinstance(data, dict):
        raise TypeError("Ledger must be an object")
    metadata: list[str] = []
    validation: list[str] = []

    def records(field: str) -> dict[str, dict[str, Any]]:
        values = data.get(field, [])
        if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
            raise ValueError(f"{field} must be a list of objects")
        result = {}
        for item in values:
            identity = item.get("id")
            if not isinstance(identity, str) or not identity:
                metadata.append(
                    f"{field}: record has no id (legacy records need explicit reconciliation)"
                )
            elif identity in result:
                raise ValueError(f"{field}: duplicate id {identity}")
            else:
                result[identity] = item
        return result

    batches, findings, validations = (
        records(key) for key in ("remediation_batches", "findings", "validation_runs")
    )
    batch = batches.get(batch_id)
    if batch is None:
        raise ValueError(f"Unknown batch: {batch_id}")

    def references(field: str) -> list[str]:
        value = batch.get(field)
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(v, str) or not v.strip() for v in value)
        ):
            metadata.append(f"{batch_id}: {field} must be a non-empty list of strings")
            return []
        if len(value) != len(set(value)):
            metadata.append(f"{batch_id}: duplicate {field}")
        return value

    for identity in references("finding_ids"):
        finding = findings.get(identity)
        if finding is None:
            metadata.append(f"Unknown finding: {identity}")
            continue
        if finding.get("disposition", "defect") == "defect":
            for field in ("remediation", "regression"):
                if (
                    not isinstance(finding.get(field), str)
                    or not finding[field].strip()
                ):
                    metadata.append(f"{identity}: missing {field}")
    passed = set()
    for identity in references("validation_ids"):
        evidence = validations.get(identity)
        if evidence is None:
            metadata.append(f"Unknown validation: {identity}")
            continue
        command = evidence.get("command")
        if not isinstance(command, str) or not command.strip():
            metadata.append(f"{identity}: missing command")
        elif (
            evidence.get("status") != "passed"
            or evidence.get("snapshot_digest") != snapshot_digest
        ):
            validation.append(
                f"{identity}: validation failed, is absent, or belongs to another snapshot"
            )
        else:
            passed.add(command)
    for command in references("required_commands"):
        if command not in passed:
            validation.append(f"No current passing evidence: {command}")
    return {"metadata_gaps": metadata, "validation_gaps": validation}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument(
        "--environment",
        required=True,
        help="Observed runtime/toolchain/fixture revision, not a generic label",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Additional ignored or external dependency file",
    )
    parser.add_argument(
        "--compare",
        type=Path,
        help="Earlier JSON output (stored outside the fingerprinted tree)",
    )
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--batch")
    args = parser.parse_args()
    if bool(args.ledger) != bool(args.batch):
        parser.error("--ledger and --batch must be supplied together")
    try:
        current = snapshot(args.repo, args.base, args.environment, args.input)
        result: dict[str, Any] = {"snapshot": current}
        if args.compare:
            previous = json.loads(args.compare.read_text())["snapshot"]
            result.update(compare(previous, current))
        if args.ledger:
            result.update(
                bookkeeping(
                    json.loads(args.ledger.read_text()), args.batch, current["digest"]
                )
            )
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
        return (
            1
            if (
                result.get("snapshot_matches") is False
                or result.get("metadata_gaps")
                or result.get("validation_gaps")
            )
            else 0
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
