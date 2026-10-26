from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import os


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "init_agents_file.py"


class InitAgentsFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.root / "yaml.py").write_text(
            "import json\ndef safe_load(text):\n    return json.loads(text)\n",
            encoding="utf-8",
        )
        self.template_repo = self.root / "templates-repo"
        (self.template_repo / "templates").mkdir(parents=True)
        (self.template_repo / "templates.yml").write_text(
            '{"project_types":[{"id":"python","path":"templates/python.md",'
            '"detect":{"file_globs":["*.py"],"content_markers":[]}}],'
            '"merge":{"always_include":[]}}',
            encoding="utf-8",
        )
        (self.template_repo / "templates" / "python.md").write_text(
            "# Python\n\nUse ${PROJECT_DESCRIPTION}.\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_helper(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(self.root)
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project", str(self.project),
             "--template-repo", str(self.template_repo), *arguments],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    def test_valid_apply_creates_instruction_file(self) -> None:
        result = self.run_helper("--types", "python", "--apply")

        self.assertEqual(result.returncode, 0, result.stderr)
        content = (self.project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("generated-by: agents-file-templates-and-skills/init-agents-file", content)
        self.assertIn("## Project Local Rules", content)

    def test_apply_refuses_unmarked_existing_file_without_changing_bytes(self) -> None:
        output = self.project / "AGENTS.md"
        original = b"# Human-authored rules\r\nKeep this file intact.\r\n"
        output.write_bytes(original)

        result = self.run_helper("--types", "python", "--apply")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite existing unmarked instruction file", result.stderr)
        self.assertEqual(output.read_bytes(), original)

    def test_dry_run_still_renders_for_unmarked_existing_file(self) -> None:
        output = self.project / "AGENTS.md"
        output.write_text("# Human-authored rules\n", encoding="utf-8")

        result = self.run_helper("--types", "python")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("generated-by: agents-file-templates-and-skills/init-agents-file", result.stdout)
        self.assertEqual(output.read_text(encoding="utf-8"), "# Human-authored rules\n")

    def test_managed_refresh_preserves_local_rules_and_recovered_placeholder(self) -> None:
        result = self.run_helper(
            "--types", "python", "--set", "PROJECT_DESCRIPTION=My custom project", "--apply"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.project / "AGENTS.md"
        content = output.read_text(encoding="utf-8")
        content = content.replace(
            "<!-- BEGIN PROJECT LOCAL -->\n\n<!-- END PROJECT LOCAL -->",
            "<!-- BEGIN PROJECT LOCAL -->\nKeep my local rule.\n<!-- END PROJECT LOCAL -->",
        )
        output.write_text(content, encoding="utf-8")

        refreshed = self.run_helper("--apply")

        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        after = output.read_text(encoding="utf-8")
        self.assertIn("- Description: My custom project", after)
        self.assertIn("Use My custom project.", after)
        self.assertIn("Keep my local rule.", after)

    def test_specific_output_variant_refuses_unmarked_existing_file(self) -> None:
        output = self.project / "CLAUDE.md"
        original = b"User-authored Claude rules\n"
        output.write_bytes(original)

        result = self.run_helper("--agent", "claude", "--output-mode", "specific", "--apply")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
