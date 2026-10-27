"""Exercise evidence invalidation using disposable repositories and real files."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "prepare_remediation_audit.py"
)
SPEC = importlib.util.spec_from_file_location("audit_evidence", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        (self.repo / "code.py").write_text("print('example')\n")
        (self.repo / ".gitignore").write_text("private.cfg\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def commit(self):
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

    def snap(self, environment="python-fixture-v1", inputs=None):
        return AUDIT.snapshot(self.repo, self.base, environment, inputs or [])

    def test_identical_tree_reuses_evidence_across_commit(self):
        (self.repo / "code.py").write_text("print('updated')\n")
        before = self.snap()
        self.commit()
        after = self.snap()
        self.assertNotEqual(before["head"], after["head"])
        self.assertTrue(AUDIT.compare(before, after)["snapshot_matches"])

    def test_changed_content_mode_and_untracked_input_invalidate(self):
        before = self.snap()
        code = self.repo / "code.py"
        code.write_text("print('changed')\n")
        self.assertEqual(
            AUDIT.compare(before, self.snap())["changed_paths"], ["code.py"]
        )
        code.write_text("print('example')\n")
        code.chmod(0o755)
        self.assertFalse(AUDIT.compare(before, self.snap())["snapshot_matches"])
        code.chmod(0o644)
        (self.repo / "new.py").write_text("# consumer\n")
        self.assertEqual(
            AUDIT.compare(before, self.snap())["changed_paths"], ["new.py"]
        )

    def test_deletion_is_stable_across_commit(self):
        (self.repo / "code.py").unlink()
        before = self.snap()
        self.commit()
        self.assertTrue(AUDIT.compare(before, self.snap())["snapshot_matches"])

    def test_environment_and_ignored_dependencies_invalidate(self):
        private = self.repo / "private.cfg"
        private.write_text("example=1\n")
        before = self.snap(inputs=["private.cfg"])
        private.write_text("example=2\n")
        result = AUDIT.compare(before, self.snap(inputs=["private.cfg"]))
        self.assertIn("additional_inputs", result["changed_components"])
        self.assertIn(
            "environment",
            AUDIT.compare(before, self.snap("python-fixture-v2", ["private.cfg"]))[
                "changed_components"
            ],
        )
        self.assertNotIn("example=", json.dumps(before))

    def test_external_symlink_target_and_required_input_are_not_silently_ignored(self):
        target = self.root / "external.txt"
        target.write_text("first")
        (self.repo / "linked.txt").symlink_to(target)
        before = self.snap()
        target.write_text("second")
        self.assertFalse(AUDIT.compare(before, self.snap())["snapshot_matches"])
        with self.assertRaises(ValueError):
            self.snap(inputs=["missing.cfg"])

    def test_directory_links_fail_closed(self):
        (self.repo / "directory").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.snap()

    def test_absent_submodule_is_not_omitted_from_evidence(self):
        self.git(
            "update-index", "--add", "--cacheinfo", f"160000,{self.base},dependency"
        )
        self.assertFalse((self.repo / "dependency").exists())
        with self.assertRaises(ValueError):
            self.snap()

    def test_tampered_snapshot_fails_closed(self):
        before = self.snap()
        before["files"].clear()
        with self.assertRaises(ValueError):
            AUDIT.compare(before, self.snap())

    def test_metadata_only_change_does_not_invalidate_code_snapshot(self):
        before = self.snap()
        (self.repo / ".git/ledger.json").write_text('{"corrected_counts": true}')
        self.assertTrue(AUDIT.compare(before, self.snap())["snapshot_matches"])

    def test_bookkeeping_distinguishes_stale_validation_from_missing_metadata(self):
        current = self.snap()
        data = {
            "findings": [
                {
                    "id": "f1",
                    "remediation": "fixed consumer",
                    "regression": "entrypoint test",
                }
            ],
            "remediation_batches": [
                {
                    "id": "b1",
                    "finding_ids": ["f1"],
                    "validation_ids": ["v1"],
                    "required_commands": ["python3 tests.py"],
                }
            ],
            "validation_runs": [
                {
                    "id": "v1",
                    "command": "python3 tests.py",
                    "status": "passed",
                    "snapshot_digest": current["digest"],
                }
            ],
        }
        self.assertEqual(
            AUDIT.bookkeeping(data, "b1", current["digest"]),
            {"metadata_gaps": [], "validation_gaps": []},
        )
        data["findings"][0].pop("regression")
        result = AUDIT.bookkeeping(data, "b1", current["digest"])
        self.assertTrue(result["metadata_gaps"])
        self.assertFalse(result["validation_gaps"])
        data["validation_runs"][0]["snapshot_digest"] = "stale"
        self.assertTrue(
            AUDIT.bookkeeping(data, "b1", current["digest"])["validation_gaps"]
        )

    def test_cli_exit_codes_and_json(self):
        command = [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(self.repo),
            "--base",
            self.base,
            "--environment",
            "python-fixture-v1",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        previous = self.root / "snapshot.json"
        previous.write_text(completed.stdout)
        (self.repo / "code.py").write_text("print('changed')\n")
        completed = subprocess.run(
            command + ["--compare", str(previous)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertFalse(json.loads(completed.stdout)["snapshot_matches"])
        completed = subprocess.run(
            command + ["--input", "missing"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
