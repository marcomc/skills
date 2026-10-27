"""Exercise configuration and recovery against isolated TOML files."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/configure_codex_desktop.py"


class JevConfigTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = self.root / "config.toml"

    def run_helper(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            env={**os.environ, "CODEX_HOME": str(self.root)},
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_provider_before_table_preserves_newline_comment_and_settings(self):
        for spacing in ("", "\n"):
            with self.subTest(spacing=spacing):
                self.config.write_text(
                    'model = "fixture-model"\n'
                    'model_provider = "openai" # preserve this comment\n'
                    + spacing
                    + '[projects."/fixture"]\ntrust_level = "trusted"\n'
                )
                result = self.run_helper("--apply")
                self.assertEqual(result.returncode, 0, result.stderr)
                parsed = tomllib.loads(self.config.read_text())
                self.assertEqual(parsed["model"], "fixture-model")
                self.assertEqual(parsed["model_provider"], "jev-gateway")
                self.assertEqual(parsed["projects"]["/fixture"]["trust_level"], "trusted")
                self.assertIn("# preserve this comment\n", self.config.read_text())

    def test_provider_last_root_key_without_comment_stays_valid(self):
        self.config.write_text(
            'model_provider = "openai"\n[features]\nfixture = true\n'
        )
        result = self.run_helper("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(tomllib.loads(self.config.read_text())["features"]["fixture"])

    def test_apply_is_idempotent_and_rollback_restores_exact_bytes(self):
        original = b'model = "fixture-model"\n[features]\nfixture = true\n'
        self.config.write_bytes(original)
        self.config.chmod(0o600)
        result = self.run_helper("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list(self.root.glob("config.toml.pre-jev-*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        updated = self.config.read_bytes()
        result = self.run_helper("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config.read_bytes(), updated)
        self.assertEqual(len(list(self.root.glob("config.toml.pre-jev-*.bak"))), 1)
        result = self.run_helper("--rollback", str(backups[0]))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config.read_bytes(), original)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)

    def test_unrelated_provider_and_symlink_are_preserved(self):
        original = b'model_provider = "custom-fixture"\n'
        self.config.write_bytes(original)
        result = self.run_helper("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config.read_bytes(), original)
        target = self.root / "canonical.toml"
        target.write_bytes(original)
        self.config.unlink()
        self.config.symlink_to(target)
        result = self.run_helper("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.config.is_symlink())
        self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
