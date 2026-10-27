"""Behavioral checks with real local Git remotes and isolated GitHub reads."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_plan.py"
SPEC = importlib.util.spec_from_file_location("release_plan", SCRIPT)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- Add filtered exports.
- Independent preview improvements.

## [1.0.0] - 2026-01-01 - First stable release

### Added

- Original feature.
"""
TODO = """# TODO

- [ ] SRC-42 Add filtered exports.
- [ ] SRC-43 Retry failed uploads.
- [ ] SRC-99 Independent preview improvements.
"""


def published(version="1.0.0", identity=1, draft=False, prerelease=False):
    return {"id": identity, "tag_name": "v" + version, "draft": draft,
            "prerelease": prerelease, "published_at": None if draft else "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"}


def scope(chat="unavailable", kind="feature"):
    return {"chat": {"status": chat, "coverage": "Relevant fixture context only"}, "items": [
        {"id": "SRC-42", "completed": True, "kind": kind,
         "summary": "Add filtered exports.", "evidence": ["Implementation and export checks"],
         "issues": ["https://github.com/example/project/issues/42"],
         "todo": {"path": "TODO.md", "entry": "- [ ] SRC-42 Add filtered exports.\n"},
         "unreleased": "- Add filtered exports.\n"},
        {"id": "SRC-43", "completed": False, "kind": "fix",
         "summary": "Retry failed uploads.", "evidence": [], "issues": [],
         "todo": {"path": "TODO.md", "entry": "- [ ] SRC-43 Retry failed uploads.\n"}},
    ]}


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="update-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bare = self.base / "remote.git"
        self.root = self.base / "work"
        self.git(self.base, "init", "--bare", str(self.bare))
        self.git(self.base, "init", "-b", "main", str(self.root))
        self.git(self.root, "config", "user.name", "Fixture")
        self.git(self.root, "config", "user.email", "fixture@example.com")
        (self.root / "CHANGELOG.md").write_text(CHANGELOG)
        (self.root / "TODO.md").write_text(TODO)
        (self.root / "package.json").write_text('{"name":"fixture","version":"1.0.0"}\n')
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Fixture baseline")
        self.git(self.root, "remote", "add", "origin", str(self.bare))
        self.git(self.root, "push", "-u", "origin", "main")
        self.git(self.root, "tag", "-a", "v1.0.0", "-m", "Fixture stable")
        self.git(self.root, "push", "origin", "refs/tags/v1.0.0")
        self.config = {"remote": "origin", "target": "main", "version_sources": [
            {"path": "package.json", "pattern": r'"version":"(?P<version>[0-9]+\.[0-9]+\.[0-9]+)"'}
        ]}
        self.github = {"status": "available", "draft_visibility": True, "releases": [published()]}
        # The server side is a real local bare repository. Only GitHub reads
        # are substituted; no network or publication is permitted by tests.
        self.reader = patch.object(release, "github_state", side_effect=lambda *_: copy.deepcopy(self.github))
        self.reader.start()
        self.addCleanup(self.reader.stop)

    def git(self, root, *args):
        environment = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                       "GIT_TERMINAL_PROMPT": "0"}
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                                env=environment, check=True)
        return result.stdout.strip()

    def plan(self, root=None, **kwargs):
        return release.make_plan(root or self.root, self.config, kwargs.pop("scope", scope()),
                                 "2026-10-27", **kwargs)

    def apply(self, plan, root=None):
        for edit in plan["edits"]:
            (root or self.root).joinpath(edit["path"]).write_bytes(edit["after"].encode())

    def integrate(self, plan):
        self.apply(plan)
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Prepare fixture release")
        self.git(self.root, "push", "origin", "HEAD:refs/heads/main")

    def test_scoped_notes_todo_ids_links_and_history(self):
        plan = self.plan()
        self.assertEqual(plan["candidate"], "1.1.0")
        self.assertIn("SRC-42: Add filtered exports.", plan["reason"])
        self.apply(plan)
        changelog = (self.root / "CHANGELOG.md").read_text()
        pending, concrete = changelog.split("## [1.1.0]", 1)
        self.assertIn("Independent preview improvements.", pending)
        self.assertNotIn("Add filtered exports.", pending)
        self.assertIn("SRC-42", concrete)
        self.assertIn("https://github.com/example/project/issues/42", concrete)
        self.assertIn("## [1.0.0] - 2026-01-01 - First stable release", concrete)
        active = (self.root / "TODO.md").read_text()
        self.assertNotIn("SRC-42", active)
        self.assertIn("SRC-43", active)
        self.assertIn("SRC-99", active)
        self.assertEqual(release.check_plan(self.root, plan, "commit")["status"], "checked")

    def test_default_minor_major_patch_and_explicit_policy(self):
        for kind, version in (("other", "1.1.0"), ("fix", "1.0.1"), ("breaking", "2.0.0")):
            with self.subTest(kind=kind):
                self.assertEqual(self.plan(scope=scope(kind=kind))["candidate"], version)
        self.assertEqual(self.plan(explicit="3.2.1")["candidate"], "3.2.1")
        self.assertEqual(self.plan(bump="patch", policy_reason="Project policy section 2")["candidate"], "1.0.1")
        with self.assertRaises(release.PlanError):
            self.plan(bump="patch")
        with self.assertRaises(release.PlanError):
            self.plan(explicit="1.0.0")

    def test_chat_optional_available_partial_unavailable(self):
        for status in ("available", "partial", "unavailable"):
            with self.subTest(status=status):
                plan = self.plan(scope=scope(chat=status))
                self.assertEqual(plan["scope"]["chat"]["status"], status)
                self.assertEqual(plan["candidate"], "1.1.0")
        missing = scope()
        del missing["chat"]
        self.assertEqual(self.plan(scope=missing)["scope"]["chat"]["status"], "unavailable")

    def test_completion_evidence_required_and_incomplete_todo_preserved(self):
        missing = scope()
        missing["items"][0]["evidence"] = []
        with self.assertRaisesRegex(release.PlanError, "evidence"):
            self.plan(scope=missing)
        (self.root / "TODO.md").write_text(TODO.replace("- [ ] SRC-43 Retry failed uploads.\n", ""))
        with self.assertRaisesRegex(release.PlanError, "Incomplete TODO"):
            self.plan()

    def test_two_worktrees_same_baseline_stale_after_first_integrates(self):
        second = self.base / "second"
        self.git(self.root, "worktree", "add", "-b", "feat/second", str(second), "HEAD")
        first_plan, second_plan = self.plan(), self.plan(root=second)
        self.assertEqual(first_plan["candidate"], second_plan["candidate"])
        self.apply(second_plan, root=second)
        self.integrate(first_plan)
        with self.assertRaisesRegex(release.PlanError, "Stale version plan"):
            release.check_plan(second, second_plan, "commit")
        bound = release.bind_plan(self.root, first_plan)
        self.assertEqual(release.check_plan(self.root, bound, "publish")["candidate"], "1.1.0")

    def test_release_changes_during_preparation_rejected_and_refresh_recomputes(self):
        plan = self.plan()
        self.apply(plan)
        self.github["releases"].append(published("1.1.0", identity=2))
        with self.assertRaisesRegex(release.PlanError, "Stale"):
            release.check_plan(self.root, plan, "commit")
        # Reconcile this plan's own metadata edits before starting a fresh plan.
        for edit in plan["edits"]:
            (self.root / edit["path"]).write_text(edit["before"])
        fresh = self.plan()
        self.assertEqual(fresh["candidate"], "1.2.0")
        with self.assertRaises(release.PlanError):
            self.plan(explicit="1.1.0")

    def test_mainline_metadata_ahead_of_latest_published(self):
        changelog = CHANGELOG.replace("## [1.0.0]", "## [1.1.0] - 2026-02-01\n\n- Integrated release.\n\n## [1.0.0]", 1)
        (self.root / "CHANGELOG.md").write_text(changelog)
        package = self.root / "package.json"
        package.write_text(package.read_text().replace("1.0.0", "1.1.0"))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Release metadata ahead of public release")
        self.git(self.root, "push", "origin", "main")
        plan = self.plan()
        self.assertEqual(plan["baseline_summary"]["latest_stable"]["tag_name"], "v1.0.0")
        self.assertEqual(plan["baseline_summary"]["version"], "1.1.0")
        self.assertEqual(plan["candidate"], "1.2.0")
        self.integrate(plan)
        bound = release.bind_plan(self.root, plan)
        with self.assertRaisesRegex(release.PlanError, "intermediate.*1.1.0"):
            release.check_plan(self.root, bound, "publish")
        self.github["releases"].append(published("1.1.0", identity=2))
        with self.assertRaisesRegex(release.PlanError, "Stale"):
            release.check_plan(self.root, bound, "publish")
        rebound = release.bind_plan(self.root, plan)
        self.assertEqual(rebound["candidate"], "1.2.0")
        self.assertEqual(rebound["binding_selection_baseline"]["version"], "1.1.0")
        self.assertEqual(release.check_plan(self.root, rebound, "publish")["status"], "checked")

    def test_remote_tag_ahead_of_changelog_sets_baseline(self):
        self.git(self.root, "tag", "v1.5.0")
        self.git(self.root, "push", "origin", "refs/tags/v1.5.0")
        self.assertEqual(self.plan()["candidate"], "1.6.0")

    def test_stable_release_build_metadata_still_sets_baseline(self):
        self.github["releases"].append(published("1.5.0+build.7", 2))
        self.assertEqual(self.plan()["candidate"], "1.6.0")

    def test_missing_github_still_prepares_but_blocks_commit_and_binding(self):
        self.github = {"status": "unavailable", "reason": "Fixture offline"}
        plan = self.plan()
        self.assertEqual(plan["candidate"], "1.1.0")
        self.apply(plan)
        with self.assertRaisesRegex(release.PlanError, "GitHub"):
            release.check_plan(self.root, plan, "commit")
        with self.assertRaises(release.PlanError):
            release.bind_plan(self.root, plan)

    def test_draft_visibility_required(self):
        self.github["draft_visibility"] = False
        plan = self.plan()
        self.apply(plan)
        with self.assertRaisesRegex(release.PlanError, "Draft release coverage"):
            release.check_plan(self.root, plan, "commit")

    def test_drafts_and_prereleases_are_not_stable_and_reserve_candidate(self):
        self.github["releases"] += [published("1.1.0", 2, draft=True)]
        with self.assertRaisesRegex(release.PlanError, "reserved"):
            self.plan()
        self.github["releases"][1] = published("1.1.0-rc.1", 2, prerelease=True)
        with self.assertRaisesRegex(release.PlanError, "reserved"):
            self.plan()
        self.github["releases"][1] = published("2.0.0-rc.1", 2, prerelease=True)
        plan = self.plan()
        self.assertEqual(plan["baseline_summary"]["version"], "1.0.0")
        self.assertEqual(plan["candidate"], "1.1.0")

    def test_remote_changes_during_observation_are_rejected(self):
        config = release.validate_config(self.root, self.config)
        refs = release.remote_refs(self.root, config)
        changed = {**refs, "refs/tags/v9.0.0": "a" * 40}
        with patch.object(release, "remote_refs", side_effect=[refs, changed]):
            with self.assertRaisesRegex(release.PlanError, "during observation"):
                self.plan()
        with patch.object(release, "github_state", side_effect=[self.github, {"status": "unavailable"}]):
            with self.assertRaisesRegex(release.PlanError, "during observation"):
                self.plan()

    def test_publish_requires_binding_clean_exact_target_and_fresh_state(self):
        plan = self.plan()
        self.apply(plan)
        with self.assertRaisesRegex(release.PlanError, "binding"):
            release.check_plan(self.root, plan, "publish")
        self.integrate(plan)
        bound = release.bind_plan(self.root, plan)
        (self.root / "extra.txt").write_text("untracked")
        with self.assertRaisesRegex(release.PlanError, "clean"):
            release.check_plan(self.root, bound, "publish")
        (self.root / "extra.txt").unlink()
        self.github["releases"].append(published("1.1.0", 2))
        with self.assertRaisesRegex(release.PlanError, "Stale"):
            release.check_plan(self.root, bound, "publish")

    def test_binding_rejects_concurrent_unreleased_edit(self):
        plan = self.plan()
        self.integrate(plan)
        changelog = self.root / "CHANGELOG.md"
        changelog.write_text(changelog.read_text().replace("## [Unreleased]", "## [Unreleased]\n\n- Concurrent note."))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Concurrent note")
        self.git(self.root, "push", "origin", "main")
        with self.assertRaisesRegex(release.PlanError, "differs from plan"):
            release.bind_plan(self.root, plan)

    def test_expected_files_detect_manual_loss_of_unrelated_notes(self):
        plan = self.plan()
        self.apply(plan)
        changelog = self.root / "CHANGELOG.md"
        changelog.write_text(changelog.read_text().replace("- Independent preview improvements.\n", ""))
        with self.assertRaisesRegex(release.PlanError, "differs from plan"):
            release.check_plan(self.root, plan, "commit")

    def test_read_only_planning_no_git_refs_index_or_files_mutated(self):
        before = self.git(self.root, "status", "--porcelain")
        refs_before = self.git(self.root, "show-ref")
        files_before = {p: (self.root / p).read_bytes() for p in ("CHANGELOG.md", "TODO.md", "package.json")}
        self.plan()
        self.assertEqual(self.git(self.root, "status", "--porcelain"), before)
        self.assertEqual(self.git(self.root, "show-ref"), refs_before)
        self.assertEqual({p: (self.root / p).read_bytes() for p in files_before}, files_before)

    def test_fetching_advanced_target_does_not_update_tracking_refs(self):
        other = self.base / "other"
        self.git(self.base, "clone", "-b", "main", str(self.bare), str(other))
        self.git(other, "config", "user.name", "Fixture")
        self.git(other, "config", "user.email", "fixture@example.com")
        (other / "independent.txt").write_text("Concurrent work")
        self.git(other, "add", ".")
        self.git(other, "commit", "-m", "Remote advances")
        self.git(other, "push", "origin", "main")
        refs_before = self.git(self.root, "show-ref")
        with self.assertRaises(release.PlanError):
            self.plan()
        self.assertEqual(self.git(self.root, "show-ref"), refs_before)

    def test_already_reconciled_feature_branch_without_target_unreleased_hands_off(self):
        changelog = self.root / "CHANGELOG.md"
        target_text = "# Changelog\n\n## [1.0.0]" + CHANGELOG.split("## [1.0.0]", 1)[1]
        changelog.write_text(target_text)
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Target has no Unreleased section")
        self.git(self.root, "push", "origin", "main")
        self.git(self.root, "switch", "-c", "feat/verified-feature")
        note = "- Add filtered exports. (SRC-42) [issue](https://github.com/example/project/issues/42)\n"
        local_pending = "## [Unreleased]\n\n### Added\n\n" + note + "- Local-only future work.\n\n"
        changelog.write_text(target_text.replace("## [1.0.0]", local_pending + "## [1.0.0]", 1))
        (self.root / "TODO.md").write_text(TODO.replace("- [ ] SRC-42 Add filtered exports.\n", ""))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Reviewed feature and reconciled TODO")
        current = scope()
        current["items"][0]["unreleased"] = note
        plan = self.plan(scope=current)
        self.assertTrue(plan["preparation"]["target_to_local_diff"]["TODO.md"])
        self.apply(plan)
        release.check_plan(self.root, plan, "commit")
        text = changelog.read_text()
        pending, concrete = text.split("## [1.1.0]", 1)
        self.assertIn("Local-only future work.", pending)
        self.assertNotIn("SRC-42", pending)
        self.assertIn("SRC-42", concrete)
        self.assertIn("https://github.com/example/project/issues/42", concrete)
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Final reviewed metadata")
        self.git(self.root, "push", "origin", "HEAD:refs/heads/main")
        self.git(self.root, "branch", "--set-upstream-to", "origin/main")
        bound = release.bind_plan(self.root, plan)
        self.assertEqual(release.check_plan(self.root, bound, "publish")["status"], "checked")

    def test_creates_unreleased_when_both_target_and_local_lack_it(self):
        changelog = self.root / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [1.0.0]" + CHANGELOG.split("## [1.0.0]", 1)[1])
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "No pending section")
        self.git(self.root, "push", "origin", "main")
        current = scope()
        del current["items"][0]["unreleased"]
        plan = self.plan(scope=current)
        self.apply(plan)
        self.assertIn("## [Unreleased]", changelog.read_text())
        self.assertEqual(release.check_plan(self.root, plan, "commit")["status"], "checked")

    def test_reviewed_additive_pending_notes_and_provisional_version_are_preserved(self):
        changelog = self.root / "CHANGELOG.md"
        changelog.write_text(CHANGELOG.replace("- Add filtered exports.",
            "- Add filtered exports.\n- Local-only pending improvement."))
        todo = self.root / "TODO.md"
        todo.write_text(TODO.replace("- [ ] SRC-42 Add filtered exports.\n", "")
                        + "- [ ] SRC-101 Local future task.\n")
        package = self.root / "package.json"
        package.write_text(package.read_text().replace("1.0.0", "1.0.1"))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Reviewed feature metadata ahead of target")
        plan = self.plan()
        self.apply(plan)
        pending = changelog.read_text().split("## [1.1.0]", 1)[0]
        self.assertIn("Independent preview improvements.", pending)
        self.assertIn("Local-only pending improvement.", pending)
        self.assertIn("SRC-101", todo.read_text())
        self.assertEqual(release.check_plan(self.root, plan, "commit")["status"], "checked")

    def test_original_source_metadata_marker_and_issue_label_move_verbatim_once(self):
        source_id = "58de7268-2c67-4efa-a362-d9b4e04a7136"
        marker = "<!-- portfolio:id=" + source_id + " -->"
        opaque = "<!-- source:trace=preserve-this-field -->"
        issue = "https://github.com/example/portfolio/issues/399"
        row = "- [ ] Export filters (Portfolio #399) " + marker + "\n"
        target = "# Changelog\n\n## [1.0.0]" + CHANGELOG.split("## [1.0.0]", 1)[1]
        (self.root / "CHANGELOG.md").write_text(target)
        (self.root / "TODO.md").write_text(TODO.replace("- [ ] SRC-42 Add filtered exports.\n", row))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Target has persistent source identity")
        self.git(self.root, "push", "origin", "main")
        self.git(self.root, "switch", "-c", "feat/source-marker")
        self.git(self.root, "branch", "--set-upstream-to", "origin/main")
        note = f"- Add filtered exports. ([Portfolio #399]({issue})) {marker}\n  {opaque}\n"
        pending = "## [Unreleased]\n\n### Added\n\n" + note + "- Future local work.\n\n"
        (self.root / "CHANGELOG.md").write_text(target.replace("## [1.0.0]", pending + "## [1.0.0]", 1))
        (self.root / "TODO.md").write_text(TODO.replace("- [ ] SRC-42 Add filtered exports.\n", ""))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Reviewed feature already reconciled source")
        current = scope()
        current["items"][0].update(id=source_id, issues=[issue], unreleased=note,
                                   todo={"path": "TODO.md", "entry": row})
        plan = self.plan(scope=current)
        self.apply(plan)
        text = (self.root / "CHANGELOG.md").read_text()
        unreleased, concrete = text.split("## [1.1.0]", 1)
        self.assertNotIn(marker, unreleased)
        self.assertEqual(concrete.count(marker), 1)
        self.assertEqual(concrete.count(opaque), 1)
        self.assertIn(note.rstrip("\n"), concrete)
        self.assertNotIn("(" + source_id + ")", concrete)
        self.assertIn("[Portfolio #399](" + issue + ")", concrete)
        self.assertEqual(release.check_plan(self.root, plan, "commit")["status"], "checked")
        self.integrate(plan)
        bound = release.bind_plan(self.root, plan)
        self.assertEqual(release.check_plan(self.root, bound, "publish")["status"], "checked")

    def test_committed_feature_cannot_revert_unrelated_target_note_or_task(self):
        for value, removed in (("CHANGELOG.md", "- Independent preview improvements.\n"),
                               ("TODO.md", "- [ ] SRC-99 Independent preview improvements.\n")):
            with self.subTest(value=value):
                self.git(self.root, "switch", "-c", "feat/revert-" + value.replace(".", "-"))
                (self.root / value).write_text((self.root / value).read_text().replace(removed, ""))
                self.git(self.root, "add", ".")
                self.git(self.root, "commit", "-m", "Stale committed copy")
                with self.assertRaisesRegex(release.PlanError, "unrelated.*removed or reverted"):
                    self.plan()
                self.git(self.root, "switch", "main")

    def test_stale_local_metadata_cannot_drop_current_target_content(self):
        for value in ("CHANGELOG.md", "TODO.md", "package.json"):
            with self.subTest(value=value):
                original = (self.root / value).read_text()
                if value == "CHANGELOG.md":
                    advanced = original.replace("### Added", "### Added\n\n- Mainline-only urgent fix.", 1)
                elif value == "TODO.md":
                    advanced = original + "- [ ] SRC-100 Mainline-only task.\n"
                else:
                    advanced = original.replace('"name":"fixture"', '"name":"fixture-new"')
                (self.root / value).write_text(advanced)
                self.git(self.root, "add", value)
                self.git(self.root, "commit", "-m", "Current target metadata")
                self.git(self.root, "push", "origin", "main")
                (self.root / value).write_text(original)
                with self.assertRaisesRegex(release.PlanError, "preimage differs from target"):
                    self.plan()
                (self.root / value).write_text(advanced)

    def test_binding_rejects_new_release_that_changes_candidate(self):
        plan = self.plan()
        self.integrate(plan)
        self.github["releases"].append(published("1.2.0", identity=2))
        with self.assertRaisesRegex(release.PlanError, "changes the candidate"):
            release.bind_plan(self.root, plan)

    def test_binding_preserves_version_source_only_prior_baseline(self):
        changelog = self.root / "CHANGELOG.md"
        changelog.write_text(CHANGELOG.split("## [1.0.0]", 1)[0])
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Version source is sole baseline")
        self.git(self.root, "push", "origin", "main")
        self.git(self.root, "push", "origin", ":refs/tags/v1.0.0")
        self.git(self.root, "tag", "-d", "v1.0.0")
        self.github["releases"] = []
        plan = self.plan()
        self.assertEqual(plan["candidate"], "1.1.0")
        self.integrate(plan)
        bound = release.bind_plan(self.root, plan)
        self.assertEqual(bound["binding_selection_baseline"]["version"], "1.0.0")
        self.assertEqual(release.check_plan(self.root, bound, "publish")["status"], "checked")

    def test_crlf_content_survives_remote_observation_and_binding(self):
        for value in ("CHANGELOG.md", "TODO.md", "package.json"):
            file_path = self.root / value
            file_path.write_bytes(file_path.read_bytes().replace(b"\n", b"\r\n"))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "CRLF fixture")
        self.git(self.root, "push", "origin", "main")
        current = scope()
        for item in current["items"]:
            item["todo"]["entry"] = item["todo"]["entry"].replace("\n", "\r\n")
            if "unreleased" in item:
                item["unreleased"] = item["unreleased"].replace("\n", "\r\n")
        plan = self.plan(scope=current)
        self.integrate(plan)
        bound = release.bind_plan(self.root, plan)
        self.assertEqual(release.check_plan(self.root, bound, "publish")["status"], "checked")

    def test_duplicate_or_partial_scoped_entries_rejected(self):
        current = scope()
        current["items"][0]["todo"]["entry"] = "SRC-42 Add filtered exports.\n"
        with self.assertRaisesRegex(release.PlanError, "line boundary"):
            self.plan(scope=current)
        (self.root / "TODO.md").write_text(TODO + "- [ ] SRC-42 Add filtered exports.\n")
        with self.assertRaisesRegex(release.PlanError, "ambiguous"):
            self.plan()

    def test_paths_and_symlinks_do_not_escape_repository(self):
        for value in ("../outside", "/tmp/outside", ".git/config"):
            with self.subTest(value=value), self.assertRaises(release.PlanError):
                release.safe_path(self.root, value)
        (self.root / "linked").symlink_to(self.base / "outside")
        with self.assertRaises(release.PlanError):
            release.safe_path(self.root, "linked")

    def test_source_conflict_is_ambiguous(self):
        package = self.root / "package.json"
        package.write_text(package.read_text().replace("1.0.0", "1.0.1"))
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-m", "Conflicting sources")
        self.git(self.root, "push", "origin", "main")
        with self.assertRaisesRegex(release.PlanError, "disagree"):
            self.plan()

    def test_plan_output_exclusive_private_and_reloadable(self):
        plan = self.plan()
        target = self.base / "plan.json"
        release.write_json(plan, target)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(release.load_plan(self.root, target)["candidate"], "1.1.0")
        with self.assertRaises(FileExistsError):
            release.write_json(plan, target)

    def test_complete_pagination_distinct_draft_and_publication_state(self):
        self.reader.stop()
        releases = [published(), published("2.0.0-rc.1", 2, prerelease=True), published("3.0.0", 3, draft=True)]
        responses = [json.dumps({"full_name": "example/project", "permissions": {"push": True}}),
                     json.dumps([[releases[0]], releases[1:]])]
        with patch.object(release, "run", side_effect=responses) as command:
            actual = release.github_state(self.root, {"github": "github.com/example/project"})
        self.assertEqual(actual["status"], "available")
        self.assertEqual(len(actual["releases"]), 3)
        self.assertIn("--paginate", command.call_args_list[1].args)
        self.assertIn("--slurp", command.call_args_list[1].args)

    def test_github_failures_and_malformed_coverage_do_not_become_absence(self):
        self.reader.stop()
        for response in ([{"full_name": "other/project"}],
                         [{"full_name": "example/project"}, {}],
                         [{"full_name": "example/project"}, [[published(), published()]]]):
            with self.subTest(response=response), patch.object(release, "run", side_effect=[json.dumps(x) for x in response]):
                actual = release.github_state(self.root, {"github": "github.com/example/project"})
                self.assertEqual(actual["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
