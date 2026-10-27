#!/usr/bin/env python3
"""Reconcile a review plan with observed evidence; do not execute or approve code."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from analyze_remediation_loop import analyze_ledger
from prepare_remediation_audit import compare, digest, fingerprint


def nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def records(values: Any, field: str) -> dict[str, dict[str, Any]]:
    if not isinstance(values, list):
        raise TypeError(f"{field} must be a list")
    result = {}
    for item in values:
        if not isinstance(item, dict):
            raise TypeError(f"{field} entries must be objects")
        identity = nonempty(item.get("id"), f"{field}.id")
        if identity in result:
            raise ValueError(f"Duplicate {field} id: {identity}")
        result[identity] = item
    return result


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"Expected an object: {path}")
    return value


def policy_fingerprint(paths: list[str], root: Path) -> str:
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("policy_files must be non-empty and unique")
    material = {}
    for name in paths:
        nonempty(name, "policy_files entry")
        value = fingerprint(root / Path(name).expanduser())
        if value is None:
            raise ValueError(f"Missing policy file: {name}")
        material[name] = value
    return digest(material)


def selectors(requirement: dict[str, Any]) -> list[str] | None:
    inputs = requirement.get("inputs")
    if inputs is None:
        return None  # The complete snapshot is the conservative default.
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("inputs must be null or a non-empty list")
    for name in inputs:
        nonempty(name, "input selector")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or name in {".", "./"}:
            raise ValueError(
                f"Use repository-relative file/directory selectors: {name}"
            )
        if (name.removesuffix("/")) != path.as_posix():
            raise ValueError(f"Use a normalized selector: {name}")
        if any(char in name for char in "*?[]\\"):
            raise ValueError("Use exact files or directories ending in /, not globs")
    nonempty(requirement.get("dependency_evidence"), "dependency_evidence")
    return inputs


def matching_inputs(
    previous: dict[str, Any], current: dict[str, Any], inputs: list[str] | None
) -> bool:
    delta = compare(previous, current)  # Also rejects forged/incomplete digests.
    if inputs is None:
        return delta["snapshot_matches"]
    if any(field != "files" for field in delta["changed_components"]):
        return False  # Environment, base, repo and extra dependencies are global.
    return not any(
        name == selector or (selector.endswith("/") and name.startswith(selector))
        for name in delta["changed_paths"]
        for selector in inputs
    )


def evaluate(
    data: dict[str, Any], current: dict[str, Any], root: Path
) -> dict[str, Any]:
    compare(current, current)
    run = data["review_run"]
    if not isinstance(run, dict):
        raise TypeError("review_run must be an object")
    nonempty(run.get("id"), "review_run.id")
    if run.get("depth") not in {"bounded", "expanded"}:
        raise ValueError("review_run.depth must be bounded or expanded")
    nonempty(run.get("risk_reason"), "review_run.risk_reason")
    files = run.get("policy_files")
    if not isinstance(files, list):
        raise TypeError("policy_files must be a list")
    policy = policy_fingerprint(files, root)
    policy_changed = run.get("policy_digest") != policy
    requirements = records(run.get("requirements"), "requirements")
    evidence = records(data.get("review_evidence", []), "review_evidence")
    findings = records(data.get("findings", []), "findings")
    pending, reused, optional, open_findings = [], [], [], []
    requirement_digests = {}
    required_kinds = set()
    for identity, requirement in requirements.items():
        kind = requirement.get("kind")
        if kind not in {"review", "validation"}:
            raise ValueError("Requirement kind must be review or validation")
        if not isinstance(requirement.get("required"), bool):
            raise TypeError("Requirement required must be explicit boolean")
        nonempty(requirement.get("coverage"), "requirement.coverage")
        if kind == "validation":
            nonempty(requirement.get("command"), "validation command")
        if (
            not isinstance(requirement.get("feedback_revision"), int)
            or isinstance(requirement["feedback_revision"], bool)
            or requirement["feedback_revision"] < 0
        ):
            raise ValueError("feedback_revision must be a non-negative integer")
        inputs = selectors(requirement)
        if not requirement["required"]:
            nonempty(requirement.get("optional_reason"), "optional_reason")
        else:
            required_kinds.add(kind)
        signature = digest(requirement)
        requirement_digests[identity] = signature
        # Append evidence chronologically. A later failure invalidates an older PASS.
        attempts = [e for e in evidence.values() if e.get("requirement_id") == identity]
        latest = attempts[-1] if attempts else None
        valid = False
        if latest is not None:
            source = nonempty(latest.get("source"), "evidence source")
            source_path = root / Path(source).expanduser()
            observed = source_path.is_file() and source_path.stat().st_size > 0
            if latest.get("status") not in {"passed", "failed", "unknown"}:
                raise ValueError("Evidence status must be passed, failed or unknown")
            if (
                observed
                and latest["status"] == "passed"
                and latest.get("policy_digest") == policy
                and latest.get("requirement_digest") == signature
                and not policy_changed
            ):
                previous = read_object(
                    root / nonempty(latest.get("snapshot"), "snapshot")
                )["snapshot"]
                valid = matching_inputs(previous, current, inputs)
                if kind == "review":
                    valid = valid and bool(latest.get("reviewer"))
                    if requirement.get("independent") is True:
                        valid = valid and latest.get("independent") is True
        if valid:
            reused.append(identity)
        elif requirement["required"]:
            pending.append(identity)
        else:
            optional.append(identity)
    if required_kinds != {"review", "validation"}:
        raise ValueError("The baseline needs a required review and required validation")
    for item in evidence.values():
        if item.get("requirement_id") not in requirements:
            raise ValueError(f"Unknown requirement: {item.get('requirement_id')}")
    for identity, finding in findings.items():
        disposition = finding.get("disposition", "defect")
        if disposition not in {"defect", "false_positive", "intentional"}:
            raise ValueError(f"Unknown finding disposition: {disposition}")
        if disposition == "defect":
            if finding.get("status") != "resolved" or not finding.get(
                "resolution_evidence"
            ):
                open_findings.append(identity)
        elif not finding.get("disposition_evidence"):
            open_findings.append(identity)
    health = (
        analyze_ledger(data) if findings or data.get("remediation_batches") else None
    )
    health_state = health["state"] if health else "NORMAL"
    block = run.get("blocked_reason")
    if block is not None:
        nonempty(block, "blocked_reason")
    status = (
        "BLOCKED"
        if block or policy_changed or health_state == "BLOCKED"
        else (
            "NEEDS_WORK"
            if pending
            or open_findings
            or health_state != "NORMAL"
            or run.get("coverage_reviewed") is not True
            else "READY"
        )
    )
    return {
        "mechanical_status": status,
        "semantic_approval": False,
        "health_state": health_state,
        "policy_digest": policy,
        "policy_changed": policy_changed,
        "requirement_digests": requirement_digests,
        "reused_check_ids": reused,
        "pending_check_ids": pending,
        "optional_pending_check_ids": optional,
        "open_finding_ids": open_findings,
        "coverage_reviewed": run.get("coverage_reviewed") is True,
        "blocked_reason": block,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(
            read_object(args.ledger),
            read_object(args.snapshot)["snapshot"],
            args.ledger.resolve().parent,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["mechanical_status"] == "READY" else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
