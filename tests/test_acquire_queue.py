"""Queue downloads are isolated, resumable, and never approve literary releases."""
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from legacy_v1 import read_json, write_json, ProjectError
from source_import import prepare
from acquire_queue import acquire_queued, register_acquisitions
from intake import queue_status


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.output = self.root/'build/downloads'
        write_json(self.root/'project.json', {'repository': 'owner/library', 'targets': [{'id': 'ja'}]})
        write_json(self.root/'queue.json', {'schema_version': 1, 'works': [
            {'id': f'gutenberg-{i}', 'source': {'type': 'gutenberg', 'id': i}, 'targets': ['ja'], 'requests': []}
            for i in (36, 41445)]})

    def fake_fetch(self, output, eid):
        raw = output/f'{eid}.txt'
        raw.write_bytes(b'PROJECT GUTENBERG\r\n\r\nTest source\r\n')
        dest = output/'books'/f'gutenberg-{eid}'/'acquisition'
        blocks = prepare(raw, dest)
        raw.unlink()
        write_json(dest/'provenance.json', {'schema_version': 1, 'provider': 'gutenberg', 'ebook_id': eid,
            'raw_sha256': blocks['raw_sha256'], 'source_edition_verified': False, 'rights_checked': False})

    def test_download_register_and_rerun(self):
        with patch('acquire_queue.fetch_gutenberg', side_effect=self.fake_fetch) as fetch:
            report = acquire_queued(self.root, self.output)
            self.assertEqual(len(report['acquired']), 2)
            self.assertFalse((self.root/'books').exists())
            register_acquisitions(self.root, self.output, 123, 456)
            receipt = read_json(self.root/'books/gutenberg-36/acquisition-receipt.json')
            self.assertFalse(receipt['rights_checked'])
            self.assertFalse((self.root/'books/gutenberg-36/work.json').exists())
            self.assertIn('verification needed', queue_status(self.root)[0]['stage'])
            again = acquire_queued(self.root, self.root/'build/again')
            self.assertEqual(len(again['skipped']), 2)
            self.assertEqual(fetch.call_count, 2)

    def test_one_failure_does_not_lose_other_downloads(self):
        def fetch(output, eid):
            if eid == 36: raise OSError('provider unavailable')
            return self.fake_fetch(output, eid)
        with patch('acquire_queue.fetch_gutenberg', side_effect=fetch):
            report = acquire_queued(self.root, self.output)
        self.assertEqual(report['acquired'], ['gutenberg-41445'])
        self.assertEqual(report['failed'][0]['work'], 'gutenberg-36')
        register_acquisitions(self.root, self.output, 123, 456)
        self.assertFalse((self.root/'books/gutenberg-36/acquisition-receipt.json').exists())

    def test_corrupt_package_cannot_be_registered(self):
        with patch('acquire_queue.fetch_gutenberg', side_effect=self.fake_fetch):
            acquire_queued(self.root, self.output)
        (self.output/'books/gutenberg-36/acquisition/acquired.txt').write_text('changed')
        with self.assertRaises(ProjectError): register_acquisitions(self.root, self.output, 123, 456)
        self.assertFalse((self.root/'books').exists())

    def test_expired_receipt_downloads_again(self):
        with patch('acquire_queue.fetch_gutenberg', side_effect=self.fake_fetch) as fetch:
            acquire_queued(self.root, self.output)
            register_acquisitions(self.root, self.output, 123, 456)
            path = self.root/'books/gutenberg-36/acquisition-receipt.json'
            receipt = read_json(path)
            receipt['retained_until'] = '2000-01-01T00:00:00+00:00'
            write_json(path, receipt)
            again = acquire_queued(self.root, self.root/'build/again')
            self.assertEqual(again['acquired'], ['gutenberg-36'])
            self.assertEqual(fetch.call_count, 3)

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir(parents=True)
        with self.assertRaises(ProjectError): acquire_queued(self.root, self.output)

    def test_existing_local_bytes_are_preserved(self):
        self.fake_fetch(self.root, 36)
        with patch('acquire_queue.fetch_gutenberg', side_effect=self.fake_fetch) as fetch:
            report = acquire_queued(self.root, self.output)
        self.assertIn('gutenberg-36', report['skipped'])
        self.assertEqual(fetch.call_count, 1)
