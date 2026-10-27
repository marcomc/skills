"""Tests for the generic remediation-loop health analyzer."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any


def load_analyzer() -> ModuleType:
    """Load the adjacent analyzer without requiring a Python package."""
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "analyze_remediation_loop.py"
    )
    spec = importlib.util.spec_from_file_location(
        "analyze_remediation_loop", script_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZER = load_analyzer()


def finding(
    finding_id: str,
    round_number: int,
    root_cause: str,
    invariant: str,
    boundary: str = "",
    locations: list[str] | None = None,
    disposition: str = "defect",
) -> dict[str, Any]:
    """Build one compact synthetic finding."""
    return {
        "id": finding_id,
        "review_round": round_number,
        "root_cause_class": root_cause,
        "invariant": invariant,
        "boundary": boundary,
        "locations": locations or [],
        "disposition": disposition,
    }


def marker(
    round_number: int,
    root_cause: str,
    invariant: str,
    boundary: str = "",
) -> dict[str, Any]:
    """Build a convergence or recovery marker."""
    return {
        "root_cause_class": root_cause,
        "invariant": invariant,
        "boundary": boundary,
        "after_review_round": round_number,
    }


class AnalyzeLedgerTests(unittest.TestCase):
    """Exercise generic state transitions without project-specific fixtures."""

    def test_unrelated_families_remain_normal(self) -> None:
        ledger = {
            "findings": [
                finding("a", 1, "validation order", "reject before mutation"),
                finding("b", 2, "cleanup ownership", "preserve prior workers"),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "NORMAL")

    def test_same_family_in_two_rounds_is_suspected(self) -> None:
        ledger = {
            "findings": [
                finding("a", 1, "schema drift", "all consumers use one schema"),
                finding("b", 2, "Schema   Drift", "all consumers use one schema"),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "SUSPECTED")
        self.assertEqual(result["decision"], "run_convergence_sweep")

    def test_broad_class_with_different_invariants_is_not_conflated(self) -> None:
        ledger = {
            "findings": [
                finding("a", 1, "identity", "names are unique"),
                finding("b", 2, "identity", "owners are authenticated"),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "NORMAL")
        self.assertEqual(len(result["families"]), 2)

    def test_different_boundaries_are_not_conflated(self) -> None:
        ledger = {
            "findings": [
                finding("a", 1, "ownership", "preserve foreign state", "startup"),
                finding("b", 2, "ownership", "preserve foreign state", "cleanup"),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "NORMAL")
        self.assertEqual(len(result["families"]), 2)

    def test_sibling_spread_in_one_round_is_suspected(self) -> None:
        base = ("partial publication", "failure preserves usable state")
        ledger = {
            "findings": [
                finding("a", 1, *base, locations=["writer"]),
                finding("b", 1, *base, locations=["recovery"]),
                finding("c", 1, *base, locations=["consumer"]),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "SUSPECTED")

    def test_third_round_requires_recovery(self) -> None:
        base = ("lifecycle leak", "cleanup owns only invocation state")
        ledger = {
            "findings": [
                finding("a", 1, *base),
                finding("b", 2, *base),
                finding("c", 3, *base),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "RECOVERY")
        self.assertEqual(result["decision"], "run_recovery_epoch")

    def test_recurrence_after_sweep_requires_recovery(self) -> None:
        base = ("alias collision", "outputs have distinct identities")
        ledger = {
            "findings": [finding("a", 1, *base), finding("b", 2, *base)],
            "convergence_sweeps": [marker(1, *base)],
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "RECOVERY")

    def test_recurrence_spread_and_churn_require_recovery(self) -> None:
        base = ("state drift", "all lifecycle paths use one state contract")
        family_marker = marker(1, *base)
        family_marker.pop("after_review_round")
        ledger = {
            "findings": [
                finding("a", 1, *base, locations=["writer"]),
                finding("b", 2, *base, locations=["reader"]),
                finding("c", 2, *base, locations=["recovery"]),
            ],
            "remediation_batches": [
                {
                    "after_review_round": 1,
                    "families": [family_marker],
                    "changed_locations": ["writer", "shared state"],
                    "changed_lines": 30,
                },
                {
                    "after_review_round": 2,
                    "families": [family_marker],
                    "changed_locations": ["reader", "shared state"],
                    "changed_lines": 40,
                },
            ],
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "RECOVERY")
        self.assertEqual(result["metrics"]["remediation_changed_lines"], 70)
        self.assertEqual(
            result["metrics"]["revisited_remediation_locations"], ["shared state"]
        )

    def test_recurrence_after_recovery_is_blocked(self) -> None:
        base = (
            "untrusted replacement",
            "existing targets require managed provenance",
            "privileged publication",
        )
        ledger = {
            "findings": [finding("a", 1, *base), finding("b", 3, *base)],
            "recovery_epochs": [marker(2, *base)],
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["decision"], "stop_sick_loop")

    def test_non_defects_do_not_drive_recurrence(self) -> None:
        base = ("policy choice", "document intentional behaviour")
        ledger = {
            "findings": [
                finding("a", 1, *base, disposition="intentional"),
                finding("b", 2, *base, disposition="false_positive"),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["state"], "NORMAL")
        self.assertEqual(result["metrics"]["defect_findings"], 0)

    def test_validation_cost_is_summarized(self) -> None:
        ledger = {
            "validation_runs": [
                {"scope": "targeted", "duration_seconds": 10},
                {"scope": "full", "duration_seconds": 90.5},
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["metrics"]["full_validation_runs"], 1)
        self.assertEqual(result["metrics"]["validation_seconds"], 100.5)

    def test_latest_round_novelty_is_summarized(self) -> None:
        ledger = {
            "findings": [
                finding("a", 1, "schema", "all readers use one schema"),
                finding("b", 2, "schema", "all readers use one schema"),
                finding("c", 2, "cleanup", "preserve unrelated state"),
            ]
        }

        result = ANALYZER.analyze_ledger(ledger)

        self.assertEqual(result["metrics"]["recurring_defect_findings"], 1)
        self.assertEqual(result["metrics"]["latest_round_family_count"], 2)
        self.assertEqual(result["metrics"]["latest_round_new_family_count"], 1)
        self.assertEqual(result["metrics"]["latest_round_novelty_ratio"], 0.5)

    def test_duplicate_finding_id_fails_closed(self) -> None:
        ledger = {
            "findings": [
                finding("same", 1, "schema", "validate once"),
                finding("same", 2, "cleanup", "clean once"),
            ]
        }

        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(ledger)

    def test_invalid_disposition_fails_closed(self) -> None:
        ledger = {
            "findings": [
                finding(
                    "a",
                    1,
                    "validation",
                    "classifications are explicit",
                    disposition="unknown",
                )
            ]
        }

        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(ledger)


if __name__ == "__main__":
    unittest.main()
