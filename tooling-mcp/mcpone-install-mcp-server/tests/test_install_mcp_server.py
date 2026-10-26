"""Offline fixtures for the McpOne installer and JSON config sync."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts/install_mcp_server.py"
SPEC = importlib.util.spec_from_file_location("install_mcp_server", SCRIPT)
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


def create_db(path: pathlib.Path, config_paths: dict[str, pathlib.Path]) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_MAX INTEGER);
        INSERT INTO Z_PRIMARYKEY VALUES (2, 0);
        CREATE TABLE ZADDEDAPP (
            Z_PK INTEGER PRIMARY KEY, ZNAME TEXT, ZAIAGENTJSONFILEPATH TEXT,
            ZAIAGENTJSONKEY TEXT, ZACTIVECLUSTERID TEXT
        );
        CREATE TABLE ZCLUSTER (
            Z_PK INTEGER PRIMARY KEY, ZID TEXT, ZAPP INTEGER, ZNAME TEXT,
            ZENABLEDADDEDSERVERIDSDATA BLOB, Z_OPT INTEGER, ZUPDATEDAT REAL
        );
        CREATE TABLE ZADDEDSERVER (
            Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER,
            ZCREATEDAT REAL, ZUPDATEDAT REAL, ZCOMMAND TEXT, ZID TEXT,
            ZNAME TEXT, ZSERVERID TEXT, ZSOURCE TEXT, ZTYPE TEXT, ZURL TEXT,
            ZVERSION TEXT, ZARGS BLOB, ZPARAMETERS BLOB, ZENV BLOB, ZHEADERS BLOB
        );
        """
    )
    for index, (app_name, config_path) in enumerate(config_paths.items(), 1):
        active_cluster_id = f"cluster-{index}"
        connection.execute(
            "INSERT INTO ZADDEDAPP VALUES (?, ?, ?, ?, ?)",
            (
                index,
                app_name,
                str(config_path) if app_name != "Codex" else None,
                "mcpServers" if app_name != "Codex" else None,
                active_cluster_id,
            ),
        )
        connection.execute(
            "INSERT INTO ZCLUSTER VALUES (?, ?, ?, ?, ?, 1, 0)",
            (index, active_cluster_id, index, "Active", b"[]"),
        )
    connection.commit()
    connection.close()


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_http_install_syncs_active_json_agents_and_preserves_other_entries(self) -> None:
        apps = ("Claude", "Gemini CLI", "Antigravity", "Codex")
        config_paths = {name: self.root / f"{name.replace(' ', '-')}.json" for name in apps}
        original = {}
        for app, path in config_paths.items():
            document = {
                "mcpServers": {
                    "local-helper": {"command": "helper", "args": []},
                    "home-assistant_id_HASS01": {"type": "stdio"},
                },
                "unrelated": {"preserve": True},
            }
            path.write_text(json.dumps(document), encoding="utf-8")
            original[app] = path.read_bytes()

        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, config_paths)
        stdout = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--name",
                "Home Assistant",
                "--id",
                "HASS01",
                "--server-url",
                "https://ha.example/api/mcp",
                "--header",
                "Authorization=Bearer secret",
                "--all-active-clusters",
                "--sync-json-agent-configs",
                "--mcpone-db",
                str(db_path),
            ],
        ), contextlib.redirect_stdout(stdout):
            result = INSTALLER.main()

        self.assertEqual(result, 0)
        self.assertIn("enabled_clusters=", stdout.getvalue())
        self.assertIn("synced_json_configs=", stdout.getvalue())
        for app in apps[:3]:
            document = json.loads(config_paths[app].read_text(encoding="utf-8"))
            self.assertEqual(document["unrelated"], {"preserve": True})
            self.assertEqual(document["mcpServers"]["local-helper"]["command"], "helper")
            self.assertNotIn("home-assistant_id_HASS01", document["mcpServers"])
            self.assertTrue(list(self.root.glob(f"{config_paths[app].name}.bak-*")))
            expected = {
                "type": "http",
                "url": "https://ha.example/api/mcp",
                "headers": {"Authorization": "Bearer secret"},
            }
            if app == "Gemini CLI":
                expected = {
                    "httpUrl": "https://ha.example/api/mcp",
                    "headers": {"Authorization": "Bearer secret"},
                }
            elif app == "Antigravity":
                expected = {
                    "serverUrl": "https://ha.example/api/mcp",
                    "headers": {"Authorization": "Bearer secret"},
                }
            self.assertEqual(document["mcpServers"]["home-assistant"], expected)

        self.assertEqual(config_paths["Codex"].read_bytes(), original["Codex"])
        self.assertFalse(list(self.root.glob("Codex.json.bak-*")))
        connection = sqlite3.connect(db_path)
        server = connection.execute(
            "SELECT ZTYPE, ZURL, ZHEADERS FROM ZADDEDSERVER WHERE ZID='HASS01'"
        ).fetchone()
        enabled = connection.execute(
            "SELECT ZENABLEDADDEDSERVERIDSDATA FROM ZCLUSTER ORDER BY Z_PK"
        ).fetchall()
        connection.close()
        self.assertEqual(server[0:2], ("STREAMABLE_HTTP", "https://ha.example/api/mcp"))
        self.assertEqual(json.loads(server[2]), {"Authorization": "Bearer secret"})
        self.assertEqual([json.loads(row[0]) for row in enabled], [["HASS01"]] * 4)

    def test_same_id_update_replaces_its_old_canonical_http_entry(self) -> None:
        config_path = self.root / "claude.json"
        config_path.write_text('{"mcpServers":{}}\n', encoding="utf-8")
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": config_path})
        common = [
            str(SCRIPT), "--name", "Report Agent", "--id", "RPT123",
            "--server-url", "https://report.example/v1", "--header",
            "Authorization=Bearer old-token", "--all-active-clusters",
            "--sync-json-agent-configs", "--mcpone-db", str(db_path),
        ]
        with mock.patch.object(sys, "argv", common), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(INSTALLER.main(), 0)
        update = common.copy()
        update[update.index("https://report.example/v1")] = "https://report.example/v2"
        update[update.index("Authorization=Bearer old-token")] = "Authorization=Bearer new-token"
        with mock.patch.object(sys, "argv", update), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(INSTALLER.main(), 0)
        document = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            document["mcpServers"]["report-agent"],
            {
                "type": "http",
                "url": "https://report.example/v2",
                "headers": {"Authorization": "Bearer new-token"},
            },
        )
        self.assertEqual(len(list(self.root.glob("claude.json.bak-*"))), 2)

    def test_wal_committed_data_is_present_in_sqlite_backup(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {})
        writer = sqlite3.connect(db_path)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE wal_receipt (value TEXT)")
        writer.execute("INSERT INTO wal_receipt VALUES ('committed-in-wal')")
        writer.commit()
        self.assertTrue(pathlib.Path(str(db_path) + "-wal").exists())
        backup = INSTALLER.backup_sqlite_database(db_path)
        copied = sqlite3.connect(backup)
        row = copied.execute("SELECT value FROM wal_receipt").fetchone()
        copied.close()
        writer.close()
        self.assertEqual(row[0], "committed-in-wal")

    def test_gemini_local_source_legacy_keys_migrate_on_renamed_update(self) -> None:
        config_path = self.root / "gemini.json"
        old_value = {
            "url": "https://old.example/mcp",
            "headers": {"Authorization": "Bearer old-token"},
        }
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "Old Name": old_value,
                        "old-name": old_value,
                        "New Name": old_value,
                        "Old_Name_id_MON123": {"legacy": True},
                        "other-server": {"url": "https://other.example/sse"},
                    }
                }
            ),
            encoding="utf-8",
        )
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Gemini CLI": config_path})
        connection = sqlite3.connect(db_path)
        connection.execute(
            "UPDATE ZCLUSTER SET ZENABLEDADDEDSERVERIDSDATA=?",
            (json.dumps(["MON123"]).encode("utf-8"),),
        )
        connection.execute(
            """INSERT INTO ZADDEDSERVER VALUES (
                1, 2, 1, 0, 0, '', 'MON123', 'Old Name', '', 'imported',
                'STREAMABLE_HTTP', 'https://old.example/mcp', '1.0.0',
                X'5B5D', X'7B7D', X'7B7D', ?
            )""",
            (json.dumps({"Authorization": "Bearer old-token"}).encode("utf-8"),),
        )
        connection.commit()
        connection.close()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT), "--name", "New Name", "--id", "MON123",
                "--server-url", "https://new.example/mcp", "--header",
                "Authorization=Bearer new-token", "--all-active-clusters",
                "--sync-json-agent-configs", "--mcpone-db", str(db_path),
            ],
        ), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(INSTALLER.main(), 0)
        servers = json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"]
        self.assertNotIn("Old Name", servers)
        self.assertNotIn("old-name", servers)
        self.assertNotIn("New Name", servers)
        self.assertNotIn("Old_Name_id_MON123", servers)
        self.assertEqual(servers["other-server"], {"url": "https://other.example/sse"})
        self.assertEqual(
            servers["new-name"],
            {
                "httpUrl": "https://new.example/mcp",
                "headers": {"Authorization": "Bearer new-token"},
            },
        )

    def test_signed_endpoint_and_headers_are_redacted_from_dry_run(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Codex": self.root / "Codex.json"})
        endpoint = "https://user:pass@safe.example/mcp?token=query-secret#fragment-secret"
        stdout = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT), "--server-url", endpoint, "--header",
                "Authorization=Bearer header-secret", "--env", "API_TOKEN=env-secret",
                "--dry-run", "--mcpone-db", str(db_path),
            ],
        ), contextlib.redirect_stdout(stdout):
            self.assertEqual(INSTALLER.main(), 0)
        output = stdout.getvalue()
        self.assertIn("url=https://safe.example/mcp", output)
        for secret in (
            "user", "pass", "query-secret", "fragment-secret", "header-secret", "env-secret"
        ):
            self.assertNotIn(secret, output)

    def test_install_preserves_signed_endpoint_in_database_but_redacts_output(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Codex": self.root / "Codex.json"})
        endpoint = "https://user:pass@safe.example/mcp?token=query-secret#fragment-secret"
        stdout = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT), "--server-url", endpoint, "--id", "URL123",
                "--app-name", "Codex", "--cluster-name", "Active",
                "--mcpone-db", str(db_path),
            ],
        ), contextlib.redirect_stdout(stdout):
            self.assertEqual(INSTALLER.main(), 0)
        output = stdout.getvalue()
        self.assertIn("url=https://safe.example/mcp", output)
        for secret in ("user", "pass", "query-secret", "fragment-secret"):
            self.assertNotIn(secret, output)
        connection = sqlite3.connect(db_path)
        stored_url = connection.execute(
            "SELECT ZURL FROM ZADDEDSERVER WHERE ZID='URL123'"
        ).fetchone()[0]
        connection.close()
        self.assertEqual(stored_url, endpoint)

    def test_config_changed_after_preflight_is_not_overwritten(self) -> None:
        first = self.root / "claude.json"
        second = self.root / "gemini.json"
        first_original = b'{"mcpServers":{"keep":{"first":true}}}\n'
        second_original = b'{"mcpServers":{"keep":{"second":true}}}\n'
        first.write_bytes(first_original)
        second.write_bytes(second_original)
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": first, "Gemini CLI": second})
        plan = INSTALLER.prepare_streamable_http_json_configs(
            db_path, "MON123", "monitor", "https://monitor.example/mcp", {},
            "Codex", "Cluster A", True,
        )
        concurrent_edit = b'{"mcpServers":{"user-edit":{"preserve":true}}}\n'
        second.write_bytes(concurrent_edit)
        before_db = db_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "changed after preflight"):
            INSTALLER.upsert_mcpone(
                db_path, "MON123", "monitor", "", [], {}, {},
                "https://monitor.example/mcp", "imported", "STREAMABLE_HTTP",
                "1.0.0", "Codex", "Cluster A", True, plan,
            )
        self.assertEqual(first.read_bytes(), first_original)
        self.assertEqual(second.read_bytes(), concurrent_edit)
        self.assertEqual(db_path.read_bytes(), before_db)
        self.assertFalse(list(self.root.glob("claude.json.bak-*")))

    def test_symlinked_json_config_is_rejected_before_mutation(self) -> None:
        target = self.root / "target.json"
        original = b'{"mcpServers":{"keep":{"command":"helper"}}}\n'
        target.write_bytes(original)
        link = self.root / "claude.json"
        link.symlink_to(target)
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": link})
        before_db = db_path.read_bytes()
        with mock.patch.object(
            sys,
            "argv",
            [str(SCRIPT), "--name", "safe-agent", "--id", "SAFE01",
             "--server-url", "https://safe.example/mcp", "--all-active-clusters",
             "--sync-json-agent-configs", "--mcpone-db", str(db_path)],
        ), self.assertRaisesRegex(RuntimeError, "Refusing symlinked agent config"):
            INSTALLER.main()
        self.assertTrue(link.is_symlink())
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(db_path.read_bytes(), before_db)
        self.assertFalse(list(self.root.glob("*.bak-*")))

    def test_incompatible_sync_option_fails_before_database_or_backup_mutation(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {})
        before = db_path.read_bytes()
        stderr = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--command",
                "npx",
                "--sync-json-agent-configs",
                "--mcpone-db",
                str(db_path),
            ],
        ), contextlib.redirect_stderr(stderr):
            result = INSTALLER.main()
        self.assertEqual(result, 2)
        self.assertIn("requires --server-url", stderr.getvalue())
        self.assertEqual(db_path.read_bytes(), before)
        self.assertFalse(list(self.root.glob("McpOne.sqlite.bak-*")))

    def test_server_url_conflicts_with_stdio_inputs_before_mutation(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {})
        before = db_path.read_bytes()
        stderr = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--server-url",
                "https://mcp.example/api",
                "--command",
                "npx",
                "--mcpone-db",
                str(db_path),
            ],
        ), contextlib.redirect_stderr(stderr):
            result = INSTALLER.main()
        self.assertEqual(result, 2)
        self.assertIn("mutually exclusive", stderr.getvalue())
        self.assertEqual(db_path.read_bytes(), before)
        self.assertFalse(list(self.root.glob("McpOne.sqlite.bak-*")))

    def test_legacy_stdio_dry_run_contract_remains_available(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {})
        before = db_path.read_bytes()
        stdout = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--name",
                "legacy-server",
                "--command",
                "npx",
                "--arg=-y",
                "--arg",
                "legacy-server",
                "--env",
                "TOKEN=value",
                "--dry-run",
                "--mcpone-db",
                str(db_path),
            ],
        ), contextlib.redirect_stdout(stdout):
            result = INSTALLER.main()
        self.assertEqual(result, 0)
        output = stdout.getvalue()
        self.assertIn("command=npx", output)
        self.assertIn('args=["-y", "legacy-server"]', output)
        self.assertIn('env_names=["TOKEN"]', output)
        self.assertNotIn("value", output)
        self.assertIn("type=STDIO", output)
        self.assertEqual(db_path.read_bytes(), before)
        self.assertFalse(list(self.root.glob("McpOne.sqlite.bak-*")))

    def test_generic_server_name_and_id_alias_variants_are_replaced(self) -> None:
        config_path = self.root / "claude.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "my-monitor[id=MON123]": {"old": True},
                        "my-monitor_idMON123": {"old": True},
                        "my-monitor_id_MON123": {"old": True},
                        "My Monitor_id_MON123": {"old": True},
                        "My_Monitor_id_MON123": {"old": True},
                        "other-monitor_id_OTHER1": {"keep": True},
                    }
                }
            ),
            encoding="utf-8",
        )
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": config_path})
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--name",
                "My Monitor",
                "--id",
                "MON123",
                "--server-url",
                "https://monitor.example/mcp",
                "--all-active-clusters",
                "--sync-json-agent-configs",
                "--mcpone-db",
                str(db_path),
            ],
        ), contextlib.redirect_stdout(io.StringIO()):
            result = INSTALLER.main()
        self.assertEqual(result, 0)
        servers = json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"]
        self.assertNotIn("my-monitor[id=MON123]", servers)
        self.assertNotIn("my-monitor_idMON123", servers)
        self.assertNotIn("my-monitor_id_MON123", servers)
        self.assertNotIn("My Monitor_id_MON123", servers)
        self.assertNotIn("My_Monitor_id_MON123", servers)
        self.assertEqual(servers["other-monitor_id_OTHER1"], {"keep": True})
        self.assertEqual(servers["my-monitor"]["url"], "https://monitor.example/mcp")
        self.assertTrue(
            INSTALLER.target_alias_pattern("home-assistant", "HASS01").fullmatch(
                "Home_Assistant_id_HASS01"
            )
        )

    def test_preflight_parses_and_guards_the_same_config_bytes(self) -> None:
        config = self.root / "claude.json"
        config.write_bytes(b'{"mcpServers":{}}\n')
        concurrent = b'{"mcpServers":{},"concurrent_edit":true}\n'
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": config})
        before_db = db_path.read_bytes()
        original_text_read = pathlib.Path.read_text
        original_byte_read = pathlib.Path.read_bytes
        changed = False

        def change_after_read(reader):
            def read(file_path, *args, **kwargs):
                nonlocal changed
                content = reader(file_path, *args, **kwargs)
                if file_path == config and not changed:
                    changed = True
                    config.write_bytes(concurrent)
                return content
            return read

        with mock.patch.object(
            pathlib.Path, "read_text", change_after_read(original_text_read)
        ), mock.patch.object(
            pathlib.Path, "read_bytes", change_after_read(original_byte_read)
        ), mock.patch.object(
            sys,
            "argv",
            [str(SCRIPT), "--name", "Monitor", "--id", "MON123",
             "--server-url", "https://monitor.example/mcp", "--all-active-clusters",
             "--sync-json-agent-configs", "--mcpone-db", str(db_path)],
        ), self.assertRaisesRegex(RuntimeError, "changed after preflight"):
            INSTALLER.main()

        self.assertTrue(changed)
        self.assertEqual(config.read_bytes(), concurrent)
        self.assertEqual(db_path.read_bytes(), before_db)

    def test_invalid_later_agent_config_preflights_without_any_mutation(self) -> None:
        for case in ("missing", "malformed", "wrong-shape"):
            with self.subTest(case=case):
                root = self.root / case
                root.mkdir()
                good = root / "a-good.json"
                bad = root / "z-bad.json"
                good.write_text('{"mcpServers":{"keep":{"x":1}}}\n', encoding="utf-8")
                if case == "malformed":
                    bad.write_text("{invalid", encoding="utf-8")
                elif case == "wrong-shape":
                    bad.write_text('{"mcpServers":[]}\n', encoding="utf-8")
                # The missing case intentionally leaves the selected path absent.
                db_path = root / "McpOne.sqlite"
                create_db(db_path, {"Claude": good, "Gemini CLI": bad})
                before_db = db_path.read_bytes()
                before_good = good.read_bytes()
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        str(SCRIPT),
                        "--name",
                        "monitor",
                        "--id",
                        "MON123",
                        "--server-url",
                        "https://monitor.example/mcp",
                        "--all-active-clusters",
                        "--sync-json-agent-configs",
                        "--mcpone-db",
                        str(db_path),
                    ],
                ), self.assertRaises(RuntimeError):
                    INSTALLER.main()
                self.assertEqual(db_path.read_bytes(), before_db)
                self.assertEqual(good.read_bytes(), before_good)
                self.assertFalse(list(root.glob("*.bak-*")))

    def test_same_name_unidentified_entry_is_not_overwritten(self) -> None:
        config_path = self.root / "claude.json"
        original = b'{"mcpServers":{"my-monitor":{"command":"unrelated"}}}\n'
        config_path.write_bytes(original)
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": config_path})
        before_db = db_path.read_bytes()
        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--name",
                "My Monitor",
                "--id",
                "MON123",
                "--server-url",
                "https://monitor.example/mcp",
                "--all-active-clusters",
                "--sync-json-agent-configs",
                "--mcpone-db",
                str(db_path),
            ],
        ), self.assertRaisesRegex(RuntimeError, "Refusing to replace same-name"):
            INSTALLER.main()
        self.assertEqual(config_path.read_bytes(), original)
        self.assertEqual(db_path.read_bytes(), before_db)
        self.assertFalse(list(self.root.glob("*.bak-*")))

    def test_failed_later_replace_restores_prior_files_and_rolls_back_database(self) -> None:
        first = self.root / "claude.json"
        second = self.root / "gemini.json"
        first_original = b'{"mcpServers":{"first":{"keep":true}}}\n'
        second_original = b'{"mcpServers":{"second":{"keep":true}}}\n'
        first.write_bytes(first_original)
        second.write_bytes(second_original)
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {"Claude": first, "Gemini CLI": second})
        before_db = db_path.read_bytes()
        original_replace = INSTALLER.os.replace
        replacements = 0

        def fail_second_replace(source, destination):
            nonlocal replacements
            replacements += 1
            if replacements == 2:
                raise OSError("injected replace failure")
            return original_replace(source, destination)

        with mock.patch.object(
            sys,
            "argv",
            [
                str(SCRIPT),
                "--name",
                "monitor",
                "--id",
                "MON123",
                "--server-url",
                "https://monitor.example/mcp",
                "--all-active-clusters",
                "--sync-json-agent-configs",
                "--mcpone-db",
                str(db_path),
            ],
        ), mock.patch.object(INSTALLER.os, "replace", side_effect=fail_second_replace), self.assertRaisesRegex(
            RuntimeError, "prior files were restored"
        ):
            INSTALLER.main()
        self.assertEqual(first.read_bytes(), first_original)
        self.assertEqual(second.read_bytes(), second_original)
        self.assertEqual(db_path.read_bytes(), before_db)
        self.assertEqual(len(list(self.root.glob("claude.json.bak-*"))), 1)
        self.assertEqual(len(list(self.root.glob("gemini.json.bak-*"))), 1)

    def test_malformed_key_value_errors_do_not_echo_secret_values(self) -> None:
        db_path = self.root / "McpOne.sqlite"
        create_db(db_path, {})
        for option in ("--env", "--header"):
            with self.subTest(option=option):
                stderr = io.StringIO()
                with mock.patch.object(
                    sys,
                    "argv",
                    [
                        str(SCRIPT),
                        "--command",
                        "npx",
                        option,
                        "Authorization: Bearer top-secret",
                        "--mcpone-db",
                        str(db_path),
                    ],
                ), contextlib.redirect_stderr(stderr), self.assertRaises(ValueError):
                    INSTALLER.main()
                self.assertNotIn("top-secret", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
