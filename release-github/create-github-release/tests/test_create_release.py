"""Local Git + synthetic GitHub/gate tests. Never contacts a publication service."""

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import unittest
from unittest.mock import patch


SKILLS = Path(__file__).resolve().parents[2]


def load(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pub = load("publisher_under_test", SKILLS / "create-github-release/scripts/create_release.py")
fixtures = load("release_fixtures", SKILLS / "update-release/tests/test_release_plan.py")
guard = fixtures.release


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                                                   "GIT_TERMINAL_PROMPT": "0"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.fixture = fixtures.GitFixture()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.base = self.fixture.root, self.fixture.base
        self.real_run = pub.run
        self.repository = "github.com/example/project"
        actual_identity = guard.remote_identity(self.root, {"remote": "origin"})
        self.helper_identity = {**actual_identity, "github": self.repository}
        self.identity = {"repository": self.repository,
                         "fetch_hash": actual_identity["fetch_hash"], "push_hash": actual_identity["push_hash"]}
        for target, field, side_effect in (
            (guard, "remote_identity", lambda *_: copy.deepcopy(self.helper_identity)),
            (pub, "repository_identity", lambda *_: copy.deepcopy(self.identity)),
            (pub, "load_guard", lambda: guard),
        ):
            mock = patch.object(target, field, side_effect=side_effect)
            mock.start()
            self.addCleanup(mock.stop)
        self.plan = self.fixture.plan()
        self.fixture.integrate(self.plan)
        self.bound = guard.bind_plan(self.root, self.plan)
        self.plan_path = self.base / "bound.json"
        guard.write_json(self.bound, self.plan_path)
        self.records = [self.full_record(fixtures.published())]
        self.latest_id = 1
        self.mutations = []
        self.fail_list = False
        self.fail_operation = None
        self.fail_push_after_success = False
        self.fail_create_after_success = False
        self.inject_tag_collision = False
        self.fail_tag_readback = False
        self.tag_was_pushed = False
        self.after_git = None
        self.adapter_state = self.base / "gate-state.json"
        self.adapter_state.write_text("{}")
        self.verifier = self.base / "live-fixture-verifier"
        self.verifier.write_text(
            "#!/usr/bin/env python3\n"
            "import datetime as dt, json, sys\n"
            "from pathlib import Path\n"
            f"state = json.loads(Path({str(self.adapter_state)!r}).read_text())\n"
            "request = json.load(sys.stdin)\n"
            "now = dt.datetime.now(dt.timezone.utc)\n"
            "proof = dict(request, gate_key='release:' + request['repository'],\n"
            " service='https://locks.example.com', held=True, exclusive=True,\n"
            " all_writers_gated=True, target_fenced=True, no_unresolved_publication=True,\n"
            " evidence={'lease_revision':'1','writer_policy_revision':'2','target_fence_revision':'3'},\n"
            " checked_at=now.isoformat(), expires_at=(now + dt.timedelta(seconds=300)).isoformat())\n"
            "if state.get('deny_phase') == request['phase']: proof['held'] = False\n"
            "proof.update(state.get('override', {}))\n"
            "print(json.dumps(proof))\n"
        )
        self.verifier.chmod(0o700)
        mock = patch.object(pub, "run", side_effect=self.provider)
        mock.start()
        self.addCleanup(mock.stop)

    def full_record(self, record, body="Original feature."):
        return {**record, "name": record["tag_name"][1:], "body": body,
                "html_url": "https://github.com/example/project/releases/tag/" + record["tag_name"]}

    def args(self, plan=True, **updates):
        return argparse.Namespace(repo=self.root, gate_verifier=self.verifier, gate_lease="fixture-lease",
            plan=self.plan_path if plan else None, version=None, changelog=None, latest=None,
            github_host=None, journal=None, **updates)

    def synchronize_records(self):
        self.fixture.github["releases"] = [{k: r[k] for k in pub.RELEASE_FIELDS} for r in self.records]

    def provider(self, cmd, cwd=None, input_text=None):
        if cmd[0] != "gh":
            if self.fail_tag_readback and self.tag_was_pushed and cmd[:3] == ["git", "ls-remote", "--tags"]:
                raise pub.ReleaseError("Fixture tag readback unavailable")
            if self.inject_tag_collision and cmd[:2] == ["git", "push"]:
                self.fixture.git(self.root, "tag", "-a", "concurrent-tag", "HEAD^", "-m", "Concurrent writer")
                self.fixture.git(self.root, "push", "origin", "refs/tags/concurrent-tag:refs/tags/v1.1.0")
            output = self.real_run(cmd, cwd, input_text)
            if cmd[:2] == ["git", "push"]:
                self.tag_was_pushed = True
            if self.fail_push_after_success and cmd[:2] == ["git", "push"]:
                raise pub.ReleaseError("Fixture lost tag-push response")
            if self.after_git:
                self.after_git(cmd)
            return output
        if cmd[1] == "api":
            endpoint = next(arg for arg in cmd if arg.startswith("repos/"))
            if endpoint.endswith("/releases/latest"):
                return json.dumps({"id": self.latest_id})
            if "/releases?" in endpoint:
                if self.fail_list:
                    raise pub.ReleaseError("Fixture transient API read failure")
                return json.dumps([self.records])
            return json.dumps({"full_name": "example/project", "permissions": {"push": True}})
        self.assertEqual(cmd[1], "release")
        operation, tag = cmd[2], cmd[3]
        self.mutations.append(operation)
        self.assertIn("--verify-tag", cmd)
        self.assertEqual(cmd[cmd.index("--repo") + 1], self.repository)
        self.assertIn("--notes-file", cmd)
        notes = Path(cmd[cmd.index("--notes-file") + 1]).read_text()
        title = cmd[cmd.index("--title") + 1]
        if self.fail_operation == operation:
            raise pub.ReleaseError("Fixture mutation transport failure")
        previous = next((r for r in self.records if r["tag_name"] == tag), None)
        if operation == "create":
            self.assertIsNone(previous)
            record = fixtures.published(title, max(r["id"] for r in self.records) + 1)
            record["updated_at"] = "2026-10-27T00:00:00Z"
            record = self.full_record(record, notes)
            self.records.append(record)
        else:
            self.assertIsNotNone(previous)
            record = previous
            record.update(name=title, body=notes, updated_at="2026-10-27T00:00:00Z")
        if "--latest=true" in cmd:
            self.latest_id = record["id"]
        elif self.latest_id == record["id"]:
            self.latest_id = next((r["id"] for r in self.records if r["id"] != record["id"]), None)
        self.synchronize_records()
        if self.fail_create_after_success and operation == "create":
            raise pub.ReleaseError("Fixture lost release-create response")
        return record["html_url"] if operation == "create" else ""

    def journal(self):
        files = list((self.root / ".git/publication-intents").glob("*.json"))
        self.assertTrue(files)
        return json.loads(files[-1].read_text())

    def install_remote_tag(self, commit=None, local_message=None):
        git = self.fixture.git
        git(self.root, "tag", "-a", "v1.1.0", commit or "HEAD", "-m", "Remote tag")
        git(self.root, "push", "origin", "refs/tags/v1.1.0")
        remote = pub.local_tag(self.root, "v1.1.0")
        git(self.root, "tag", "-d", "v1.1.0")
        if local_message:
            git(self.root, "tag", "-a", "v1.1.0", "-m", local_message)
        return remote

    def test_guarded_publication_accepts_only_owned_exact_tag_and_release(self):
        result = pub.Publisher(self.args()).publish()
        self.assertEqual(result["version"], "1.1.0")
        self.assertEqual(self.mutations, ["create"])
        self.assertEqual(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0")["commit"], result["commit"])
        record = self.journal()
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["owned_tag"]["commit"], result["commit"])
        self.assertEqual(record["owned_release"]["tag_name"], "v1.1.0")
        self.assertFalse(list((self.root / ".git/publication-intents").glob(".release-notes-*")))
        for file_path in (self.root / ".git/publication-intents").glob("*.json"):
            self.assertEqual(file_path.stat().st_mode & 0o777, 0o600)

    def test_journal_directory_entries_are_durable_before_a_mutation(self):
        phases = []
        actual_sync = pub.sync_directory
        def record_sync(directory):
            actual_sync(directory)
            phases.append(Path(directory))
        with patch.object(pub, "sync_directory", side_effect=record_sync):
            publisher = pub.Publisher(self.args())
            self.addCleanup(publisher.local_gate.close)
            intent_dir = publisher.journal.path.parent
            self.assertEqual(phases[:2], [intent_dir.parent, intent_dir])
            def mutation(cmd, cwd=None, input_text=None):
                journal = json.loads(publisher.journal.path.read_text())
                self.assertEqual(journal["status"], "attempting")
                self.assertEqual(phases[-1], intent_dir)
                return ""
            with patch.object(pub, "run", side_effect=mutation), patch.object(publisher, "checkpoint"):
                publisher.mutate("fixture_write", ["fixture-write"])
            self.assertEqual(phases[-2:], [intent_dir, intent_dir])
            publisher.gate.close()
            publisher.local_gate.close()

    def test_legacy_inference_and_exact_remote_adoption(self):
        expected = self.install_remote_tag()
        result = pub.Publisher(self.args(plan=False)).publish()
        self.assertEqual(result["version"], "1.1.0")
        self.assertEqual(pub.local_tag(self.root, "v1.1.0"), expected)
        self.assertEqual(self.journal()["expected_tag"], expected)
        self.assertEqual(self.mutations, ["create"])

    def test_remote_tag_on_wrong_commit_is_never_adopted(self):
        previous = self.fixture.git(self.root, "rev-parse", "HEAD^")
        expected = self.install_remote_tag(commit=previous)
        with self.assertRaisesRegex(pub.ReleaseError, "different commit"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertIsNone(pub.local_tag(self.root, "v1.1.0"))
        self.assertEqual(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0"), expected)
        self.assertEqual(self.mutations, [])

    def test_equal_commit_but_different_annotated_tag_object_is_rejected(self):
        remote = self.install_remote_tag(local_message="Different local annotation")
        local = pub.local_tag(self.root, "v1.1.0")
        self.assertEqual(remote["commit"], local["commit"])
        self.assertNotEqual(remote["object"], local["object"])
        with self.assertRaisesRegex(pub.ReleaseError, "tag objects differ"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertEqual(pub.local_tag(self.root, "v1.1.0"), local)
        self.assertEqual(self.mutations, [])

    def test_unavailable_read_is_never_treated_as_absent(self):
        self.fail_list = True
        with self.assertRaisesRegex(pub.ReleaseError, "transient API read"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertIsNone(pub.local_tag(self.root, "v1.1.0"))
        self.assertEqual(self.mutations, [])

    def test_edit_failure_never_falls_back_to_create(self):
        self.install_remote_tag()
        self.records.append(self.full_record(fixtures.published("1.1.0", 2), "Old notes"))
        self.synchronize_records()
        self.fail_operation = "edit"
        with self.assertRaises(pub.UnknownMutation):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertEqual(self.mutations, ["edit"])
        self.assertEqual(self.journal()["status"], "unknown")
        self.fail_operation = None
        self.assertEqual(self.journal()["existing_release"]["id"], 2)
        with self.assertRaisesRegex(pub.ReleaseError, "prior publication intent"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertEqual(self.mutations, ["edit"])

    def test_lost_push_response_is_not_retried_and_blocks_new_intent(self):
        self.fail_push_after_success = True
        with self.assertRaises(pub.UnknownMutation):
            pub.Publisher(self.args()).publish()
        self.assertIsNotNone(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0"))
        self.assertEqual(self.journal()["status"], "unknown")
        self.assertEqual(self.mutations, [])
        self.fail_push_after_success = False
        with self.assertRaisesRegex(pub.ReleaseError, "prior publication intent"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertEqual(self.mutations, [])

    def test_lost_create_response_keeps_unknown_result_without_edit_or_retry(self):
        self.fail_create_after_success = True
        with self.assertRaises(pub.UnknownMutation):
            pub.Publisher(self.args()).publish()
        self.assertEqual(self.journal()["status"], "unknown")
        self.assertEqual(self.mutations, ["create"])
        self.assertTrue(any(r["tag_name"] == "v1.1.0" for r in self.records))
        self.fail_create_after_success = False
        with self.assertRaisesRegex(pub.ReleaseError, "prior publication intent"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertEqual(self.mutations, ["create"])

    def test_remote_collision_during_push_never_overwrites_or_creates_release(self):
        self.inject_tag_collision = True
        with self.assertRaises(pub.UnknownMutation):
            pub.Publisher(self.args()).publish()
        actual = pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0")
        self.assertEqual(actual, pub.local_tag(self.root, "concurrent-tag"))
        self.assertNotEqual(actual["commit"], self.bound["publication_baseline"]["target_sha"])
        self.assertEqual(self.mutations, [])
        self.assertEqual(self.journal()["status"], "unknown")

    def test_tag_readback_failure_stops_before_release_and_retains_intent(self):
        self.fail_tag_readback = True
        with self.assertRaisesRegex(pub.ReleaseError, "tag readback unavailable"):
            pub.Publisher(self.args()).publish()
        self.assertEqual(self.mutations, [])
        self.assertEqual(self.journal()["status"], "requires_read_only_reconciliation")
        self.fail_tag_readback = False
        self.assertIsNotNone(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0"))

    def test_missing_or_unverified_shared_gate_blocks_every_mode(self):
        for plan in (False, True):
            args = self.args(plan=plan)
            args.gate_verifier = None
            with self.subTest(plan=plan), self.assertRaisesRegex(pub.ReleaseError, "shared-gate"):
                pub.Publisher(args).publish()
        self.assertIsNone(pub.local_tag(self.root, "v1.1.0"))

    def test_default_same_host_gate_requires_no_external_adapter(self):
        args = self.args()
        args.gate_verifier, args.gate_lease = None, None
        result = pub.Publisher(args).publish()
        self.assertEqual(result["serialization"], "same_host_common_git_lock")
        self.assertFalse(result["cross_host_exclusion"])
        self.assertEqual(self.mutations, ["create"])

    def test_wrong_binding_expired_local_or_unfenced_proof_stops_before_tag(self):
        cases = [{"repository": "github.com/other/project"}, {"target_sha": "a" * 40},
                 {"gate_key": "release:version-1.1.0"}, {"exclusive": False},
                 {"target_fenced": False}, {"all_writers_gated": False},
                 {"no_unresolved_publication": False}, {"service": "file:///tmp/local-lock"},
                 {"checked_at": "2020-01-01T00:00:00+00:00"},
                 {"expires_at": "2020-01-01T00:00:00+00:00"}]
        for override in cases:
            with self.subTest(override=override):
                self.adapter_state.write_text(json.dumps({"override": override}))
                with self.assertRaises(pub.ReleaseError):
                    pub.Publisher(self.args()).publish()
                self.assertIsNone(pub.local_tag(self.root, "v1.1.0"))
                self.assertEqual(self.mutations, [])

    def test_gate_revocation_after_tag_push_prevents_release_creation(self):
        self.adapter_state.write_text(json.dumps({"deny_phase": "before_create_release"}))
        with self.assertRaisesRegex(pub.ReleaseError, "held"):
            pub.Publisher(self.args()).publish()
        self.assertIsNotNone(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0"))
        self.assertEqual(self.mutations, [])
        self.assertEqual(self.journal()["status"], "requires_read_only_reconciliation")

    def test_release_advances_between_tag_creation_and_push(self):
        def after(cmd):
            if cmd[:3] == ["git", "tag", "-a"]:
                self.records.append(self.full_record(fixtures.published("2.0.0", 3)))
                self.synchronize_records()
        self.after_git = after
        with self.assertRaisesRegex(pub.ReleaseError, "release state changed"):
            pub.Publisher(self.args()).publish()
        self.assertIsNone(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0"))
        self.assertEqual(self.mutations, [])

    def test_target_advances_between_tag_creation_and_push(self):
        def after(cmd):
            if cmd[:3] == ["git", "tag", "-a"]:
                tree = self.fixture.git(self.root, "rev-parse", "HEAD^{tree}")
                commit = self.fixture.git(self.root, "commit-tree", tree, "-p", "HEAD", "-m", "Concurrent target")
                self.fixture.git(self.root, "push", "origin", commit + ":refs/heads/main")
        self.after_git = after
        with self.assertRaisesRegex(pub.ReleaseError, "Authoritative target changed"):
            pub.Publisher(self.args()).publish()
        self.assertIsNone(pub.tag_from_refs(pub.remote_tags(self.root, "origin"), "v1.1.0"))
        self.assertEqual(self.mutations, [])

    def test_guarded_inputs_are_exact_and_prepared_plan_cannot_publish(self):
        args = self.args()
        args.version = "1.2.0"
        with self.assertRaisesRegex(pub.ReleaseError, "version differs"):
            pub.Publisher(args)
        args.version = None
        args.changelog = "other.md"
        with self.assertRaisesRegex(pub.ReleaseError, "Changelog differs"):
            pub.Publisher(args)
        guard.write_json(self.plan, self.base / "prepared.json")
        args.changelog, args.plan = None, self.base / "prepared.json"
        with self.assertRaisesRegex(pub.ReleaseError, "Bind the prepared plan"):
            pub.Publisher(args)
        self.assertEqual(self.mutations, [])

    def test_historical_default_is_non_latest_and_explicit_latest_is_honored(self):
        self.records.append(self.full_record(fixtures.published("2.0.0", 3)))
        self.latest_id = 3
        result = pub.Publisher(self.args(plan=False)).publish()
        self.assertFalse(result["latest"])
        self.assertEqual(self.latest_id, 3)
        args = self.args(plan=False)
        args.latest = True
        result = pub.Publisher(args).publish()
        self.assertTrue(result["latest"])

    def test_missing_history_blocks_before_tag_creation(self):
        self.records.clear()
        self.fixture.github["releases"] = []
        with self.assertRaisesRegex(pub.ReleaseError, "Missing intermediate.*1.0.0"):
            pub.Publisher(self.args(plan=False)).publish()
        self.assertIsNone(pub.local_tag(self.root, "v1.1.0"))
        self.assertEqual(self.mutations, [])


class ConcurrentProcessTests(unittest.TestCase):
    def test_competing_worktree_publishers_share_default_gate_and_reject_stale_plan(self):
        fixture = fixtures.GitFixture()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.reader.stop()
        root, base = fixture.root, fixture.base
        binary_dir = base / "bin"
        binary_dir.mkdir()
        state = base / "github.json"
        first = {**fixtures.published(), "name": "1.0.0", "body": "Original feature.",
                 "html_url": "https://github.test/example/project/releases/tag/v1.0.0"}
        state.write_text(json.dumps({"records": [first], "latest": 1}))
        marker, log = base / "creating-release", base / "mutations.jsonl"
        ssh = binary_dir / "fixture-ssh"
        ssh.write_text(
            "#!/usr/bin/env python3\nimport os, subprocess, sys\n"
            "operation = sys.argv[-1].split()[0]\n"
            "assert operation in ('git-upload-pack', 'git-receive-pack')\n"
            "raise SystemExit(subprocess.call([operation, os.environ['FIXTURE_BARE']]))\n"
        )
        ssh.chmod(0o700)
        gh = binary_dir / "gh"
        gh.write_text('''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
args = sys.argv[1:]
state = Path(os.environ['FIXTURE_GITHUB'])
data = json.loads(state.read_text())
if args[0] == 'api':
    endpoint = next(value for value in args if value.startswith('repos/'))
    if endpoint.endswith('/releases/latest'):
        output = {'id': data['latest']}
    elif '/releases?' in endpoint:
        output = [data['records']]
    else:
        output = {'full_name':'example/project','permissions':{'push':True}}
else:
    assert args[:2] == ['release', 'create'], args
    assert '--verify-tag' in args
    Path(os.environ['FIXTURE_MARKER']).touch()
    time.sleep(0.8)
    tag = args[2]
    notes = Path(args[args.index('--notes-file') + 1]).read_text()
    record = {'id': 2, 'tag_name':tag, 'draft':False, 'prerelease':False,
              'published_at':'2026-10-27T00:00:00Z', 'updated_at':'2026-10-27T00:00:00Z',
              'name':tag[1:], 'body':notes,
              'html_url':'https://github.test/example/project/releases/tag/' + tag}
    data['records'].append(record)
    data['latest'] = 2
    temporary = state.with_suffix('.new')
    temporary.write_text(json.dumps(data))
    temporary.replace(state)
    with Path(os.environ['FIXTURE_LOG']).open('a') as stream:
        stream.write(json.dumps(args[:3]) + '\\n')
    output = record['html_url']
print(json.dumps(output) if not isinstance(output, str) else output)
''')
        gh.chmod(0o700)
        environment = {**os.environ, "PATH": str(binary_dir) + os.pathsep + os.environ["PATH"],
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": shlex.quote(str(ssh)),
            "FIXTURE_BARE": str(fixture.bare), "FIXTURE_GITHUB": str(state),
            "FIXTURE_MARKER": str(marker), "FIXTURE_LOG": str(log)}
        with patch.dict(os.environ, environment):
            fixture.git(root, "remote", "set-url", "origin", "git@github.test:example/project.git")
            fixture.config["github_host"] = "github.test"
            plan = fixture.plan()
            fixture.integrate(plan)
            bound = guard.bind_plan(root, plan)
            plan_path = base / "publish.json"
            guard.write_json(bound, plan_path)
            second = base / "second-worktree"
            fixture.git(root, "worktree", "add", "--no-track", "-b", "feat/second-publisher", str(second), "HEAD")
            fixture.git(second, "branch", "--set-upstream-to", "origin/main")
            command = [sys.executable, str(SKILLS / 'create-github-release/scripts/create_release.py'),
                       "--plan", str(plan_path), "--github-host", "github.test", "--lock-timeout", "30"]
            one = subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.addCleanup(lambda: one.kill() if one.poll() is None else None)
            deadline = time.monotonic() + 15
            while not marker.exists() and one.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(marker.exists(), one.communicate(timeout=5) if one.poll() is not None else "No create marker")
            two = subprocess.Popen(command, cwd=second, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.addCleanup(lambda: two.kill() if two.poll() is None else None)
            time.sleep(0.1)
            self.assertIsNone(two.poll(), "Competing worktree escaped the held default lock")
            output_one, error_one = one.communicate(timeout=30)
            output_two, error_two = two.communicate(timeout=30)
            self.assertEqual(one.returncode, 0, error_one)
            self.assertNotEqual(two.returncode, 0, output_two)
            self.assertIn("existing release", error_two)
            result = json.loads(output_one)
            self.assertEqual(result["serialization"], "same_host_common_git_lock")
            self.assertFalse(result["cross_host_exclusion"])
            self.assertEqual(len(log.read_text().splitlines()), 1)
            remote_tag = pub.tag_from_refs(pub.remote_tags(root, "origin"), "v1.1.0")
            self.assertEqual(remote_tag["commit"], result["commit"])


if __name__ == "__main__":
    unittest.main()
