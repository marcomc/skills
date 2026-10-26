#!/usr/bin/env python3
"""Classify a Codex PR remediation ledger for pathological loop risk."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

STATES = ("NORMAL", "SUSPECTED", "RECOVERY", "BLOCKED")
SEVERITY = {state: index for index, state in enumerate(STATES)}
DECISIONS = {
    "NORMAL": "continue",
    "SUSPECTED": "run_convergence_sweep",
    "RECOVERY": "run_recovery_epoch",
    "BLOCKED": "stop_sick_loop",
}
NEXT_ACTIONS = {
    "NORMAL": "Continue the standard remediation workflow.",
    "SUSPECTED": (
        "Stop local patching and complete a convergence sweep before pushing."
    ),
    "RECOVERY": ("Freeze review requests and run the family's single recovery epoch."),
    "BLOCKED": (
        "Stop automatic remediation and report a redesign, rollback, or PR split."
    ),
}
DISPOSITIONS = {"defect", "false_positive", "intentional"}
ORIGINS = {
    "pre_existing",
    "missed_sibling",
    "remediation_regression",
    "independent",
    "unknown",
}


class LedgerError(ValueError):
    """Raised when the remediation ledger is malformed."""


def normalized_text(value: Any, field: str, *, optional: bool = False) -> str:
    """Normalize spelling, without claiming to resolve semantic equivalence."""
    if value is None and optional:
        return ""
    if not isinstance(value, str):
        raise LedgerError(f"{field} must be a string")
    normalized = " ".join(value.split()).casefold()
    if not normalized and not optional:
        raise LedgerError(f"{field} must not be empty")
    return normalized


def review_round(value: Any, field: str) -> int:
    """Validate and return a positive review-round number."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LedgerError(f"{field} must be a positive integer")
    return value


def family_key(item: dict[str, Any], context: str) -> tuple[str, str, str]:
    """Build the normalized family fingerprint for one ledger item."""
    return (
        normalized_text(item.get("root_cause_class"), f"{context}.root_cause_class"),
        normalized_text(item.get("invariant"), f"{context}.invariant"),
        normalized_text(item.get("boundary"), f"{context}.boundary", optional=True),
    )


def family_label(key: tuple[str, str, str]) -> str:
    """Render a stable human-readable family fingerprint."""
    parts = [key[0], key[1]]
    if key[2]:
        parts.append(key[2])
    return " :: ".join(parts)


