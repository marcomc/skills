"""Exercise run reconciliation against real Git snapshots and evidence files."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import evaluate_review as REVIEW
import prepare_remediation_audit as AUDIT


class ReviewEvaluationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "example.py").write_text("print('ok')\n")
        (self.repo / "README.md").write_text("# Fixture\n")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Example",
            "-c",
            "user.email=user@example.com",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "fixture",
        )
        self.base = self.git("rev-parse", "HEAD").strip()
        (self.root / "policy.md").write_text("Fixture review policy\n")
        observed = subprocess.run(
            [sys.executable, str(self.repo / "src/example.py")],
            check=True,
            capture_output=True,
            text=True,
        )
        (self.root / "test.log").write_text(observed.stdout)
        (self.root / "review.log").write_text("Fixture independent review record\n")
        current = self.snap()
        self.save_snapshot("previous.json", current)
        policy = REVIEW.policy_fingerprint(["policy.md"], self.root)
        self.data = {
            "review_run": {
                "id": "fixture",
                "depth": "bounded",
                "risk_reason": "one CLI contract",
                "policy_files": ["policy.md"],
                "policy_digest": policy,
                "coverage_reviewed": True,
                "requirements": [
                    {
                        "id": "review",
                        "kind": "review",
                        "required": True,
                        "coverage": "CLI behavior and consumers",
                        "feedback_revision": 0,
                        "independent": True,
                        "inputs": ["src/"],
                        "dependency_evidence": "Fixture has no other imports or runtime inputs",
                    },
                    {
                        "id": "test",
                        "kind": "validation",
                        "required": True,
                        "coverage": "CLI executable output",
                        "feedback_revision": 0,
                        "command": f"{sys.executable} src/example.py",
                        "inputs": ["src/"],
                        "dependency_evidence": "Standalone standard-library-free fixture",
                    },
                ],
            },
            "findings": [],
            "review_evidence": [],
        }
        for requirement in self.data["review_run"]["requirements"]:
            self.data["review_evidence"].append(
                {
                    "id": requirement["id"] + "-1",
                    "requirement_id": requirement["id"],
                    "requirement_digest": AUDIT.digest(requirement),
                    "policy_digest": policy,
                    "status": "passed",
                    "source": requirement["id"] + ".log",
                    "snapshot": "previous.json",
                    "reviewer": "fixture-independent",
                    "independent": True,
                }
            )

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def snap(self, environment="fixture-python-v1", inputs=None):
        return AUDIT.snapshot(self.repo, self.base, environment, inputs or [])

    def save_snapshot(self, name, value):
        (self.root / name).write_text(json.dumps({"snapshot": value}))

    def evaluate(self, data=None, current=None):
        return REVIEW.evaluate(
            self.data if data is None else data,
            self.snap() if current is None else current,
            self.root,
        )

    def test_current_evidence_reused_without_claiming_semantic_approval(self):
        result = self.evaluate()
        self.assertEqual(result["mechanical_status"], "READY")
        self.assertEqual(result["reused_check_ids"], ["review", "test"])
        self.assertFalse(result["semantic_approval"])

    def test_unrelated_doc_change_keeps_bounded_evidence(self):
        (self.repo / "README.md").write_text("# Updated fixture\n")
        self.assertEqual(self.evaluate()["reused_check_ids"], ["review", "test"])

    def test_full_scope_evidence_invalidated_by_unrelated_doc_change(self):
        for requirement, evidence in zip(
            self.data["review_run"]["requirements"],
            self.data["review_evidence"],
            strict=True,
        ):
            requirement.pop("inputs")
            evidence["requirement_digest"] = AUDIT.digest(requirement)
        (self.repo / "README.md").write_text("# Updated fixture\n")
        self.assertEqual(self.evaluate()["pending_check_ids"], ["review", "test"])

    def test_new_consumer_and_deleted_producer_invalidate(self):
        consumer = self.repo / "src/consumer.py"
        consumer.write_text("import example\n")
        self.assertEqual(self.evaluate()["pending_check_ids"], ["review", "test"])
        consumer.unlink()
        (self.repo / "src/example.py").unlink()
        self.assertEqual(self.evaluate()["pending_check_ids"], ["review", "test"])

    def test_environment_and_external_inputs_are_global(self):
        self.assertEqual(
            self.evaluate(current=self.snap("fixture-python-v2"))["reused_check_ids"],
            [],
        )
        extra = self.root / "external.cfg"
        extra.write_text("fixture=true\n")
        self.assertEqual(
            self.evaluate(current=self.snap(inputs=[str(extra)]))["reused_check_ids"],
            [],
        )

    def test_policy_drift_blocks_even_when_product_unchanged(self):
        (self.root / "policy.md").write_text("Changed policy\n")
        result = self.evaluate()
        self.assertEqual(result["mechanical_status"], "BLOCKED")
        self.assertEqual(result["reused_check_ids"], [])

    def test_new_feedback_invalidates_only_affected_review(self):
        self.data["review_run"]["requirements"][0]["feedback_revision"] = 1
        result = self.evaluate()
        self.assertEqual(result["pending_check_ids"], ["review"])
        self.assertEqual(result["reused_check_ids"], ["test"])

    def test_command_or_coverage_change_invalidates(self):
        self.data["review_run"]["requirements"][1]["command"] += " --validate"
        self.assertIn("test", self.evaluate()["pending_check_ids"])

    def test_later_failed_or_unknown_record_supersedes_pass(self):
        later = copy.deepcopy(self.data["review_evidence"][1])
        later.update(id="test-2", status="failed")
        self.data["review_evidence"].append(later)
        self.assertEqual(self.evaluate()["pending_check_ids"], ["test"])
        later["status"] = "unknown"
        self.assertEqual(self.evaluate()["pending_check_ids"], ["test"])

    def test_missing_empty_or_nonindependent_evidence_not_reused(self):
        (self.root / "test.log").unlink()
        (self.root / "review.log").write_text("")
        self.assertEqual(self.evaluate()["pending_check_ids"], ["review", "test"])
        (self.root / "review.log").write_text("Review result\n")
        self.data["review_evidence"][0]["independent"] = False
        self.assertIn("review", self.evaluate()["pending_check_ids"])

    def test_unreviewed_coverage_cannot_be_ready(self):
        self.data["review_run"]["coverage_reviewed"] = False
        self.assertEqual(self.evaluate()["mechanical_status"], "NEEDS_WORK")

    def test_unknown_required_check_and_optional_suggestion(self):
        requirement = {
            "id": "extra",
            "kind": "review",
            "required": True,
            "coverage": "packaging",
            "feedback_revision": 0,
        }
        self.data["review_run"]["requirements"].append(requirement)
        self.assertEqual(self.evaluate()["mechanical_status"], "NEEDS_WORK")
        requirement.update(
            required=False, optional_reason="Unchanged unrelated packaging"
        )
        result = self.evaluate()
        self.assertEqual(result["mechanical_status"], "READY")
        self.assertEqual(result["optional_pending_check_ids"], ["extra"])

    def test_missing_baseline_or_ambiguous_requirement_rejected(self):
        self.data["review_run"]["requirements"].pop()
        self.data["review_evidence"].pop()
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_invalid_or_undeclared_narrow_input_rejected(self):
        for selection in [
            [],
            ["../src"],
            ["/src"],
            ["src/*.py"],
            ["./src/"],
            ["src//"],
        ]:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.data["review_run"]["requirements"][0]["inputs"] = selection
                self.evaluate()
        self.data["review_run"]["requirements"][0]["inputs"] = ["src/"]
        self.data["review_run"]["requirements"][0].pop("dependency_evidence")
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_snapshot_tampering_rejected(self):
        snapshot = self.snap()
        snapshot["files"]["src/example.py"]["sha256"] = "fake"
        self.save_snapshot("previous.json", snapshot)
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_metadata_changes_do_not_invalidate_product_proofs(self):
        (self.repo / ".git/bookkeeping.json").write_text('{"batch": "b1"}')
        self.assertEqual(self.evaluate()["mechanical_status"], "READY")

    def test_open_defect_and_unsubstantiated_false_positive_cannot_be_ready(self):
        finding = {
            "id": "f1",
            "root_cause_class": "wrong output",
            "invariant": "prints ok",
            "review_round": 1,
        }
        self.data["findings"].append(finding)
        self.assertEqual(self.evaluate()["open_finding_ids"], ["f1"])
        finding.update(status="resolved", resolution_evidence="test.log")
        self.assertEqual(self.evaluate()["mechanical_status"], "READY")
        finding["disposition"] = "false_positive"
        self.assertEqual(self.evaluate()["open_finding_ids"], ["f1"])
        finding["disposition_evidence"] = "review.log"
        self.assertEqual(self.evaluate()["mechanical_status"], "READY")

    def test_recurrence_gate_remains_authoritative_for_resolved_records(self):
        self.data["findings"] = [
            {
                "id": f"f{round_}",
                "review_round": round_,
                "root_cause_class": "wrong output",
                "invariant": "prints ok",
                "status": "resolved",
                "resolution_evidence": "test.log",
            }
            for round_ in [1, 2]
        ]
        result = self.evaluate()
        self.assertEqual(result["health_state"], "SUSPECTED")
        self.assertEqual(result["mechanical_status"], "NEEDS_WORK")

    def test_unknown_and_duplicate_record_ids_rejected(self):
        self.data["review_evidence"][0]["requirement_id"] = "missing"
        with self.assertRaises(ValueError):
            self.evaluate()
        self.data["review_evidence"][0]["requirement_id"] = "review"
        self.data["review_evidence"].append(
            copy.deepcopy(self.data["review_evidence"][0])
        )
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_cli_exit_codes_for_ready_missing_proof_and_invalid_input(self):
        ledger = self.root / "ledger.json"
        current = self.root / "current.json"
        self.save_snapshot("current.json", self.snap())
        command = [
            sys.executable,
            str(SCRIPTS / "evaluate_review.py"),
            str(ledger),
            "--snapshot",
            str(current),
        ]
        for data, expected in [
            (self.data, 0),
            ({**self.data, "review_evidence": []}, 1),
            ({}, 2),
        ]:
            ledger.write_text(json.dumps(data))
            result = subprocess.run(
                command, check=False, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
