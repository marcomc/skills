"""Behavioral replay of family identity, recovery and cost accounting contracts."""

import copy
import unittest

from test_analyze_remediation_loop import ANALYZER, finding, marker


def ledger():
    return {
        "contracts": [
            {"id": "loading", "invariant": "load and restore share one budget"}
        ],
        "families": [
            {
                "id": "attempt-budget",
                "contract_id": "loading",
                "root_cause_class": "failed attempts bypass cumulative budget",
                "invariant": "each failed load consumes the shared attempt budget",
                "boundary": "catalog load",
            }
        ],
        "findings": [
            {"id": "f1", "review_round": 1, "family_id": "attempt-budget"},
            {"id": "f2", "review_round": 2, "family_id": "attempt-budget"},
        ],
    }


class ConvergenceCompletionTests(unittest.TestCase):
    def test_completed_sweep_clears_suspicion_without_recovery(self):
        data = ledger()
        data["convergence_sweeps"] = [
            {
                "family_id": "attempt-budget",
                "after_review_round": 2,
                "status": "completed",
                "head": "current-tree",
                "validation_evidence": "audit and entrypoint cases",
                "completion_version": 1,
            }
        ]
        result = ANALYZER.analyze_ledger(data)
        self.assertEqual(result["state"], "NORMAL")
        self.assertTrue(result["families"][0]["completed_convergence_sweep"])
        self.assertFalse(result["families"][0]["completed_recovery_epoch"])
        data["findings"].append(
            {"id": "f3", "family_id": "attempt-budget", "review_round": 3}
        )
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "RECOVERY")
        data["convergence_sweeps"][0]["after_review_round"] = 3
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "RECOVERY")

    def test_unfinished_or_unproven_sweep_does_not_clear_suspicion(self):
        data = ledger()
        data["convergence_sweeps"] = [
            {"family_id": "attempt-budget", "after_review_round": 2}
        ]
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "SUSPECTED")
        data["convergence_sweeps"][0].update(status="completed", completion_version=1)
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)

    def test_legacy_free_text_completion_remains_readable_without_becoming_pass(self):
        data = ledger()
        data["convergence_sweeps"] = [
            {
                "family_id": "attempt-budget",
                "after_review_round": 2,
                "status": "completed; historical checks PASS",
                "evidence": "legacy report",
            }
        ]
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "SUSPECTED")


