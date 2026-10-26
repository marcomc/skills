from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import os


REPOSITORY = Path(__file__).resolve().parents[3]
INIT_SCRIPT = REPOSITORY / "codex-workflow" / "init-agents-file" / "scripts" / "init_agents_file.py"
UPDATE_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_agents_templates.py"


class UpdateAgentsTemplatesInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "yaml.py").write_text(
            "import json\ndef safe_load(text):\n    return json.loads(text)\n",
            encoding="utf-8",
        )
        self.template_repo = self.root / "template-repo"
        (self.template_repo / "templates").mkdir(parents=True)
        (self.template_repo / "templates.yml").write_text(
            '{"project_types":[{"id":"python","path":"templates/python.md",'
            '"detect":{"file_globs":["*.py"],"content_markers":[]}}],'
            '"merge":{"always_include":[]},'
            '"scan_defaults":{"ignored_dirs":[".git",".work"],"max_depth":2}}',
            encoding="utf-8",
        )
        (self.template_repo / "templates" / "python.md").write_text(
            "# Python\n\nValidate changes.\n", encoding="utf-8"
        )
        self.scan_root = self.root / "projects"
        self.project = self.scan_root / "sample"
        self.project.mkdir(parents=True)
        (self.project / "app.py").write_text("print('ok')\n", encoding="utf-8")
        generated = subprocess.run(
            [sys.executable, str(INIT_SCRIPT), "--project", str(self.project),
             "--template-repo", str(self.template_repo), "--types", "python", "--apply"],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONPATH": str(self.root)},
        )
        if generated.returncode:
            self.fail(generated.stderr)

        self.skills = self.root / "codex-home" / "skills"
        self.update_skill = self.skills / "update-agents-file-templates"
        (self.update_skill / "scripts").mkdir(parents=True)
        shutil.copy2(UPDATE_SCRIPT, self.update_skill / "scripts" / UPDATE_SCRIPT.name)
        self.companion = self.skills / "init-agents-file"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_report(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.update_skill / "scripts" / UPDATE_SCRIPT.name),
             "--template-repo", str(self.template_repo), "--scan-root", str(self.scan_root),
             "--out-of-sync-report"],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONPATH": str(self.root)},
        )

    def test_isolated_update_skill_fails_actionably_before_report_write(self) -> None:
        result = self.run_report()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires the companion init-agents-file skill", result.stderr)
        self.assertIn("Install both skills", result.stderr)
        self.assertFalse((self.template_repo / ".work" / "out-of-sync").exists())

    def test_installed_sibling_pair_generates_report(self) -> None:
        helper_dir = self.companion / "scripts"
        helper_dir.mkdir(parents=True)
        shutil.copy2(INIT_SCRIPT, helper_dir / INIT_SCRIPT.name)

        result = self.run_report()

        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.template_repo / ".work" / "out-of-sync" / "projects.json"
        self.assertTrue(report.is_file())
        self.assertIn(str(self.project / "AGENTS.md"), report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
