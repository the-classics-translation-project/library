"""Offline Git publication tests; no network, browser, model or relay submission."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ctp as c
import draft_distribution as d
import relay_coordinator as coordinator
from tests import test_relay_coordinator as coordinator_fixture
from tests import test_translation_relay as relay_fixture


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


class DraftDistributionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = coordinator_fixture.CoordinatorTests('test_status_is_read_only_and_idle_reconcile_calls_no_model')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        shutil.copy2(c.ROOT/'draft-distribution.json', self.root/'draft-distribution.json')
        self.fixture.init_git()

    def imported(self, **kwargs):
        row = self.fixture.prepare(**kwargs)
        self.fixture.submit(row)
        self.fixture.response(row)
        coordinator.reconcile(self.root, True)
        self.assertEqual(coordinator.load(self.root, row['id'])['state'], 'imported')
        return row

    def test_noop_and_review_hold_do_not_commit(self):
        original = git(self.root, 'rev-parse', 'HEAD')
        self.assertEqual(d.publish_ready(self.root, False)['published'], [])
        row = self.fixture.prepare()
        self.fixture.submit(row)
        self.fixture.register(row, 'needs_review')
        coordinator.reconcile(self.root, True)
        self.assertEqual(d.publish_ready(self.root, False)['published'], [])
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), original)

    def test_disabled_policy_stops_publication(self):
        row = self.imported(guide_issue=12)
        path = self.root/'draft-distribution.json'
        value = json.loads(path.read_text())
        value['enabled'] = False
        path.write_text(json.dumps(value))
        self.assertTrue(d.publish_ready(self.root, False)['disabled'])
        self.assertFalse(coordinator.load(self.root, row['id']).get('commit'))

    def test_backfill_two_imported_guides_without_sweeping_other_files(self):
        first = self.imported(guide_issue=12)
        second = self.imported(task_type='work_analysis', work='gutenberg-41445')
        (self.root/'unrelated-private.txt').write_text('Do not publish')
        result = d.publish_ready(self.root, False)
        self.assertEqual(set(result['published']), {first['id'], second['id']})
        self.assertFalse(result['pushed'])
        changed = set(git(self.root, 'diff-tree', '--no-commit-id', '--name-only',
                          '-r', result['commit']).splitlines())
        expected = set(coordinator.load(self.root, first['id'])['outputs']) | set(
            coordinator.load(self.root, second['id'])['outputs'])
        self.assertEqual(changed, expected)
        self.assertNotIn('catalog.json', changed)
        self.assertTrue((self.root/'unrelated-private.txt').exists())
        self.assertFalse(coordinator.load(self.root, first['id']).get('pushed_at'))
        # A crash before push must not create a second commit on retry.
        again = d.publish_ready(self.root, False)
        self.assertEqual(again['commit'], result['commit'])

    def test_changed_or_missing_output_holds(self):
        row = self.imported(guide_issue=12)
        output = next(iter(coordinator.load(self.root, row['id'])['outputs']))
        (self.root/output).write_text('Altered after import')
        with self.assertRaises(c.ProjectError):
            d.publish_ready(self.root, False)
        (self.root/output).unlink()
        with self.assertRaises(c.ProjectError):
            d.publish_ready(self.root, False)

    def test_failed_push_retries_same_commit_without_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            remote = Path(directory)/'remote.git'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            git(self.root, 'remote', 'add', 'origin', str(remote))
            git(self.root, 'push', '-u', 'origin', 'main')
            row = self.imported(guide_issue=12)
            actual_git = d.git
            failed = [False]

            def checked_git(root, *args, **kwargs):
                if args == ('remote', 'get-url', 'origin'):
                    return 'https://github.com/the-classics-translation-project/library.git'
                if args and args[0] == 'push' and not failed[0]:
                    failed[0] = True
                    raise c.ProjectError('Simulated push interruption')
                return actual_git(root, *args, **kwargs)

            with patch.object(d, 'git', side_effect=checked_git):
                with self.assertRaises(c.ProjectError):
                    d.publish_ready(self.root, True)
                commit = git(self.root, 'rev-parse', 'HEAD')
                self.assertFalse(coordinator.load(self.root, row['id']).get('pushed_at'))
                result = d.publish_ready(self.root, True)
            self.assertEqual(result['commit'], commit)
            self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), commit)
            self.assertEqual(git(remote, 'rev-parse', 'refs/heads/main'), commit)
            self.assertTrue(coordinator.load(self.root, row['id']).get('pushed_at'))
            self.assertEqual(d.publish_ready(self.root, False)['published'], [])


class DirectDraftDistributionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = relay_fixture.RelayTests('test_package_is_local_ordered_and_explicit')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        for name in ('catalog.json', 'guide-requests.json', 'translation-requests.json'):
            shutil.copy2(c.ROOT/name, self.root/name)
        shutil.copy2(c.ROOT/'draft-distribution.json', self.root/'draft-distribution.json')
        for args in [('init', '-b', 'main'), ('config', 'user.name', 'Offline Fixture'),
                     ('config', 'user.email', 'fixture@example.invalid'),
                     ('add', '.'), ('commit', '-m', 'Initial fixture')]:
            subprocess.run(['git', '-C', str(self.root), *args], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with (self.root/'.git/info/exclude').open('a') as out:
            out.write('\n/private/\n')

    def test_direct_import_publication_manifest_and_exact_commit(self):
        package = self.fixture.package()
        self.fixture.accept(package)
        marker = self.root/'private/relay'/package['attempt']/'publication.json'
        record = json.loads(marker.read_text())
        self.assertEqual(record['state'], 'imported')
        self.assertTrue(record['outputs'])
        self.assertTrue(all(path.startswith('books/gutenberg-36/editions/ja/')
                            for path in record['outputs']))
        result = d.publish_ready(self.root, False)
        self.assertEqual(result['published'], [package['attempt']])
        changed = set(git(self.root, 'diff-tree', '--no-commit-id', '--name-only',
                          '-r', result['commit']).splitlines())
        self.assertEqual(changed, set(record['outputs']))
        self.assertNotIn('catalog.json', changed)


if __name__ == '__main__':
    unittest.main()