class StableFamiliesTests(unittest.TestCase):
    def test_paraphrased_evidence_retains_family(self):
        data = ledger()
        data["findings"][1].update(
            root_cause_class="cumulative budget omits failed attempts",
            invariant=data["families"][0]["invariant"],
            boundary="catalog load",
            family_evidence="Both paths skip charging the same shared counter on failure.",
        )
        result = ANALYZER.analyze_ledger(data)
        self.assertEqual(result["state"], "SUSPECTED")
        self.assertEqual(result["families"][0]["family_id"], "attempt-budget")
        self.assertEqual(result["metrics"]["recurring_defect_findings"], 1)

    def test_unexplained_semantic_override_is_rejected(self):
        data = ledger()
        data["findings"][1].update(
            root_cause_class="unrelated cause", invariant="different outcome"
        )
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)

    def test_exact_legacy_records_and_markers_join_registered_family(self):
        data = ledger()
        family = data["families"][0]
        data["findings"][0] = finding(
            "f1", 1, family["root_cause_class"], family["invariant"], family["boundary"]
        )
        data["convergence_sweeps"] = [
            marker(
                1, family["root_cause_class"], family["invariant"], family["boundary"]
            )
        ]
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "RECOVERY")

    def test_unknown_ids_and_duplicate_fingerprints_fail_closed(self):
        for mutate in (
            lambda d: d["findings"][0].update(family_id="missing"),
            lambda d: d["families"].append({**d["families"][0], "id": "new-spelling"}),
            lambda d: d["families"][0].update(contract_id="missing"),
            lambda d: d["families"][0].update(contract_id=[]),
        ):
            data = ledger()
            mutate(data)
            with self.subTest(data=data), self.assertRaises(ANALYZER.LedgerError):
                ANALYZER.analyze_ledger(data)

    def test_same_contract_different_mechanisms_are_not_recovery(self):
        data = ledger()
        data["findings"] = []
        for number in range(3):
            identity = f"budget-{number}"
            data["families"].append(
                {
                    **data["families"][0],
                    "id": identity,
                    "root_cause_class": f"distinct mechanism {number}",
                }
            )
            data["findings"].append(
                {"id": f"f{number}", "review_round": number + 1, "family_id": identity}
            )
        result = ANALYZER.analyze_ledger(data)
        self.assertEqual(result["state"], "NORMAL")
        self.assertEqual(result["convergence_attention"], ["loading"])

    def test_completed_recovery_is_historical_until_later_recurrence(self):
        data = ledger()
        data["recovery_epochs"] = [
            {
                "family_id": "attempt-budget",
                "after_review_round": 2,
                "status": "completed",
                "head": "reviewed-head",
                "validation_evidence": "focused and integrated gate passed",
            }
        ]
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "NORMAL")
        data["findings"].append(
            {"id": "f3", "family_id": "attempt-budget", "review_round": 3}
        )
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "BLOCKED")

    def test_duplicate_resolved_family_or_batch_cannot_inflate_recovery(self):
        data = ledger()
        data["remediation_batches"] = [
            {
                "id": "b1",
                "after_review_round": 2,
                "families": [{"family_id": "attempt-budget"}, data["families"][0]],
            }
        ]
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)
        data["remediation_batches"][0]["families"].pop()
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "SUSPECTED")
        data["remediation_batches"].append(
            copy.deepcopy(data["remediation_batches"][0])
        )
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)

    def test_unfinished_recovery_resumes_and_cannot_be_claimed_complete(self):
        data = ledger()
        data["recovery_epochs"] = [
            {"family_id": "attempt-budget", "after_review_round": 2}
        ]
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "RECOVERY")
        data["recovery_epochs"][0]["status"] = "completed"
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)

    def test_existing_completion_fields_and_batch_labels_remain_readable(self):
        data = ledger()
        family = data["families"][0]
        data["recovery_epochs"] = [
            {
                **marker(
                    2,
                    family["root_cause_class"],
                    family["invariant"],
                    family["boundary"],
                ),
                "status": "completed",
                "replacement_head": "verified-head",
                "validation": ".git/review/full-validation.json",
            }
        ]
        data["remediation_batches"] = [
            {
                "id": "B1",
                "after_review_round": 2,
                "families": [{"family_id": "attempt-budget"}],
            }
        ]
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "NORMAL")

    def test_second_recovery_never_resets_the_budget(self):
        data = ledger()
        data["recovery_epochs"] = [
            {"family_id": "attempt-budget", "after_review_round": 2}
        ] * 2
        self.assertEqual(ANALYZER.analyze_ledger(data)["state"], "BLOCKED")

    def test_non_defects_do_not_make_contract_attention_or_recurrence(self):
        data = ledger()
        data["findings"][1]["disposition"] = "false_positive"
        result = ANALYZER.analyze_ledger(data)
        self.assertEqual(result["state"], "NORMAL")
        self.assertEqual(result["convergence_attention"], [])

    def test_regression_origin_needs_evidence(self):
        data = ledger()
        data["findings"][1]["origin"] = "remediation_regression"
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)
        data["findings"][1]["origin_evidence"] = (
            "Fails after batch b1; passes at its parent."
        )
        self.assertEqual(
            ANALYZER.analyze_ledger(data)["metrics"]["finding_origins"],
            {"unknown": 1, "remediation_regression": 1},
        )

    def test_costs_are_nonoverlapping_deltas_with_missing_fields_absent(self):
        data = ledger()
        data["cost_events"] = [
            {
                "id": "a1",
                "category": "audit",
                "duration_seconds": 3,
                "input_tokens": 100,
                "cached_input_tokens": 80,
            },
            {"id": "a2", "category": "audit", "duration_seconds": 5},
        ]
        result = ANALYZER.analyze_ledger(data)["costs_by_category"]["audit"]
        self.assertEqual(result["duration_seconds"], 8)
        self.assertNotIn("output_tokens", result)
        data["cost_events"].append(copy.deepcopy(data["cost_events"][0]))
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(data)

    def test_nonfinite_costs_and_invalid_cache_totals_fail(self):
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(value=value), self.assertRaises(ANALYZER.LedgerError):
                ANALYZER.analyze_ledger(
                    {"validation_runs": [{"scope": "full", "duration_seconds": value}]}
                )
        with self.assertRaises(ANALYZER.LedgerError):
            ANALYZER.analyze_ledger(
                {
                    "cost_events": [
                        {
                            "id": "x",
                            "category": "audit",
                            "input_tokens": 2,
                            "cached_input_tokens": 3,
                        }
                    ]
                }
            )


if __name__ == "__main__":
    unittest.main()
