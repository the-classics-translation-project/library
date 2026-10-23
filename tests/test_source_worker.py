"""The local worker is exercised without Codex, GitHub or a live scheduler."""
import fcntl
import json
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import ctp
import source_worker as worker
import site_builder
from legacy_v1 import ProjectError, object_hash, write_json
from source_import import apply, prepare


class SourceWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.state = self.base / 'state'
        self.remote = self.base / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', '--initial-branch=main', str(self.root)], check=True)
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('remote', 'add', 'origin', str(self.remote))
        shutil.copy(ctp.ROOT / 'project.json', self.root / 'project.json')
        write_json(self.root / 'catalog.json', {'schema_version': 1, 'revisions': []})
        write_json(self.root / 'queue.json', {'schema_version': 1, 'works': [
            {'id': 'gutenberg-999', 'source': {'type': 'gutenberg', 'id': 999},
             'targets': ['en', 'ja'], 'requests': []}]})
        (self.root / 'books/gutenberg-999').mkdir(parents=True)
        raw = self.base / 'received.txt'
        raw.write_text('A Test\n\nFirst paragraph.\n\n', encoding='utf-8')
        prepare(raw, self.root / 'books/gutenberg-999/acquisition')
        write_json(self.root / 'books/gutenberg-999/rights.json',
                   {'ebook_id': 999, 'status': 'acquired', 'eligible': True, 'reasons': []})
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.git('push', '-q', '-u', 'origin', 'main')
        self.saved_rights = {'status': 'acquired', 'eligible': True, 'reasons': []}

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def fake_agent(self, worktree, row, run_dir):
        run_dir.mkdir(parents=True, exist_ok=True)
        wd = worktree / 'books' / row['work']
        blocks = ctp.read_json(wd / 'acquisition/blocks.json')
        plan = {'blocks_sha256': object_hash(blocks),
                'tree': {'label_blocks': ['b000001'], 'text_blocks': ['b000002']}}
        plan_path = run_dir / 'plan.json'
        write_json(plan_path, plan)
        apply(wd, plan_path)
        write_json(wd / 'work.json', {
            'schema_version': 2, 'id': row['work'], 'language': 'en',
            'author': 'A Test Author', 'source_edition': 'Test first edition',
            'source_provenance': 'Synthetic test acquisition',
            'rights_note': 'Synthetic rights fixture', 'status': 'imported',
            'source': {'provider': 'gutenberg', 'ebook_id': 999},
            'structure': 'structure.json'})
        (wd / 'notes.md').write_text('Synthetic source analysis.\n', encoding='utf-8')

    def test_two_targets_select_one_work_and_dry_run_has_no_side_effects(self):
        with patch.object(worker, 'validate_record', return_value=self.saved_rights):
            report = worker.run_once(self.root, self.state, dry_run=True)
        self.assertEqual([r['work'] for r in report['pending']], ['gutenberg-999'])
        self.assertEqual(report['selected'][0]['stage'], 'structure')
        self.assertFalse(report['model_called'])
        self.assertFalse(self.state.exists())

    def test_one_work_run_is_validated_committed_and_not_repeated(self):
        with patch.object(worker, 'REMOTE', str(self.remote)), \
             patch.object(worker, 'validate_record', return_value=self.saved_rights), \
             patch('acquire_queue.validate_record', return_value=self.saved_rights), \
             patch.object(worker, 'cli_flags'):
            result = worker.run_once(self.root, self.state, executor=self.fake_agent,
                                     publish=False)
            self.assertEqual(result['work'], 'gutenberg-999')
            self.assertFalse(result['published'])
            self.assertTrue((self.state / 'ledger.json').exists())
            pending = worker.selected(self.root, self.state)
            self.assertEqual(pending['pending'], [])
            again = worker.run_once(self.root, self.state, executor=lambda *_: self.fail('model called'),
                                    publish=False)
            self.assertFalse(again['model_called'])

    def test_lock_contention_uses_no_model(self):
        self.state.mkdir()
        with (self.state / 'worker.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = worker.run_once(self.root, self.state,
                                     executor=lambda *_: self.fail('model called'))
        self.assertTrue(result['locked'])
        self.assertFalse(result['model_called'])

    def test_acquisition_change_is_rejected(self):
        wd = self.root / 'books/gutenberg-999'
        (wd / 'acquisition/acquired.txt').write_text('altered', encoding='utf-8')
        with patch.object(worker, 'validate_record', return_value=self.saved_rights):
            row = {'work': 'gutenberg-999', 'ebook_id': 999, 'stage': 'structure'}
            with self.assertRaises(ProjectError):
                worker.verify_changes(self.root, row)

    def test_agent_commit_before_validation_is_rejected(self):
        def premature_commit(worktree, row, run_dir):
            self.fake_agent(worktree, row, run_dir)
            subprocess.run(['git', 'add', '.'], cwd=worktree, check=True)
            subprocess.run(['git', 'commit', '-qm', 'agent tried to commit'],
                           cwd=worktree, check=True)
        with patch.object(worker, 'REMOTE', str(self.remote)), \
             patch.object(worker, 'validate_record', return_value=self.saved_rights), \
             patch.object(worker, 'cli_flags'):
            with self.assertRaises(ProjectError):
                worker.run_once(self.root, self.state, executor=premature_commit,
                                publish=False)
            ledger = worker.read_ledger(self.state)
            self.assertEqual(ledger['works']['gutenberg-999']['result'], 'held')

    def test_unchanged_hold_cools_down_until_fingerprint_changes(self):
        held = {'status': 'held', 'eligible': False,
                'reasons': [{'country': 'JP', 'code': 'source_publication_missing',
                             'detail': 'No publication year'}]}
        with patch.object(worker, 'validate_record', return_value=held):
            first = worker.selected(self.root, self.state)['pending'][0]
            self.assertEqual(first['stage'], 'research')
            worker.write_outcome(self.state, first, 'held', 'test')
            self.assertEqual(worker.selected(self.root, self.state)['pending'], [])
            (self.root / 'books/gutenberg-999/notes.md').write_text('New evidence to inspect.\n')
            self.assertEqual(len(worker.selected(self.root, self.state)['pending']), 1)

    def test_existing_pinned_evidence_needs_owner_review(self):
        held = {'status': 'held', 'eligible': False,
                'admission_evidence': {'file': 'admission-evidence.json', 'sha256': 'old'},
                'reasons': [{'country': 'JP', 'code': 'source_publication_missing',
                             'detail': 'No publication year'}]}
        with patch.object(worker, 'validate_record', return_value=held):
            report = worker.selected(self.root, self.state)
        self.assertEqual(report['pending'], [])
        self.assertEqual(report['deferred'][0]['stage'], 'unsupported-hold')

    def test_published_commit_needs_successful_ci_and_pages(self):
        row = {'work': 'gutenberg-999', 'fingerprint': 'fixture'}
        worker.write_outcome(self.state, row, 'published-pending', 'attempt', commit='abc')
        runs = [
            {'workflowName': 'Validate and build', 'status': 'completed',
             'conclusion': 'success', 'url': 'https://example.invalid/ci',
             'createdAt': '2026-10-18T00:00:00Z'},
            {'workflowName': 'Deploy catalogue and workbench', 'status': 'completed',
             'conclusion': 'success', 'url': 'https://example.invalid/pages',
             'createdAt': '2026-10-18T00:00:00Z'},
        ]
        with patch.object(worker, 'command', return_value=SimpleNamespace(stdout=json.dumps(runs))):
            result = worker.reconcile_published(self.root, self.state)
        self.assertEqual(result[0]['state'], 'complete')
        self.assertEqual(worker.read_ledger(self.state)['works']['gutenberg-999']['result'],
                         'complete')

    def test_admin_exposes_tree_shape_without_full_source_prose(self):
        self.fake_agent(self.root, {'work': 'gutenberg-999'}, self.base / 'fake-run')
        (self.root / 'site').mkdir()
        shutil.copy(ctp.ROOT / 'site/admin.js', self.root / 'site/admin.js')
        shutil.copy(ctp.ROOT / 'site/translation-admin.js', self.root / 'site/translation-admin.js')
        html = site_builder.admin(self.root, ctp.read_json(self.root / 'project.json'), '')
        payload = re.search(r'<script id="admin-data" type="application/json">(.*?)</script>',
                            html, re.S).group(1)
        sources = json.loads(payload)['sources']
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]['tree']['label'], 'A Test')
        self.assertTrue(sources[0]['tree']['has_text'])
        self.assertNotIn('First paragraph.', html)
        self.assertIn('source-trees', html)

    def test_launch_agent_template_is_inert_until_install(self):
        script = ctp.ROOT / 'tools/install-source-launch-agent.sh'
        installed = Path.home() / 'Library/LaunchAgents/org.classics-translation-project.source-worker.plist'
        before = installed.read_bytes() if installed.exists() else None
        raw = subprocess.run([str(script), 'print-plist'], check=True,
                             stdout=subprocess.PIPE).stdout
        config = plistlib.loads(raw)
        self.assertEqual(config['StartInterval'], 1800)
        self.assertTrue(config['RunAtLoad'])
        self.assertEqual(config['ProgramArguments'][1], 'run-once')
        self.assertEqual(installed.read_bytes() if installed.exists() else None, before)


if __name__ == '__main__':
    unittest.main()
