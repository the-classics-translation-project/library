"""Offline exact-completion follow-up; no browser, submission or Git push."""
from contextlib import closing
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp as c
import relay_completed as followup
import translation_relay as direct
import tests.test_relay_coordinator as coordinator_fixture


class DirectCompletedTests(unittest.TestCase):
    def setUp(self):
        self.fixture=coordinator_fixture.CoordinatorTests('test_status_is_read_only_and_idle_reconcile_calls_no_model')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root;self.relay=self.fixture.relay
        self.job=direct.package(self.root,'gutenberg-36','ja',['n0005'],
                                '6 Extra High',language='ja')
        self.attempt=self.job['attempt']
        self.folder=self.root/'private/relay'/self.attempt
        self.manifest=c.read_json(self.folder/'job.json')['manifest']

    def authorize(self):
        m=self.manifest
        c.write_json(self.folder/'authorization.json',{
            'attempt':self.attempt,'request_sha256':c.read_json(self.folder/'job.json')['package_sha256'],
            'model_requested':m['model_requested'],'work':m['work'],'target':m['edition'],
            'nodes':list(m['fields']),'context_nodes':m['context_nodes'],
            'authorized_at':'2026-01-01T00:00:00Z','authorization':'Exact synthetic test request'})

    def register(self,**changes):
        record={'input_name':self.attempt+'.zip',
                'sha256':c.read_json(self.folder/'job.json')['package_sha256'],
                'model':self.manifest['model_requested'],
                'output_filename':self.manifest['output_filename'],
                'status':'complete','chat_url':'https://chatgpt.com/c/synthetic-test',
                'review_reason':None}
        record.update(changes)
        with closing(sqlite3.connect(self.relay/'relay.sqlite3')) as db:
            db.execute('INSERT INTO jobs('+','.join(record)+') VALUES('+','.join('?' for _ in record)+')',list(record.values()))
            db.commit()

    def response(self,invalid=False):
        obj={k:self.manifest[k] for k in ('attempt','work','edition','language')}
        obj.update(schema_version=1,status='complete',nodes={
            'n0005':{'label':'Synthetic heading','text':'text/n0005.md'}})
        if invalid:obj['work']='wrong-work'
        path=self.relay/'output'/self.manifest['output_filename']
        with ZipFile(path,'w') as out:
            out.writestr('result.json',json.dumps(obj))
            out.writestr('text/n0005.md','Synthetic translated text.')
            out.writestr('glossary.md','# Synthetic glossary\n')
            out.writestr('notes.md','# Synthetic notes\n')
        return path

    def test_imports_exact_authorized_completed_result_once(self):
        self.authorize();self.register();self.response()
        before=self.relay.joinpath('relay.sqlite3').read_bytes()
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual([item['attempt'] for item in result['imported']],[self.attempt])
        self.assertEqual(result['held'],[])
        self.assertFalse(result['model_called'] or result['relay_submitted'] or result['relay_queue_mutated'])
        self.assertEqual(self.relay.joinpath('relay.sqlite3').read_bytes(),before)
        self.assertTrue((self.folder/'publication.json').is_file())
        self.assertEqual(c.read_json(self.root/'books/gutenberg-36/editions/ja/relay'/self.attempt/'receipt.json')['chat_url'],
                         'https://chatgpt.com/c/synthetic-test')
        run=next((self.root/'books/gutenberg-36/editions/ja/runs').glob('*.json'))
        self.assertEqual(c.read_json(run)['model_label'],'unknown')
        second=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(second['imported'],[])
        self.assertEqual(second['existing'],[self.attempt])
        output=io.StringIO()
        with (patch.object(c,'ROOT',self.root),
              patch.object(sys,'argv',['ctp','relay-direct-reconcile','--relay',str(self.relay)]),
              contextlib.redirect_stdout(output)):
            self.assertEqual(c.main(),0)
        self.assertEqual(json.loads(output.getvalue())['imported'],[])
        c.validate_project(self.root)

    def test_missing_authorization_and_mismatch_hold_without_import(self):
        self.register();self.response()
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(result['imported'],[])
        self.assertIn('authorization',result['held'][0]['reason'])
        self.authorize()
        auth=c.read_json(self.folder/'authorization.json');auth['request_sha256']='0'*64
        c.write_json(self.folder/'authorization.json',auth)
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertIn('authorization',result['held'][0]['reason'])
        self.assertFalse((self.root/'books/gutenberg-36/editions/ja/edition.json').exists())

    def test_prepared_unsubmitted_package_is_pending_without_authorization(self):
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(result['pending'],[self.attempt])
        self.assertEqual(result['held'],[])

    def test_missing_result_can_arrive_later_without_resubmission(self):
        self.authorize();self.register()
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertIn('missing',result['held'][0]['reason'])
        self.response()
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(len(result['imported']),1)

    def test_invalid_result_is_captured_and_stays_unpublished(self):
        self.authorize();self.register();self.response(invalid=True)
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(result['imported'],[])
        self.assertEqual(len(result['held']),1)
        self.assertTrue((self.folder/'response.zip').is_file())
        self.assertFalse((self.folder/'publication.json').exists())

    def test_relay_hash_mismatch_and_pending_are_safe(self):
        self.authorize();self.register(status='submitted',sha256='0'*64);self.response()
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertIn('differs',result['held'][0]['reason'])
        self.assertFalse((self.folder/'publication.json').exists())

    def test_submitted_job_waits_and_changed_captured_result_stops(self):
        self.authorize();self.register(status='submitted');self.response()
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(result['pending'],[self.attempt])
        self.assertFalse((self.folder/'response.zip').exists())
        with closing(sqlite3.connect(self.relay/'relay.sqlite3')) as db:
            db.execute("UPDATE jobs SET status='complete' WHERE input_name=?",(self.attempt+'.zip',))
            db.commit()
        captured=self.folder/'response.zip';captured.write_bytes(b'older result')
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertIn('changed after private capture',result['held'][0]['reason'])
        self.assertFalse((self.folder/'publication.json').exists())

    def test_relay_review_is_reported_without_import(self):
        self.authorize();self.register(status='needs_review',review_reason='Download uncertain')
        result=followup.import_direct_completed(self.root,self.relay)
        self.assertEqual(result['imported'],[])
        self.assertEqual(result['held'][0]['reason'],'Download uncertain')


if __name__=='__main__':unittest.main()
