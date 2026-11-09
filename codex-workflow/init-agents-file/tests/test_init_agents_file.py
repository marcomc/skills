from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import os


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "init_agents_file.py"


class InitAgentsFileTests(unittest.TestCase):
    def test_custom_project_name_stays_current_and_learned_headings_are_scoped(self) -> None:
        template = self.template_repo / "templates" / "python.md"
        template.write_text("# Python\n\n## Learned Rules\n\n- Preserve evidence.\n", encoding="utf-8")
        result = self.run_helper("--types", "python", "--set", "PROJECT_NAME=Stable project name", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.project / "AGENTS.md").read_text()
        self.assertIn("## Python Learned Rules", text)
        result = self.run_helper("--check", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"status": "current"', result.stdout)

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

    def test_template_drift_blocks_apply_when_custom_values_cannot_be_recovered(self) -> None:
        template = self.template_repo / "templates" / "python.md"
        template.write_text(
            "# Python\n\nRun tests with `${TEST_COMMAND}` for ${PROJECT_DESCRIPTION}. "
            "Lint config: ${MARKDOWNLINT_CONFIG}.\n",
            encoding="utf-8",
        )
        initial = self.run_helper(
            "--types", "python", "--set", "PROJECT_DESCRIPTION=Custom project",
            "--set", "PROJECT_NAME=Custom Python Project",
            "--set", "GLOBAL_AGENTS_PATH=../policy/AGENTS.md",
            "--set", "TEST_COMMAND=make test-custom",
            "--set", "MARKDOWNLINT_CONFIG=custom-markdownlint.json", "--apply",
        )
        self.assertEqual(initial.returncode, 0, initial.stderr)
        output = self.project / "AGENTS.md"
        original = output.read_bytes()
        self.assertIn(b"make test-custom", original)

        template.write_text(
            "# Python\n\nRun the complete suite with `${TEST_COMMAND}` for ${PROJECT_DESCRIPTION}. "
            "Lint config: ${MARKDOWNLINT_CONFIG}.\n",
            encoding="utf-8",
        )
        refused = self.run_helper("--apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("placeholders MARKDOWNLINT_CONFIG, TEST_COMMAND are missing", refused.stderr)
        self.assertIn("No file was changed", refused.stderr)
        self.assertEqual(output.read_bytes(), original)

        explicit = self.run_helper(
            "--set", "TEST_COMMAND=make test-custom",
            "--set", "MARKDOWNLINT_CONFIG=custom-markdownlint.json", "--apply",
        )
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        refreshed = output.read_text(encoding="utf-8")
        self.assertIn("Run the complete suite with `make test-custom`", refreshed)
        self.assertIn("- Description: Custom project", refreshed)
        self.assertIn("- Project: `Custom Python Project`", refreshed)
        self.assertIn("Follow `../policy/AGENTS.md`", refreshed)

    def test_template_drift_with_recoverable_root_overrides_can_refresh(self) -> None:
        template = self.template_repo / "templates" / "python.md"
        template.write_text("# Python\n\nUse ${PROJECT_DESCRIPTION}.\n", encoding="utf-8")
        initial = self.run_helper(
            "--types", "python", "--set", "PROJECT_DESCRIPTION=Custom project",
            "--set", "PROJECT_NAME=Named Project", "--apply"
        )
        self.assertEqual(initial.returncode, 0, initial.stderr)
        template.write_text(
            "# Python\n\nUse the project description: ${PROJECT_DESCRIPTION}.\n",
            encoding="utf-8",
        )
        refreshed = self.run_helper("--apply")
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        self.assertIn(
            "Use the project description: Custom project.",
            (self.project / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "- Project: `Named Project`",
            (self.project / "AGENTS.md").read_text(encoding="utf-8"),
        )

    def test_template_drift_preserves_multiline_description(self) -> None:
        description = "first line\nsecond line"
        initial = self.run_helper(
            "--types", "python", "--set", f"PROJECT_DESCRIPTION={description}", "--apply"
        )
        self.assertEqual(initial.returncode, 0, initial.stderr)
        template = self.template_repo / "templates" / "python.md"
        template.write_text("# Python\n\nUpdated guidance for ${PROJECT_DESCRIPTION}.\n")
        refreshed = self.run_helper("--apply")
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        result = (self.project / "AGENTS.md").read_text()
        self.assertIn(f"- Description: {description}\n\n## Project-Type Overlays", result)
        self.assertIn(f"Updated guidance for {description}.", result)

    def test_ambiguous_description_boundary_refuses_refresh_without_mutation(self) -> None:
        description = "first line\n\n## Project-Type Overlays\nsecond line"
        initial = self.run_helper(
            "--types", "python", "--set", f"PROJECT_DESCRIPTION={description}", "--apply"
        )
        self.assertEqual(initial.returncode, 0, initial.stderr)
        output = self.project / "AGENTS.md"
        before = output.read_bytes()
        template = self.template_repo / "templates" / "python.md"
        template.write_text("# Python\n\nUpdated guidance for ${PROJECT_DESCRIPTION}.\n")
        refused = self.run_helper("--apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("PROJECT_DESCRIPTION", refused.stderr)
        self.assertEqual(output.read_bytes(), before)
        explicit = self.run_helper("--set", f"PROJECT_DESCRIPTION={description}", "--apply")
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        self.assertIn(f"Updated guidance for {description}.", output.read_text())

    def test_drift_refresh_preserves_default_and_empty_descriptions(self) -> None:
        template = self.template_repo / "templates" / "python.md"
        for description in [None, ""]:
            with self.subTest(description=description):
                output = self.project / "AGENTS.md"
                output.unlink(missing_ok=True)
                template.write_text("# Python\n\nOriginal guidance.\n")
                arguments = [] if description is None else ["--set", "PROJECT_DESCRIPTION="]
                initial = self.run_helper("--types", "python", *arguments, "--apply")
                self.assertEqual(initial.returncode, 0, initial.stderr)
                template.write_text("# Python\n\nUpdated guidance.\n")
                refreshed = self.run_helper("--apply")
                self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
                expected = "${PROJECT_DESCRIPTION}" if description is None else ""
                self.assertIn(f"- Description: {expected}\n", output.read_text())
                self.assertIn('"status": "current"', self.run_helper("--check", "--json").stdout)

    def test_renamed_project_refresh_distinguishes_derived_and_explicit_names(self) -> None:
        for explicit in [False, True]:
            with self.subTest(explicit=explicit):
                self.project = self.root / f"old-{explicit}"
                self.project.mkdir()
                arguments = ["--set", "PROJECT_NAME=Stable name"] if explicit else []
                initial = self.run_helper("--types", "python", *arguments, "--apply")
                self.assertEqual(initial.returncode, 0, initial.stderr)
                renamed = self.root / f"new-{explicit}"
                self.project.rename(renamed)
                self.project = renamed
                refreshed = self.run_helper("--apply")
                self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
                text = (renamed / "AGENTS.md").read_text()
                expected = "Stable name" if explicit else renamed.name
                self.assertIn(f"- Project: `{expected}`", text)
                self.assertEqual("<!-- project-name-override -->" in text, explicit)
                self.assertIn('"status": "current"', self.run_helper("--check", "--json").stdout)

    def test_legacy_project_names_are_preserved_during_refresh_and_rename(self) -> None:
        for saved_name in ["Legacy custom name", None]:
            for rename in [False, True]:
                with self.subTest(name=saved_name, rename=rename):
                    self.project = self.root / f"legacy-{saved_name}-{rename}"
                    self.project.mkdir()
                    name = saved_name or self.project.name
                    arguments = ["--set", f"PROJECT_NAME={saved_name}"] if saved_name else []
                    initial = self.run_helper("--types", "python", *arguments, "--apply")
                    self.assertEqual(initial.returncode, 0, initial.stderr)
                    output = self.project / "AGENTS.md"
                    output.write_text(output.read_text().replace("<!-- project-name-override -->\n", "")
                                      .replace("<!-- project-name-derived -->\n", ""))
                    if rename:
                        target = self.project.with_name(self.project.name + "-renamed")
                        self.project.rename(target)
                        self.project = target
                    template = self.template_repo / "templates" / "python.md"
                    template.write_text("# Python\n\nUpdated legacy guidance.\n")
                    refreshed = self.run_helper("--apply")
                    self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
                    text = (self.project / "AGENTS.md").read_text()
                    self.assertIn(f"- Project: `{name}`", text)
                    self.assertIn("<!-- project-name-override -->", text)
                    self.assertIn('"status": "current"', self.run_helper("--check", "--json").stdout)

    def test_explicit_name_equal_to_directory_remains_an_override_after_rename(self) -> None:
        name = self.project.name
        initial = self.run_helper("--types", "python", "--set", f"PROJECT_NAME={name}", "--apply")
        self.assertEqual(initial.returncode, 0, initial.stderr)
        renamed = self.project.with_name("renamed-project")
        self.project.rename(renamed)
        self.project = renamed
        refreshed = self.run_helper("--apply")
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        text = (renamed / "AGENTS.md").read_text()
        self.assertIn(f"- Project: `{name}`", text)
        self.assertIn("<!-- project-name-override -->", text)
        self.assertIn('"status": "current"', self.run_helper("--check", "--json").stdout)

    def test_recorded_and_explicit_values_take_precedence_over_section_inference(self) -> None:
        template = self.template_repo / "templates" / "python.md"
        template.write_text("# Python\n\nUse production.\n")
        initial = self.run_helper("--types", "python", "--set", "PROJECT_DESCRIPTION=Custom project", "--apply")
        self.assertEqual(initial.returncode, 0, initial.stderr)
        template.write_text("# Python\n\nUse ${PROJECT_DESCRIPTION}.\n")
        for arguments, expected in [([], "Custom project"),
                                    (["--set", "PROJECT_DESCRIPTION=Reviewed replacement"], "Reviewed replacement")]:
            with self.subTest(arguments=arguments):
                refreshed = self.run_helper(*arguments, "--apply")
                self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
                text = (self.project / "AGENTS.md").read_text()
                self.assertIn(f"- Description: {expected}", text)
                self.assertIn(f"Use {expected}.", text)
                self.assertEqual(self.run_helper("--check", "--json").returncode, 0)

    def test_explicit_values_resolve_conflicting_section_inference_without_losing_other_values(self) -> None:
        (self.template_repo / "templates.yml").write_text(
            '{"project_types":[{"id":"python","path":"templates/python.md"},'
            '{"id":"generic","path":"templates/generic.md"}],"merge":{"always_include":[]}}'
        )
        python = self.template_repo / "templates" / "python.md"
        generic = self.template_repo / "templates" / "generic.md"
        python.write_text("# Python\n\nUse production; lint alpha.\n")
        generic.write_text("# Generic\n\nUse staging; lint beta.\n")
        initial = self.run_helper("--types", "python,generic", "--set", "PROJECT_DESCRIPTION=Keep description", "--apply")
        self.assertEqual(initial.returncode, 0, initial.stderr)
        output = self.project / "AGENTS.md"
        original = output.read_bytes()
        python.write_text("# Python\n\nUse ${TEST_COMMAND}; lint ${LINT_COMMAND}.\n")
        generic.write_text("# Generic\n\nUse ${TEST_COMMAND}; lint ${LINT_COMMAND}.\n")
        refused = self.run_helper("--apply")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("Conflicting recovered placeholder TEST_COMMAND", refused.stderr)
        self.assertEqual(output.read_bytes(), original)
        partial = self.run_helper("--set", "TEST_COMMAND=make checked", "--apply")
        self.assertNotEqual(partial.returncode, 0)
        self.assertIn("Conflicting recovered placeholder LINT_COMMAND", partial.stderr)
        self.assertEqual(output.read_bytes(), original)
        arguments = ["--set", "TEST_COMMAND=make checked", "--set", "LINT_COMMAND=make lint"]
        preview = self.run_helper(*arguments)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(preview.stdout.count("Use make checked; lint make lint."), 2)
        refreshed = self.run_helper(*arguments, "--apply")
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        text = output.read_text()
        self.assertEqual(text.count("Use make checked; lint make lint."), 2)
        self.assertIn("- Description: Keep description", text)
        self.assertEqual(self.run_helper("--check", "--json").returncode, 0)

    def test_specific_output_variant_refuses_unmarked_existing_file(self) -> None:
        output = self.project / "CLAUDE.md"
        original = b"User-authored Claude rules\n"
        output.write_bytes(original)

        result = self.run_helper("--agent", "claude", "--output-mode", "specific", "--apply")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
