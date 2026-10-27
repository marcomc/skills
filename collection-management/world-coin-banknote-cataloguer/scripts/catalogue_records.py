#!/usr/bin/env python3
"""Plan collection actions and pair structured currency-side observations."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

ACTION_INSERT = "INSERT"
ACTION_UPDATE_QUANTITY = "UPDATE QUANTITY"
ACTION_SKIP_DUPLICATE = "SKIP EXACT DUPLICATE"
ACTION_NEEDS_REVIEW = "NEEDS REVIEW"


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _fold(value: Any) -> str:
    return " ".join(_text(value).casefold().split())


def _require_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer, not text or boolean")
    return value


def _is_high(record: dict[str, Any]) -> bool:
    return _fold(record.get("confidence")) == "high"


def _banknote_identity(record: dict[str, Any]) -> tuple[str, ...]:
    return (
        _fold(record.get("country")),
        _fold(record.get("denomination")),
        _fold(record.get("currency_code")),
        _fold(record.get("series")),
        _fold(record.get("serial")),
    )


def _banknote_serial(record: dict[str, Any]) -> str:
    return _fold(record.get("serial"))


def _coin_identity(record: dict[str, Any]) -> tuple[str, ...]:
    return (
        _fold(record.get("object_class", "coin")),
        _fold(record.get("country")),
        _fold(record.get("denomination")),
        _fold(record.get("currency_code")),
        _fold(record.get("series")),
        _fold(record.get("obverse")),
        _fold(record.get("reverse")),
    )


def _complete_identity(identity: tuple[str, ...]) -> bool:
    return all(identity)


def classify_banknote(
    incoming: dict[str, Any], existing: list[dict[str, Any]]
) -> dict[str, Any]:
    """Classify one banknote without treating a missing serial as identity."""
    identity = _banknote_identity(incoming)
    if not _is_high(incoming) or not _complete_identity(identity):
        return {"action": ACTION_NEEDS_REVIEW, "reason": "uncertain identity or serial"}
    for row in existing:
        if _banknote_serial(row) != _banknote_serial(incoming):
            continue
        if _banknote_identity(row) == identity:
            return {
                "action": ACTION_SKIP_DUPLICATE,
                "existing_row": row.get("row"),
                "reason": "exact banknote identity and serial",
            }
        return {
            "action": ACTION_NEEDS_REVIEW,
            "existing_row": row.get("row"),
            "reason": "serial already exists with conflicting metadata",
        }
    return {"action": ACTION_INSERT, "reason": "new physical banknote serial"}


def classify_coin(
    incoming: dict[str, Any], existing: list[dict[str, Any]]
) -> dict[str, Any]:
    """Classify one coin using exact issue and side-design identity."""
    identity = _coin_identity(incoming)
    object_class = _fold(incoming.get("object_class", "coin"))
    sovereign_currency = object_class not in {
        "medal",
        "token",
        "novelty",
        "private issue",
    }
    required_fields = (
        incoming.get("country"),
        incoming.get("series"),
        incoming.get("obverse"),
        incoming.get("reverse"),
    )
    if sovereign_currency:
        required_fields += (incoming.get("denomination"), incoming.get("currency_code"))
    else:
        required_fields += (incoming.get("issue_name"),)
    if not _is_high(incoming) or not all(_fold(value) for value in required_fields):
        return {"action": ACTION_NEEDS_REVIEW, "reason": "incomplete exact coin issue"}
    for row in existing:
        if _coin_identity(row) == identity:
            incoming_issue = _fold(incoming.get("issue_name"))
            existing_issue = _fold(row.get("issue_name"))
            if incoming_issue and existing_issue and incoming_issue != existing_issue:
                return {
                    "action": ACTION_NEEDS_REVIEW,
                    "existing_row": row.get("row"),
                    "reason": "matching sides have conflicting issue names",
                }
            quantity = row.get("quantity", 1)
            if (
                isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or quantity < 0
            ):
                return {
                    "action": ACTION_NEEDS_REVIEW,
                    "reason": "invalid existing quantity",
                }
            return {
                "action": ACTION_UPDATE_QUANTITY,
                "existing_row": row.get("row"),
                "old_quantity": quantity,
                "new_quantity": quantity + 1,
                "reason": "exact coin issue and design",
            }
    return {"action": ACTION_INSERT, "reason": "distinct coin issue or design"}


HEADER_ALIASES = {
    "album_year": ("album babbo",),
    "country": ("paese",),
    "denomination": ("valore",),
    "currency_symbol": ("simbolo", "s.lo"),
    "currency_code": ("codice",),
    "currency_name": ("valuta",),
    "series": ("serie",),
    "serial": ("numero di serie",),
    "notes": ("note",),
    "obverse": ("dritto",),
    "reverse": ("rovescio",),
    "quantity": ("quantitá", "quantità"),
    "type": ("tipo", "type/category", "type", "categoria"),
    "base_value": ("valore base",),
}


def prepare_row(headers: list[Any], record: dict[str, Any]) -> list[Any]:
    """Align values to live headers and keep unrecognized columns empty."""
    album_year = _require_integer(record.get("album_year"), "album_year")
    values = dict(record)
    values["album_year"] = album_year
    by_header: dict[str, Any] = {}
    for field, aliases in HEADER_ALIASES.items():
        if field in values:
            for alias in aliases:
                by_header[_fold(alias)] = values[field]
    return [by_header.get(_fold(header), "") for header in headers]


@dataclass(frozen=True)
class PairEvidence:
    score: int
    signals: tuple[str, ...]
    contradiction: str | None = None


def _pair_evidence(front: dict[str, Any], back: dict[str, Any]) -> PairEvidence:
    score = 0
    signals: list[str] = []
    weighted = (
        ("serial", 100, True),
        ("denomination", 30, True),
        ("country", 25, True),
        ("currency", 20, False),
        ("series", 15, False),
        ("dimensions", 8, False),
        ("design", 6, False),
        ("position", 1, False),
    )
    for field, weight, hard in weighted:
        left = _fold(front.get(field))
        right = _fold(back.get(field))
        if not left or not right:
            continue
        if left == right:
            score += weight
            signals.append(field)
        elif hard:
            return PairEvidence(
                score=-10_000, signals=tuple(signals), contradiction=field
            )
    return PairEvidence(score=score, signals=tuple(signals))


def _pair_is_sufficient(item: PairEvidence) -> bool:
    signals = set(item.signals)
    return "serial" in signals or (
        {"country", "denomination"}.issubset(signals)
        and bool(signals.intersection({"series", "dimensions", "design"}))
    )


def pair_sides(
    fronts: list[dict[str, Any]], backs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return a maximum-score one-to-one pairing with contradiction guards."""
    if len(fronts) != len(backs):
        raise ValueError("front and back observation counts must match")
    if len(fronts) > 16:
        raise ValueError("pairing helper supports at most 16 objects per batch")
    evidence = [[_pair_evidence(front, back) for back in backs] for front in fronts]

    @cache
    def solve(front_index: int, used_mask: int) -> tuple[int, tuple[int, ...]]:
        if front_index == len(fronts):
            return 0, ()
        best_score = -(10**9)
        best_pairs: tuple[int, ...] = ()
        for back_index in range(len(backs)):
            if used_mask & (1 << back_index):
                continue
            item = evidence[front_index][back_index]
            if item.contradiction or not _pair_is_sufficient(item):
                continue
            tail_score, tail_pairs = solve(
                front_index + 1, used_mask | (1 << back_index)
            )
            total = item.score + tail_score
            if total > best_score:
                best_score = total
                best_pairs = (back_index,) + tail_pairs
        return best_score, best_pairs

    _, indexes = solve(0, 0)
    if len(indexes) != len(fronts):
        raise ValueError("no contradiction-free complete pairing exists")
    for front_index, back_index in enumerate(indexes):
        selected = evidence[front_index][back_index]
        selected_score = selected.score - (1 if "position" in selected.signals else 0)
        equally_supported = 0
        for item in evidence[front_index]:
            if item.contradiction or not _pair_is_sufficient(item):
                continue
            score = item.score - (1 if "position" in item.signals else 0)
            if score == selected_score:
                equally_supported += 1
        if equally_supported > 1:
            raise ValueError("pairing is ambiguous without photograph position")
    result = []
    for front_index, back_index in enumerate(indexes):
        item = evidence[front_index][back_index]
        result.append(
            {
                "front_id": fronts[front_index].get("id", front_index),
                "back_id": backs[back_index].get("id", back_index),
                "score": item.score,
                "signals": list(item.signals),
            }
        )
    return result


def plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, reviewable audit plan from structured records."""
    album_year = _require_integer(payload.get("album_year"), "album_year")
    existing_banknotes = payload.get("existing_banknotes", [])
    projected_coins = [dict(row) for row in payload.get("existing_coins", [])]
    decisions = []
    coin_groups: list[dict[str, Any]] = []
    insert_groups: dict[tuple[str, ...], dict[str, Any]] = {}
    update_groups: dict[tuple[Any, tuple[str, ...]], dict[str, Any]] = {}
    for record in payload.get("banknotes", []):
        decision = classify_banknote(record, existing_banknotes)
        decisions.append({"id": record.get("id"), "type": "banknote", **decision})
    for record in payload.get("coins", []):
        decision = classify_coin(record, projected_coins)
        decisions.append({"id": record.get("id"), "type": "coin", **decision})
        decision_index = len(decisions) - 1
        action = decision["action"]
        if action == ACTION_INSERT:
            identity = _coin_identity(record)
            issue_name = _fold(record.get("issue_name"))
            group = insert_groups.get(identity)
            if group is None:
                group = {
                    "action": ACTION_INSERT,
                    "identity": identity,
                    "issue_names": set(),
                    "record": dict(record),
                    "specimen_ids": [],
                    "decision_indexes": [],
                }
                insert_groups[identity] = group
                coin_groups.append(group)
            if issue_name:
                group["issue_names"].add(issue_name)
                if not _fold(group["record"].get("issue_name")):
                    group["record"] = dict(record)
            specimen_id = record.get("id")
            if specimen_id is not None:
                group["specimen_ids"].append(specimen_id)
            group["decision_indexes"].append(decision_index)
            continue
        if action != ACTION_UPDATE_QUANTITY:
            continue

        # Each decision represents one specimen. Project prior planned quantity
        # updates so a later specimen targeting the same live row increments
        # from the preceding planned value instead of re-proposing old + 1.
        identity = _coin_identity(record)
        matched = next(
            (row for row in projected_coins if _coin_identity(row) == identity),
            None,
        )
        if matched is not None:
            matched["quantity"] = decision["new_quantity"]
        update_key = (decision.get("existing_row"), identity)
        group = update_groups.get(update_key)
        if group is None:
            group = {
                "action": ACTION_UPDATE_QUANTITY,
                "existing_row": decision.get("existing_row"),
                "identity": identity,
                "old_quantity": decision["old_quantity"],
                "new_quantity": decision["new_quantity"],
                "specimen_ids": [],
                "decision_indexes": [],
            }
            update_groups[update_key] = group
            coin_groups.append(group)
        else:
            group["new_quantity"] = decision["new_quantity"]
        specimen_id = record.get("id")
        if specimen_id is not None:
            group["specimen_ids"].append(specimen_id)
        group["decision_indexes"].append(decision_index)

    for group in insert_groups.values():
        if len(group["issue_names"]) > 1:
            group["action"] = ACTION_NEEDS_REVIEW
            for index in group["decision_indexes"]:
                decisions[index]["action"] = ACTION_NEEDS_REVIEW
                decisions[index]["reason"] = (
                    "matching batch specimens have conflicting issue names"
                )

    coin_write_operations = []
    for group in coin_groups:
        if group["action"] == ACTION_NEEDS_REVIEW:
            continue
        if group["action"] == ACTION_INSERT:
            row_record = dict(group["record"])
            row_record["quantity"] = len(group["decision_indexes"])
            operation = {
                "type": "coin",
                "action": ACTION_INSERT,
                "record": row_record,
                "quantity": row_record["quantity"],
                "specimen_ids": group["specimen_ids"],
                "decision_indexes": group["decision_indexes"],
            }
        else:
            operation = {
                "type": "coin",
                "action": ACTION_UPDATE_QUANTITY,
                "existing_row": group["existing_row"],
                "identity": list(group["identity"]),
                "old_quantity": group["old_quantity"],
                "new_quantity": group["new_quantity"],
                "specimen_ids": group["specimen_ids"],
                "decision_indexes": group["decision_indexes"],
            }
        operation_index = len(coin_write_operations)
        coin_write_operations.append(operation)
        for index in group["decision_indexes"]:
            decisions[index]["coin_operation_index"] = operation_index
    counts: dict[str, int] = {}
    for decision in decisions:
        counts[decision["action"]] = counts.get(decision["action"], 0) + 1
    write_counts: dict[str, int] = {}
    for operation in coin_write_operations:
        action = operation["action"]
        write_counts[action] = write_counts.get(action, 0) + 1
    return {
        "album_year": album_year,
        "decisions": decisions,
        "coin_write_operations": coin_write_operations,
        "summary": counts,
        "coin_write_summary": write_counts,
    }


def _load_json(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan", help="classify proposed records")
    plan_parser.add_argument("input", help="JSON input path, or - for stdin")
    pair_parser = subparsers.add_parser("pair", help="pair front and back observations")
    pair_parser.add_argument("input", help="JSON input path, or - for stdin")
    args = parser.parse_args()
    try:
        payload = _load_json(args.input)
        result = (
            plan(payload)
            if args.command == "plan"
            else pair_sides(payload.get("fronts", []), payload.get("backs", []))
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
