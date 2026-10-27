"""Exercise cleanup boundaries using an isolated home and stubbed macOS tools."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mac_disk_cleanup.sh"


class DiskCleanupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.work = self.root / "work"
        self.tools = self.root / "bin"
        self.work.mkdir()
        self.tools.mkdir()
        for folder in (
            ".cache",
            "Library/Caches",
            "Library/Developer/Xcode/DerivedData",
            "Library/Containers",
            "Library/Group Containers",
        ):
            (self.home / folder).mkdir(parents=True, exist_ok=True)
        bodies = {
            "df": "exit 0",
            "diskutil": "exit 0",
            "tmutil": 'if [ "$1" = thinlocalsnapshots ]; then printf "tmutil %s\\n" "$*" >> "$CASE_LOG"; fi\nexit 0',
            "pgrep": "exit 1",
            "lsof": '''case "${LSOF_MODE:-idle}" in
    idle) exit 1 ;;
    active) printf '123\\n'; exit 0 ;;
    warning) printf 'lsof: WARNING: permission denied\\n' >&2; exit 1 ;;
    mixed) printf '123\\n'; printf 'lsof: WARNING: permission denied\\n' >&2; exit 0 ;;
    error) exit 2 ;;
esac''',
            "npm": '''printf "npm %s\\n" "$*" >> "$CASE_LOG"
if [ "$*" = "config get cache" ]; then
    [ "${NPM_DISCOVERY_FAIL:-0}" = 1 ] && exit 8
    printf '%s\\n' "${NPM_CACHE_DIR:-$HOME/.npm}"
    exit 0
fi
if [ "$*" = "cache verify" ] && [ "${NPM_VERIFY_FAIL:-0}" = 1 ]; then exit 7; fi
exit 0''',
            "uv": '''printf "uv %s\\n" "$*" >> "$CASE_LOG"
if [ "$*" = "cache dir" ]; then
    [ "${UV_DISCOVERY_FAIL:-0}" = 1 ] && exit 8
    printf '%s\\n' "${UV_CACHE_DIR:-$HOME/.cache/uv}"
    exit 0
fi
exit 0''',
        }
        for name, body in bodies.items():
            tool = self.tools / name
            tool.write_text("#!/bin/sh\n" + body + "\n")
            tool.chmod(0o755)
        self.log = self.root / "calls.log"

    def run_cleanup(self, *args, **overrides):
        environment = {
            **os.environ,
            "HOME": str(self.home),
            "PATH": str(self.tools) + ":/usr/bin:/bin",
            "CASE_LOG": str(self.log),
            "LSOF_MODE": "idle",
            **overrides,
        }
        return subprocess.run(
            ["/bin/sh", str(SCRIPT), *args],
            cwd=self.work,
            env=environment,
            text=True,
            capture_output=True,
            timeout=20,
        )

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_default_and_explicit_dry_run_do_not_mutate_caches(self):
        cache = self.home / ".cache" / "artifact"
        cache.write_text("cached content")
        for arguments in ((), ("--dry-run",)):
            with self.subTest(arguments=arguments):
                result = self.run_cleanup(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(cache.read_text(), "cached content")
                self.assertEqual(self.calls(), [])

    def test_apply_handles_newlines_and_hidden_names_without_touching_cwd(self):
        unrelated = self.work / "KEEP.md"
        unrelated.write_text("user content")
        eligible = self.home / ".cache" / "artifact\nKEEP.md"
        eligible.mkdir()
        hidden = self.home / "Library/Caches" / ".hidden"
        hidden.write_text("cache")
        sandbox = self.home / "Library/Containers" / "bundle\nKEEP.md" / "Data/Library/Caches"
        sandbox.mkdir(parents=True)
        sandbox_artifact = sandbox / "artifact"
        sandbox_artifact.write_text("cache")
        model = self.home / ".cache/whisper"
        model.mkdir()
        (model / "model.bin").write_text("model")
        npm_cache = self.home / ".npm"
        npm_cache.mkdir()
        uv_cache = self.home / ".cache/uv"
        uv_cache.mkdir()

        result = self.run_cleanup("--apply-safe")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(eligible.exists())
        self.assertFalse(hidden.exists())
        self.assertFalse(sandbox_artifact.exists())
        self.assertEqual(unrelated.read_text(), "user content")
        self.assertTrue((model / "model.bin").exists())
        self.assertIn("npm config get cache", self.calls())
        self.assertIn("npm cache clean --force", self.calls())
        self.assertIn("npm cache verify", self.calls())
        self.assertIn("uv cache dir", self.calls())
        self.assertIn("uv cache prune", self.calls())

    def test_active_or_inconclusive_handles_preserve_targets_and_skip_npm(self):
        cache = self.home / ".cache" / "artifact"
        cache.write_text("cache")
        for mode in ("active", "warning", "mixed", "error"):
            with self.subTest(mode=mode):
                result = self.run_cleanup("--apply-safe", LSOF_MODE=mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(cache.exists())
                self.assertFalse(any(call in {"npm cache clean --force", "npm cache verify"} for call in self.calls()))

    def test_npm_verification_failure_is_reported(self):
        result = self.run_cleanup("--apply-safe", NPM_VERIFY_FAIL="1")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(
            self.calls(),
            ["npm config get cache", "uv cache dir", "npm cache clean --force", "npm cache verify"],
        )

    def test_custom_cache_discovery_preserves_all_cache_paths(self):
        custom_npm = self.home / ".cache" / "custom-npm"
        custom_npm.mkdir()
        custom_file = custom_npm / "data"
        custom_file.write_text("package cache")
        default_uv = self.home / ".cache" / "uv"
        default_uv.mkdir()
        uv_file = default_uv / "data"
        uv_file.write_text("uv cache")
        generic = self.home / "Library/Caches" / "artifact"
        generic.write_text("generic cache")

        result = self.run_cleanup(
            "--apply-safe", NPM_CACHE_DIR=str(custom_npm), UV_CACHE_DIR=str(default_uv)
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(custom_file.exists())
        self.assertTrue(uv_file.exists())
        self.assertTrue(generic.exists())
        self.assertFalse(any(call in {"npm cache clean --force", "npm cache verify", "uv cache prune"} for call in self.calls()))

    def test_failed_cache_discovery_performs_no_cache_mutations(self):
        cache = self.home / "Library/Caches" / "artifact"
        cache.write_text("generic cache")

        result = self.run_cleanup("--apply-safe", NPM_DISCOVERY_FAIL="1")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(cache.exists())
        self.assertFalse(any(call in {"npm cache clean --force", "npm cache verify", "uv cache prune"} for call in self.calls()))

    def test_custom_uv_cache_discovery_performs_no_cache_mutations(self):
        custom_uv = self.home / ".cache" / "custom-uv"
        custom_uv.mkdir()
        custom_file = custom_uv / "data"
        custom_file.write_text("uv cache")
        generic = self.home / "Library/Caches" / "artifact"
        generic.write_text("generic cache")

        result = self.run_cleanup("--apply-safe", UV_CACHE_DIR=str(custom_uv))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(custom_file.exists())
        self.assertTrue(generic.exists())
        self.assertFalse(any(call in {"npm cache clean --force", "npm cache verify", "uv cache prune"} for call in self.calls()))

    def test_failed_uv_cache_discovery_performs_no_cache_mutations(self):
        cache = self.home / "Library/Caches" / "artifact"
        cache.write_text("generic cache")

        result = self.run_cleanup("--apply-safe", UV_DISCOVERY_FAIL="1")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(cache.exists())
        self.assertFalse(any(call in {"npm cache clean --force", "npm cache verify", "uv cache prune"} for call in self.calls()))


if __name__ == "__main__":
    unittest.main()