def object_list(data: dict[str, Any], field: str) -> list[dict[str, Any]]:
    """Validate a top-level list of JSON objects."""
    value = data.get(field, [])
    if not isinstance(value, list):
        raise LedgerError(f"{field} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise LedgerError(f"{field}[{index}] must be an object")
    return value


def stable_id(value: Any, field: str) -> str:
    """Keep identifiers explicit and distinct from free-text descriptions."""
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", value):
        raise LedgerError(f"{field} must be a lowercase stable identifier")
    return value


class FamilyRegistry:
    """Resolve explicit IDs or an unambiguous legacy fingerprint, never fuzzy text."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_key: dict[tuple[str, str, str], str] = {}
        self.contracts: dict[str, str] = {}
        for index, contract in enumerate(object_list(data, "contracts")):
            context = f"contracts[{index}]"
            identity = stable_id(contract.get("id"), f"{context}.id")
            if identity in self.contracts:
                raise LedgerError(f"{context}.id duplicates a contract")
            self.contracts[identity] = normalized_text(
                contract.get("invariant"), f"{context}.invariant"
            )
        for index, family in enumerate(object_list(data, "families")):
            context = f"families[{index}]"
            identity = stable_id(family.get("id"), f"{context}.id")
            key = family_key(family, context)
            if identity in self.by_id or key in self.by_key:
                raise LedgerError(
                    f"{context} duplicates an ID or canonical fingerprint"
                )
            contract = family.get("contract_id")
            if contract is not None:
                stable_id(contract, f"{context}.contract_id")
                if contract not in self.contracts:
                    raise LedgerError(f"{context}.contract_id is not registered")
            self.by_id[identity] = {**family, "key": key}
            self.by_key[key] = identity

    def resolve(self, item: dict[str, Any], context: str) -> tuple[str, str, str]:
        identity = item.get("family_id")
        if identity is not None:
            identity = stable_id(identity, f"{context}.family_id")
            if identity not in self.by_id:
                raise LedgerError(f"{context}.family_id is not registered")
            family = self.by_id[identity]
            supplied = any(
                field in item for field in ("root_cause_class", "invariant", "boundary")
            )
            if supplied and family_key(item, context) != family["key"]:
                normalized_text(
                    item.get("family_evidence"), f"{context}.family_evidence"
                )
            return family["key"]
        key = family_key(item, context)
        # Exact legacy spellings naturally join an explicitly registered family.
        return key


def nonnegative_number(value: Any, context: str) -> float:
    """Reject booleans and non-finite cost data instead of emitting invalid JSON."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise LedgerError(f"{context} must be finite and non-negative")
    return float(value)


def analyze_ledger(data: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic loop-health state and supporting metrics."""
    if not isinstance(data, dict):
        raise LedgerError("ledger root must be an object")
    registry = FamilyRegistry(data)
    origins: dict[str, int] = defaultdict(int)
    warnings: list[str] = []
    completed_recoveries: dict[tuple[str, str, str], set[int]] = defaultdict(set)
    completed_sweeps: dict[tuple[str, str, str], set[int]] = defaultdict(set)

    families: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "finding_ids": [],
            "finding_rounds": [],
            "rounds": set(),
            "locations": set(),
            "remediation_batches": 0,
            "remediation_changed_lines": 0,
            "sweeps_after": [],
            "recoveries_after": [],
        }
    )
    defect_count = 0
    seen_finding_ids: set[str] = set()

    for index, finding in enumerate(object_list(data, "findings")):
        context = f"findings[{index}]"
        finding_id = normalized_text(finding.get("id"), f"{context}.id")
        if finding_id in seen_finding_ids:
            raise LedgerError(f"{context}.id duplicates an earlier finding")
        seen_finding_ids.add(finding_id)
        disposition = normalized_text(
            finding.get("disposition", "defect"), f"{context}.disposition"
        )
        if disposition not in DISPOSITIONS:
            allowed = ", ".join(sorted(DISPOSITIONS))
            raise LedgerError(f"{context}.disposition must be one of: {allowed}")
        if disposition != "defect":
            if "family_id" in finding:
                registry.resolve(finding, context)
            continue
        key = registry.resolve(finding, context)
        origin = finding.get("origin", "unknown")
        if not isinstance(origin, str) or origin not in ORIGINS:
            raise LedgerError(
                f"{context}.origin must be one of: {', '.join(sorted(ORIGINS))}"
            )
        if origin not in {"unknown", "pre_existing"}:
            normalized_text(
                finding.get("origin_evidence"), f"{context}.origin_evidence"
            )
        origins[origin] += 1
        round_number = review_round(
            finding.get("review_round"), f"{context}.review_round"
        )
        locations = finding.get("locations", [])
        if not isinstance(locations, list) or not all(
            isinstance(location, str) and location.strip() for location in locations
        ):
            raise LedgerError(
                f"{context}.locations must be a list of non-empty strings"
            )
        record = families[key]
        record["finding_ids"].append(finding_id)
        record["finding_rounds"].append(round_number)
        record["rounds"].add(round_number)
        record["locations"].update(
            normalized_text(location, f"{context}.locations") for location in locations
        )
        defect_count += 1

    marker_fields = (
        ("convergence_sweeps", "sweeps_after"),
        ("recovery_epochs", "recoveries_after"),
    )
    for top_level_field, record_field in marker_fields:
        for index, marker in enumerate(object_list(data, top_level_field)):
            context = f"{top_level_field}[{index}]"
            key = registry.resolve(marker, context)
            after_round = review_round(
                marker.get("after_review_round"),
                f"{context}.after_review_round",
            )
            families[key][record_field].append(after_round)
            if (
                top_level_field == "convergence_sweeps"
                and "completion_version" in marker
                and (
                    type(marker["completion_version"]) is not int
                    or marker["completion_version"] != 1
                )
            ):
                raise LedgerError(f"{context}.completion_version must be 1")
            if top_level_field == "recovery_epochs" or "completion_version" in marker:
                status = marker.get("status", "in_progress")
                if not isinstance(status, str) or status not in {
                    "in_progress",
                    "completed",
                }:
                    raise LedgerError(
                        f"{context}.status must be in_progress or completed"
                    )
                if status == "completed":
                    normalized_text(
                        marker.get("head", marker.get("replacement_head")),
                        f"{context}.head",
                    )
                    normalized_text(
                        marker.get("validation_evidence", marker.get("validation")),
                        f"{context}.validation_evidence",
                    )
                    completed_markers = (
                        completed_recoveries
                        if top_level_field == "recovery_epochs"
                        else completed_sweeps
                    )
                    completed_markers[key].add(after_round)

    remediation_changed_lines = 0
    remediation_location_touches: dict[str, int] = defaultdict(int)
    remediation_batches = object_list(data, "remediation_batches")
    seen_batch_ids: set[str] = set()
    for index, batch in enumerate(remediation_batches):
        context = f"remediation_batches[{index}]"
        if "id" in batch:
            identity = normalized_text(batch["id"], f"{context}.id")
            if identity in seen_batch_ids:
                raise LedgerError(f"{context}.id duplicates a remediation batch")
            seen_batch_ids.add(identity)
        review_round(
            batch.get("after_review_round"),
            f"{context}.after_review_round",
        )
        changed_lines = batch.get("changed_lines", 0)
        if (
            isinstance(changed_lines, bool)
            or not isinstance(changed_lines, int)
            or changed_lines < 0
        ):
            raise LedgerError(f"{context}.changed_lines must be non-negative")
        changed_locations = batch.get("changed_locations", [])
        if not isinstance(changed_locations, list) or not all(
            isinstance(location, str) and location.strip()
            for location in changed_locations
        ):
            raise LedgerError(
                f"{context}.changed_locations must be a list of non-empty strings"
            )
        for location in {
            normalized_text(location, f"{context}.changed_locations")
            for location in changed_locations
        }:
            remediation_location_touches[location] += 1
        remediation_changed_lines += changed_lines

        batch_families = batch.get("families", [])
        if not isinstance(batch_families, list) or not all(
            isinstance(item, dict) for item in batch_families
        ):
            raise LedgerError(f"{context}.families must be a list of objects")
        seen_batch_families: set[tuple[str, str, str]] = set()
        for family_index, batch_family in enumerate(batch_families):
            key = registry.resolve(batch_family, f"{context}.families[{family_index}]")
            if key in seen_batch_families:
                raise LedgerError(f"{context}.families duplicates a resolved family")
            seen_batch_families.add(key)
            families[key]["remediation_batches"] += 1
            families[key]["remediation_changed_lines"] += changed_lines

    validation_seconds = 0.0
    full_validation_runs = 0
    for index, validation in enumerate(object_list(data, "validation_runs")):
        context = f"validation_runs[{index}]"
        scope = normalized_text(validation.get("scope"), f"{context}.scope")
        duration = validation.get("duration_seconds", 0)
        validation_seconds += nonnegative_number(
            duration, f"{context}.duration_seconds"
        )
        if scope == "full":
            full_validation_runs += 1

    family_results = []
    all_rounds: set[int] = set()
    for key, record in families.items():
        rounds = sorted(record["rounds"])
        all_rounds.update(rounds)
        locations = sorted(record["locations"])
        sweeps_after = sorted(record["sweeps_after"])
        recoveries_after = sorted(record["recoveries_after"])
        state = "NORMAL"
        reasons = []

        if len(rounds) >= 2:
            state = "SUSPECTED"
            reasons.append("family appeared in at least two review rounds")
        elif len(record["finding_ids"]) >= 3 and len(locations) >= 2:
            state = "SUSPECTED"
            reasons.append("family spans at least three findings and two locations")

        if len(rounds) >= 3:
            state = "RECOVERY"
            reasons.append("family appeared in at least three review rounds")
        if any(
            round_number > swept_round
            for swept_round in sweeps_after
            for round_number in rounds
        ):
            state = "RECOVERY"
            reasons.append("family recurred after a convergence sweep")
        if (
            len(rounds) >= 2
            and len(record["finding_ids"]) >= 3
            and len(locations) >= 2
            and record["remediation_batches"] >= 2
        ):
            state = "RECOVERY"
            reasons.append("recurrence, sibling spread, and remediation churn coincide")

        if len(recoveries_after) > 1:
            state = "BLOCKED"
            reasons.append("family has more than one recovery epoch")
        if any(
            round_number > recovered_round
            for recovered_round in recoveries_after
            for round_number in rounds
        ):
            state = "BLOCKED"
            reasons.append("family recurred after its recovery epoch")

        sweep_complete = (
            state == "SUSPECTED"
            and bool(rounds)
            and any(swept >= rounds[-1] for swept in completed_sweeps[key])
        )
        if sweep_complete:
            state = "NORMAL"
            reasons = [
                "completed convergence sweep covers the latest defect without recovery"
            ]

        completed = (
            len(recoveries_after) == 1
            and recoveries_after[0] in completed_recoveries[key]
        )
        if completed and state != "BLOCKED":
            state = "NORMAL"
            reasons = ["completed recovery has no later defect in this family"]
        elif recoveries_after and state != "BLOCKED":
            state = "RECOVERY"
            reasons.append(
                "recovery has no explicit completion evidence; resume the existing epoch"
            )

        family_results.append(
            {
                "family_key": family_label(key),
                "family_id": registry.by_key.get(key),
                "completed_recovery_epoch": completed,
                "completed_convergence_sweep": sweep_complete,
                "state": state,
                "finding_count": len(record["finding_ids"]),
                "review_rounds": rounds,
                "location_count": len(locations),
                "remediation_batches": record["remediation_batches"],
                "remediation_changed_lines": record["remediation_changed_lines"],
                "convergence_sweeps_after": sweeps_after,
                "recovery_epochs_after": recoveries_after,
                "reasons": reasons,
            }
        )

    family_results.sort(key=lambda item: (-SEVERITY[item["state"]], item["family_key"]))
    state = family_results[0]["state"] if family_results else "NORMAL"
    highest_families = [
        item["family_key"] for item in family_results if item["state"] == state
    ]
    latest_round = max(all_rounds) if all_rounds else None
    latest_round_families = {
        key for key, record in families.items() if latest_round in record["rounds"]
    }
    latest_new_families = {
        key
        for key in latest_round_families
        if min(families[key]["rounds"]) == latest_round
    }
    latest_novelty_ratio = (
        len(latest_new_families) / len(latest_round_families)
        if latest_round_families
        else 1.0
    )
    recurring_defect_findings = sum(
        sum(
            round_number > min(record["rounds"])
            for round_number in record["finding_rounds"]
        )
        for record in families.values()
        if record["rounds"]
    )
    revisited_locations = sorted(
        location
        for location, touches in remediation_location_touches.items()
        if touches > 1
    )
    contract_results = []
    for identity, invariant in registry.contracts.items():
        keys = {
            family["key"]
            for family in registry.by_id.values()
            if family.get("contract_id") == identity
        }
        active = [
            families[key] for key in keys if key in families and families[key]["rounds"]
        ]
        rounds = sorted({r for record in active for r in record["rounds"]})
        contract_results.append(
            {
                "contract_id": identity,
                "invariant": invariant,
                "family_count": len(active),
                "review_rounds": rounds,
                "latest_round_active": latest_round in rounds,
            }
        )
    # Advisory only: distinct causes under one contract must not consume a family's recovery epoch.
    contract_attention = [
        c["contract_id"]
        for c in contract_results
        if c["family_count"] >= 2
        and len(c["review_rounds"]) >= 3
        and c["latest_round_active"]
    ]
    telemetry: dict[str, dict[str, Any]] = {}
    seen_cost_ids: set[str] = set()
    for index, entry in enumerate(object_list(data, "cost_events")):
        context = f"cost_events[{index}]"
        identity = stable_id(entry.get("id"), f"{context}.id")
        if identity in seen_cost_ids:
            raise LedgerError(f"{context}.id duplicates a cost event")
        seen_cost_ids.add(identity)
        category = entry.get("category")
        if not isinstance(category, str) or category not in {
            "local",
            "audit",
            "test",
            "cloud_wait",
        }:
            raise LedgerError(
                f"{context}.category must be local, audit, test or cloud_wait"
            )
        bucket = telemetry.setdefault(category, {"events": 0, "observed_events": {}})
        bucket["events"] += 1
        for field in (
            "duration_seconds",
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
        ):
            if field in entry:
                value = nonnegative_number(entry[field], f"{context}.{field}")
                if field != "duration_seconds" and not value.is_integer():
                    raise LedgerError(f"{context}.{field} must be an integer")
                bucket[field] = bucket.get(field, 0) + value
                bucket["observed_events"][field] = (
                    bucket["observed_events"].get(field, 0) + 1
                )
        if entry.get("cached_input_tokens", 0) > entry.get(
            "input_tokens", float("inf")
        ):
            raise LedgerError(f"{context}.cached_input_tokens exceeds input_tokens")
    if any(registry.by_key.get(key) is None for key in families):
        warnings.append(
            "Legacy text identity is in use; reconcile families before assigning stable IDs."
        )
    return {
        "state": state,
        "decision": DECISIONS[state],
        "next_action": NEXT_ACTIONS[state],
        "highest_severity_families": highest_families,
        "metrics": {
            "defect_findings": defect_count,
            "recurring_defect_findings": recurring_defect_findings,
            "review_rounds": sorted(all_rounds),
            "latest_round": latest_round,
            "latest_round_family_count": len(latest_round_families),
            "latest_round_new_family_count": len(latest_new_families),
            "latest_round_novelty_ratio": latest_novelty_ratio,
            "remediation_batches": len(remediation_batches),
            "remediation_changed_lines": remediation_changed_lines,
            "revisited_remediation_locations": revisited_locations,
            "full_validation_runs": full_validation_runs,
            "validation_seconds": validation_seconds,
            "finding_origins": dict(origins),
        },
        "families": family_results,
        "contracts": contract_results,
        "convergence_attention": contract_attention,
        "costs_by_category": telemetry,
        "warnings": warnings,
    }


def load_ledger(input_path: str) -> dict[str, Any]:
    """Load a ledger object from a file or standard input."""
    try:
        if input_path == "-":
            value = json.load(sys.stdin)
        else:
            with Path(input_path).open(encoding="utf-8") as handle:
                value = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise LedgerError(str(error)) from error
    if not isinstance(value, dict):
        raise LedgerError("ledger root must be an object")
    return value


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", help="JSON ledger path, or - for standard input")
    return parser.parse_args()


def main() -> int:
    """Run the command-line analyzer."""
    args = parse_args()
    try:
        result = analyze_ledger(load_ledger(args.ledger))
    except LedgerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
