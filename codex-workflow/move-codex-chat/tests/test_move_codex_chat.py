import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/move_codex_chat.py'
spec = importlib.util.spec_from_file_location('move', SCRIPT)
move = importlib.util.module_from_spec(spec)
spec.loader.exec_module(move)


class MembershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.cwd = self.home / 'isolated-worker'
        self.cwd.mkdir()
        self.rollout = self.home / 'rollout.jsonl'
        self.rollout.write_text('{"type":"session_meta","payload":{"cwd":"original"}}\n')
        with contextlib.closing(sqlite3.connect(self.home / 'state_5.sqlite')) as db:
            db.execute('create table threads(id text,cwd text,rollout_path text)')
            db.execute('insert into threads values(?,?,?)', ('test', str(self.cwd), str(self.rollout)))
            db.commit()
        self.thread = {'id':'test','kind':'codex','hostId':'local','cwd':str(self.cwd),'projectId':'source'}
        self.projects = {'projects':[{'projectKind':'local','hostId':'local','projectId':'dest',
                                      'label':'destination','path':str(self.home/'other-project')}]}
        (self.home/'other-project').mkdir()
        self.thread_file = self.home / 'thread.json'
        self.projects_file = self.home / 'projects.json'
        self.thread_file.write_text(json.dumps(self.thread))
        self.projects_file.write_text(json.dumps(self.projects))
        self.args = ['--codex-home', str(self.home), '--thread-json', str(self.thread_file)]

    def invoke(self, *extra):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            move.main(self.args + list(extra))
        return json.loads(output.getvalue())

    def test_current_inventory_resolves_project_absent_from_saved_roots(self):
        self.assertEqual(move.destination(self.projects,'destination','local')['projectId'],'dest')
        self.assertFalse((self.home/'.codex-global-state.json').exists())

    def test_incomplete_and_ambiguous_inventory_refused(self):
        for inventory in [{**self.projects,'unavailableHosts':['local']},
                          {'projects':self.projects['projects']*2}, {'projects':[]}]:
            with self.subTest(inventory=inventory), self.assertRaises(ValueError):
                move.destination(inventory,'destination','local')

    def test_apply_refuses_without_mutation(self):
        before = (self.home/'state_5.sqlite').read_bytes(), self.rollout.read_bytes()
        with self.assertRaisesRegex(ValueError,'No private metadata writes'):
            self.invoke('--apply')
        self.assertEqual(before, ((self.home/'state_5.sqlite').read_bytes(), self.rollout.read_bytes()))

    def test_missing_database_never_created(self):
        (self.home/'state_5.sqlite').unlink()
        with self.assertRaisesRegex(ValueError,'database unavailable'):
            move.execution(self.home,self.thread)
        self.assertFalse((self.home/'state_5.sqlite').exists())

    def test_preview_preserves_isolated_cwd(self):
        before = self.rollout.read_bytes()
        result = self.invoke('--projects-json',str(self.projects_file),'--dest-project','dest')
        self.assertEqual(result['execution']['cwd'],str(self.cwd))
        self.assertNotEqual(result['execution']['cwd'],result['destination']['path'])
        self.assertEqual(self.rollout.read_bytes(),before)

    def test_verify_requires_membership_and_unchanged_history(self):
        preview = self.invoke('--projects-json',str(self.projects_file),'--dest-project','dest')
        saved = self.home/'before.json'
        saved.write_text(json.dumps(preview))
        with self.assertRaisesRegex(ValueError,'membership not proven'):
            self.invoke('--before-json',str(saved))
        self.thread['projectId']='dest'
        self.thread_file.write_text(json.dumps(self.thread))
        self.assertEqual(self.invoke('--before-json',str(saved))['status'],'verified')
        self.rollout.write_text('changed history')
        with self.assertRaisesRegex(ValueError,'Execution context changed'):
            self.invoke('--before-json',str(saved))

    def test_conflicting_app_database_cwd_refused(self):
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            move.execution(self.home,{**self.thread,'cwd':str(self.home)})

    def test_unknown_source_membership_refused(self):
        self.thread['projectId']=None
        self.thread_file.write_text(json.dumps(self.thread))
        with self.assertRaisesRegex(ValueError,'Source membership ambiguous'):
            self.invoke('--projects-json',str(self.projects_file),'--dest-project','dest')


if __name__ == '__main__':
    unittest.main()
