"""Coordinator tests with a synthetic transport ledger; no browser or model use."""
from pathlib import Path
from contextlib import closing
import fcntl
import json
import copy
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp as c
import relay_coordinator as r
from translation_jobs import zip_files


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'project';self.root.mkdir()
        for name in ('books','prompts'):
            shutil.copytree(c.ROOT/name,self.root/name)
        # Copy admitted source only, independent of real local result imports.
        for work in (self.root/'books').iterdir():
            if work.is_dir():
                for name in ('editions','reference'):
                    shutil.rmtree(work/name,ignore_errors=True)
        (self.root/'docs').mkdir()
        shutil.copy2(c.ROOT/'docs/editorial-policy.md',self.root/'docs/editorial-policy.md')
        for name in ('project.json','queue.json','guide-requests.json','translation-requests.json','catalog.json'):
            shutil.copy2(c.ROOT/name,self.root/name)
        shutil.copy2(c.ROOT/'model-submission-policy.json',
                     self.root/'model-submission-policy.json')
        self.relay=Path(self.temp.name)/'relay';(self.relay/'input').mkdir(parents=True);(self.relay/'output').mkdir()
        with closing(sqlite3.connect(self.relay/'relay.sqlite3')) as db:
            db.execute('CREATE TABLE jobs(id INTEGER PRIMARY KEY,input_name TEXT UNIQUE,sha256 TEXT,model TEXT,output_filename TEXT,status TEXT,chat_url TEXT,review_reason TEXT)')
            db.commit()

    def prepare(self,**kwargs):
        return r.prepare(self.root,self.relay,**(kwargs or {'guide_issue':12}))

    def submit(self,row):return r.submit(self.root,row['id'],'Explicit test authorization; synthetic result only')

    def register(self,row,state='submitted',**overrides):
        record={'input_name':row['input_name'],'sha256':row['request_sha256'],
                'model':row['model_requested'],'output_filename':row['output_filename'],
                'status':state,'chat_url':'https://chatgpt.com/c/synthetic-test','review_reason':None}
        record.update(overrides)
        with closing(sqlite3.connect(self.relay/'relay.sqlite3')) as db:
            db.execute('INSERT INTO jobs('+','.join(record)+') VALUES('+','.join('?' for _ in record)+') '
                       'ON CONFLICT(input_name) DO UPDATE SET '+
                       ','.join(name+'=excluded.'+name for name in record if name!='input_name'),
                       list(record.values()))
            db.commit()

    def response(self,row,edit=None):
        if row['adapter']=='independent_guide':
            obj={'schema_version':1,'task_type':row['task_type'],'work':row['work'],'target':row['target'],
                 'job_sha256':row['job_sha256'],'status':'complete','model_label':'unknown','guide_file':'guide.md'}
            if edit:edit(obj)
            files={'result.json':obj,'guide.md':'# Synthetic reference\n\nOffline fixture; no model generation.'}
        elif row['adapter']=='legacy_guide':
            obj={'schema_version':1,'kind':'guide','issue':row['issue'],'work':row['work'],'target':row['target'],
                 'job_sha256':row['job_sha256'],'model_label':'unknown',
                 'work_guide':'# Synthetic work reference\n\nOffline fixture only.',
                 'target_guide':'# Synthetic target reference\n\nOffline fixture only.'}
            if edit:edit(obj)
            files={'response.json':obj}
        else:
            with ZipFile(r.request_path(self.root,row)) as z:m=json.loads(z.read('input/manifest.json'))
            obj={'schema_version':1,'kind':'translation','issue':row['issue'],'job_sha256':row['job_sha256'],
                 'model_label':'unknown','translations':{nid:{f:'Synthetic fixture prose.' for f in fields} for nid,fields in m['requested_fields'].items()}}
            if edit:edit(obj)
            files={'response.json':obj}
        out=self.relay/'output'/row['output_filename'];zip_files(out,files);self.register(row,'complete');return out

    def latest(self,row):return r.load(self.root,row['id'])

    def test_status_is_read_only_and_idle_reconcile_calls_no_model(self):
        before=self.relay.joinpath('relay.sqlite3').read_bytes()
        result=r.status(self.root)
        self.assertFalse((self.root/'private').exists())
        self.assertFalse(result['model_invoked_directly'])
        result=r.reconcile(self.root,True)
        self.assertEqual(result['attempts'],[])
        self.assertEqual((self.relay/'relay.sqlite3').read_bytes(),before)
        self.assertEqual(list((self.relay/'input').iterdir()),[])

    def test_dispatch_prepares_but_requires_committed_bounded_policy_to_submit(self):
        from relay_dispatch import dispatch
        first=dispatch(self.root,self.relay)
        self.assertFalse(first['policy_enabled'])
        self.assertFalse(first['submitted'])
        self.assertFalse(list((self.relay/'input').iterdir()))
        policy=c.read_json(self.root/'model-submission-policy.json')
        policy.pop('requires_import',None)
        policy.update(enabled=True,authorized_by='hiroshi-manabe',
                      authorization_note='Fixture authorization for one work analysis',
                      works=['gutenberg-41445'],targets=['en'],
                      task_types=['work_analysis'],max_submissions_total=1,
                      max_submissions_per_run=1,max_in_flight=1)
        c.write_json(self.root/'model-submission-policy.json',policy)
        with self.assertRaisesRegex(c.ProjectError,'clean, current origin/main'):
            dispatch(self.root,self.relay)
        self.assertFalse(list((self.relay/'input').iterdir()))
        subprocess.run(['git','init','-b','main',str(self.root)],check=True,
                       capture_output=True)
        shutil.copy2(c.ROOT/'.gitignore',self.root/'.gitignore')
        subprocess.run(['git','-C',str(self.root),'add','-A'],
                       check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture',
                        '-c','user.email=fixture@example.test','commit','-m','Authorize fixture'],
                       check=True,capture_output=True)
        bare=Path(self.temp.name)/'origin.git'
        subprocess.run(['git','init','--bare',str(bare)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'remote','add','origin',str(bare)],
                       check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'push','-u','origin','main'],
                       check=True,capture_output=True)
        second=dispatch(self.root,self.relay)
        self.assertEqual(len(second['submitted']),1)
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)
        submitted=r.load(self.root,second['submitted'][0]['attempt'])
        self.assertEqual(submitted['authorization']['policy_id'],policy['policy_id'])
        again=dispatch(self.root,self.relay)
        self.assertEqual(again['submitted'],[])
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)

    def test_bounded_dispatch_waits_for_exact_unified_pilot_import(self):
        from relay_dispatch import dispatch,import_prerequisite_met
        pilot=self.prepare(translation_issue=30)
        gate={key:pilot[source] for key,source in (
            ('attempt','id'),('issue','issue'),('job_sha256','job_sha256'),
            ('request_sha256','request_sha256'),('output_filename','output_filename'))}
        policy=c.read_json(self.root/'model-submission-policy.json')
        policy.update(enabled=True,authorized_by='hiroshi-manabe',
                      authorization_note='Synthetic standing approval',
                      works=['gutenberg-36'],targets=['ja'],task_types=['translation'],
                      max_submissions_total=1,max_submissions_per_run=1,max_in_flight=1,
                      requires_import=gate)
        queue=c.read_json(self.root/'translation-requests.json')
        other=copy.deepcopy(next(x for x in queue['requests'] if x['issue']==30))
        other['issue']=31;queue['requests'].append(other)
        c.write_json(self.root/'translation-requests.json',queue)
        with patch('relay_dispatch.policy',return_value=policy):
            blocked=dispatch(self.root,self.relay)
        self.assertEqual(blocked['activation_blocked'],
                         'Exact imported unified translation pilot is not verified')
        self.assertFalse(blocked['submitted'])
        self.assertFalse(list((self.relay/'input').iterdir()))
        self.assertFalse(import_prerequisite_met(self.root,gate))

        with ZipFile(r.request_path(self.root,pilot)) as z:
            manifest=json.loads(z.read('input/manifest.json'))
        nodes={};files={}
        for nid,fields in manifest['requested_fields'].items():
            nodes[nid]={}
            for field in fields:
                name='text/'+nid+('.label.md' if field=='label' else '.md')
                nodes[nid][field]=name
                files[name]='Synthetic fixture label' if field=='label' else 'Synthetic fixture prose.\n'
        files['result.json']={
            'schema_version':2,'kind':'translation','adapter':'issue',
            'request_id':'30','input_sha256':pilot['job_sha256'],
            'status':'complete','model_label':'unknown','nodes':nodes,'auxiliary':{}}
        response=r.archive(self.root,pilot)/'response.zip'
        zip_files(response,files)
        receipt=self.root/'translation-results/issue-30.json'
        receipt.parent.mkdir(parents=True,exist_ok=True)
        c.write_json(receipt,{'schema_version':1,'issue':30,
            'job_sha256':pilot['job_sha256'],
            'response_sha256':c.digest(response.read_bytes()),
            'revision':'synthetic-fixture'})
        pilot.update(state='imported',authorization={'note':'Synthetic exact approval'},
                     response_sha256=c.digest(response.read_bytes()),
                     outputs={'translation-results/issue-30.json':{
                         'before':None,'after':c.digest(receipt.read_bytes())}})
        r.save(self.root,pilot)
        self.assertTrue(import_prerequisite_met(self.root,gate))
        receipt.write_text(receipt.read_text()+' ',encoding='utf-8')
        self.assertFalse(import_prerequisite_met(self.root,gate))
        c.write_json(receipt,{'schema_version':1,'issue':30,
            'job_sha256':pilot['job_sha256'],
            'response_sha256':pilot['response_sha256'],
            'revision':'synthetic-fixture'})
        pilot['outputs']['translation-results/issue-30.json']['after']=c.digest(receipt.read_bytes())
        r.save(self.root,pilot)
        self.assertTrue(import_prerequisite_met(self.root,gate))
        with patch('relay_dispatch.policy',return_value=policy):
            sent=dispatch(self.root,self.relay)
        self.assertIsNone(sent['activation_blocked'])
        self.assertEqual(len(sent['submitted']),1)
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)
        with patch('relay_dispatch.policy',return_value=policy):
            again=dispatch(self.root,self.relay)
        self.assertEqual(again['submitted'],[])
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)
        sent_row=r.load(self.root,sent['submitted'][0]['attempt'])
        sent_row['state']='needs_review';r.save(self.root,sent_row)
        policy['max_submissions_total']=3
        another=copy.deepcopy(other);another['issue']=32
        queue['requests'].append(another)
        c.write_json(self.root/'translation-requests.json',queue)
        with patch('relay_dispatch.policy',return_value=policy):
            held=dispatch(self.root,self.relay)
        self.assertEqual(held['activation_blocked'],
                         'A policy-authorized attempt needs review')
        self.assertFalse(held['submitted'])
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)

    def test_dispatch_prepares_accepted_translation_issue_without_submission(self):
        from relay_dispatch import dispatch
        from translation_jobs import intake,prompt_catalogue,MARKER_V2
        c.write_json(self.root/'translation-requests.json',
                     {'schema_version':1,'requests':[]})
        prompt=prompt_catalogue(self.root)[0]
        request={'schema_version':2,'work':'gutenberg-36','target':'ja',
                 'nodes':['n0005'],'source_fingerprint':c.source_fingerprint(
                     self.root/'books/gutenberg-36'),
                 'scope':'all','prompt':{'id':prompt['id'],'sha256':prompt['sha256']},
                 'reference':{'mode':'none','revision':None},
                 'instructions':'','materials':[]}
        fence=chr(96)*3
        issue={'number':62,'state':'open','user':{'login':'hiroshi-manabe'},
               'body':MARKER_V2+'\n'+fence+'json\n'+json.dumps(request)+'\n'+fence}
        self.assertEqual(intake(self.root,[issue])['accepted'],[62])
        first=dispatch(self.root,self.relay)
        self.assertEqual([r['issue'] for r in first['issue_prepared'] if
                          r['adapter']=='translation'],[62])
        self.assertFalse(first['submitted'])
        self.assertFalse(list((self.relay/'input').iterdir()))
        again=dispatch(self.root,self.relay)
        self.assertEqual(again['issue_prepared'],[])
        self.assertTrue(any(r['issue']==62 for r in again['issue_existing']))

        target_attempt=next(item['attempt'] for item in first['issue_prepared']
                            if item['adapter']=='translation' and item['issue']==62)
        row=r.load(self.root,target_attempt)
        row['state']='needs_review';row['reason']='Synthetic transport hold'
        r.save(self.root,row)
        held=dispatch(self.root,self.relay)
        self.assertEqual(held['issue_prepared'],[])
        self.assertTrue(any(item.get('issue')==62 for item in held['held']),held)
        self.assertEqual(len([record for record in r.records(self.root)
                              if record['adapter']=='translation' and record['issue']==62]),1)
        self.assertFalse(list((self.relay/'input').iterdir()))

    def test_prepare_deduplicates_and_submit_needs_exact_authorization(self):
        row=self.prepare();again=self.prepare()
        self.assertEqual(row['id'],again['id'])
        self.assertEqual(list((self.relay/'input').iterdir()),[])
        with self.assertRaises(c.ProjectError):r.submit(self.root,row['id'],'')
        self.submit(row);self.submit(row)
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)
        self.assertEqual(self.latest(row)['state'],'delivered')

    def test_sync_prepares_accepted_guides_without_submission_or_duplicates(self):
        first=r.sync_proposals(self.root,self.relay)
        self.assertEqual(len(first['prepared']),1)
        self.assertEqual(first['prepared'][0]['proposal']['work'],'gutenberg-41445')
        self.assertEqual(first['prepared'][0]['proposal']['type'],'work_analysis')
        self.assertFalse(first['model_called'])
        self.assertFalse(first['relay_submitted'])
        self.assertFalse(list((self.relay/'input').iterdir()))
        attempt=first['prepared'][0]['attempt']
        self.assertIsNone(r.load(self.root,attempt)['authorization'])
        second=r.sync_proposals(self.root,self.relay)
        self.assertEqual(second['prepared'],[])
        self.assertEqual(second['existing'][0]['attempt'],attempt)
        self.assertEqual(len(r.records(self.root)),1)

        work=r.load(self.root,attempt)
        self.submit(work);self.response(work);r.reconcile(self.root,True)
        third=r.sync_proposals(self.root,self.relay)
        self.assertEqual(len(third['prepared']),1)
        self.assertEqual(third['prepared'][0]['proposal']['type'],'target_guide')
        self.assertEqual(third['prepared'][0]['proposal']['target'],'en')
        self.assertEqual(len(r.records(self.root)),2)
        self.assertEqual(len(list((self.relay/'input').iterdir())),1)

    def test_sync_does_not_retry_stopped_attempt(self):
        first=r.sync_proposals(self.root,self.relay)
        attempt=first['prepared'][0]['attempt']
        row=r.load(self.root,attempt)
        row['state']='needs_review';row['reason']='Synthetic review hold';r.save(self.root,row)
        again=r.sync_proposals(self.root,self.relay)
        self.assertEqual(again['prepared'],[])
        self.assertEqual(len(again['held']),1)
        self.assertEqual(len(r.records(self.root)),1)
        self.assertFalse(list((self.relay/'input').iterdir()))

    def test_delivered_job_can_be_adopted_without_resending(self):
        row=self.prepare();path=r.request_path(self.root,row)
        duplicate=r.adopt(self.root,path,self.relay)
        self.assertEqual(row['id'],duplicate['id'])
        self.submit(row);mtime=(self.relay/'input'/row['input_name']).stat().st_mtime_ns
        self.register(row);self.submit(row)
        self.assertEqual((self.relay/'input'/row['input_name']).stat().st_mtime_ns,mtime)
        self.assertEqual(self.latest(row)['state'],'submitted')

    def test_legacy_result_staged_import_and_duplicate_poll(self):
        row=self.prepare();self.submit(row);self.response(row)
        r.reconcile(self.root,False)
        self.assertEqual(self.latest(row)['state'],'returned')
        self.assertFalse((self.root/'guide-results').exists())
        db=(self.relay/'relay.sqlite3').read_bytes()
        r.reconcile(self.root,True)
        current=self.latest(row)
        self.assertEqual(current['state'],'imported',current.get('reason'))
        self.assertTrue(current['outputs'])
        self.assertTrue((self.root/'guide-results/issue-12.json').exists())
        before=r.inventory(self.root);r.reconcile(self.root,True)
        self.assertEqual(r.inventory(self.root),before)
        self.assertEqual((self.relay/'relay.sqlite3').read_bytes(),db)
        c.validate_project(self.root)

    def test_independent_guide_import_and_dependency_discovery(self):
        row=self.prepare(task_type='work_analysis',work='gutenberg-41445');self.submit(row);self.response(row)
        r.reconcile(self.root,True)
        current=self.latest(row)
        self.assertEqual(current['state'],'imported',current.get('reason'))
        rows=r.status(self.root)['planning']['proposed']
        self.assertIn({'type':'target_guide','work':'gutenberg-41445','target':'en','state':'proposed'},rows)
        next_job=self.prepare(task_type='target_guide',work='gutenberg-41445',target='en')
        self.submit(next_job);self.response(next_job);r.reconcile(self.root,True)
        self.assertEqual(self.latest(next_job)['state'],'imported')
        c.validate_project(self.root)

    def test_malformed_response_leaves_canonical_files_unchanged(self):
        row=self.prepare();self.submit(row);before=r.inventory(self.root)
        self.response(row,lambda x:x.update(job_sha256='0'*64))
        r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertEqual(r.inventory(self.root),before)
        self.assertTrue((r.archive(self.root,row)/'response.zip').exists())

    def test_transport_mismatch_and_missing_download_require_review(self):
        for field,value in [('sha256','0'*64),('model','different-model')]:
            with self.subTest(field=field):
                row=self.prepare(task_type='work_analysis',work='gutenberg-41445')
                self.submit(row);self.register(row,**{field:value});r.reconcile(self.root,True)
                self.assertEqual(self.latest(row)['state'],'needs_review')
                break
        row=self.prepare();self.submit(row);self.register(row,'complete');r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertIn('missing',self.latest(row)['reason'])

    def test_submitting_is_never_automatically_resent(self):
        row=self.prepare();self.submit(row);self.register(row,'submitting')
        (self.relay/'input'/row['input_name']).unlink()
        r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'submitting')
        self.assertEqual(list((self.relay/'input').iterdir()),[])

    def test_lost_delivery_requires_review_and_explicit_new_retry(self):
        row=self.prepare();self.submit(row)
        (self.relay/'input'/row['input_name']).unlink()
        r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        with self.assertRaises(c.ProjectError):self.prepare()
        retry=self.prepare(guide_issue=12,retry_of=row['id'])
        self.assertNotEqual(retry['input_name'],row['input_name'])
        self.assertEqual(retry['retry_of'],row['id'])
        self.assertEqual(list((self.relay/'input').iterdir()),[])
        self.assertIsNone(retry['authorization'])

    def test_restored_download_resumes_without_resubmission(self):
        row=self.prepare();self.submit(row);self.register(row,'complete')
        r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.response(row)
        r.resume(self.root,row['id']);r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'imported')
        self.assertEqual(len(list((self.relay/'input').glob('*.zip'))),1)
        self.assertTrue(self.latest(row)['review_history'])

    def test_completed_transport_recovers_prior_review_hold_without_resubmission(self):
        work=self.prepare(task_type='work_analysis',work='gutenberg-41445')
        self.submit(work);self.response(work);r.reconcile(self.root,True)
        row=self.prepare(task_type='target_guide',work='gutenberg-41445',target='en')
        self.submit(row)
        self.register(row,'needs_review',review_reason='Result link was unavailable')
        r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        input_files=list((self.relay/'input').iterdir())
        self.response(row)
        db=(self.relay/'relay.sqlite3').read_bytes()
        result=r.reconcile(self.root,True,recover_completed=True)
        current=self.latest(row)
        self.assertEqual(current['state'],'imported',current.get('reason'))
        self.assertEqual(current['import_result']['observed_model'],'unknown')
        self.assertEqual(current['review_history'][-1]['recovery'],'exact completed relay result')
        self.assertEqual(list((self.relay/'input').iterdir()),input_files)
        self.assertEqual((self.relay/'relay.sqlite3').read_bytes(),db)
        self.assertFalse(result['model_invoked_directly'])
        before=r.inventory(self.root)
        r.reconcile(self.root,True,recover_completed=True)
        self.assertEqual(r.inventory(self.root),before)

    def test_completed_transport_does_not_recover_import_failure(self):
        row=self.prepare();self.submit(row)
        self.register(row,'needs_review',review_reason='Result link was unavailable')
        r.reconcile(self.root,True)
        self.response(row,lambda x:x.update(job_sha256='0'*64))
        r.reconcile(self.root,True,recover_completed=True)
        held=self.latest(row)
        self.assertEqual(held['state'],'needs_review')
        self.assertIsNotNone(held.get('response_sha256'))
        before=r.inventory(self.root)
        r.reconcile(self.root,True,recover_completed=True)
        self.assertEqual(r.inventory(self.root),before)
        self.assertEqual(self.latest(row)['updated_at'],held['updated_at'])

    def test_completed_transport_with_different_chat_stays_held(self):
        row=self.prepare();self.submit(row)
        self.register(row,'needs_review',review_reason='Result link unavailable')
        r.reconcile(self.root,True)
        self.response(row)
        self.register(row,'complete',chat_url='https://chatgpt.com/c/other-chat')
        r.reconcile(self.root,True,recover_completed=True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertIn('differs from the reviewed transport',self.latest(row)['reason'])
        self.assertFalse((self.root/'guide-results').exists())

    def test_changed_source_blocks_delivery(self):
        row=self.prepare()
        path=self.root/'books/gutenberg-36/work.json';work=c.read_json(path);work['author']+=' altered';c.write_json(path,work)
        with self.assertRaises(c.ProjectError):self.submit(row)
        self.assertEqual(list((self.relay/'input').iterdir()),[])

    def test_partial_install_failure_restores_original_files(self):
        row=self.prepare();self.submit(row);self.response(row);before=r.inventory(self.root)
        original=r._atomic_bytes;calls=[]
        def fail_second(path,data):
            calls.append(path)
            if len(calls)==2:raise OSError('Simulated installation interruption')
            original(path,data)
        with patch.object(r,'_atomic_bytes',side_effect=fail_second):r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertEqual(r.inventory(self.root),before)

    def test_crash_recovery_preserves_concurrent_human_edit(self):
        row=self.prepare();folder=r.archive(self.root,row)/'transaction';folder.mkdir()
        path=self.root/'books/gutenberg-36/reference/current.json';path.parent.mkdir();path.write_text('Human edit')
        name=path.relative_to(self.root).as_posix()
        c.write_json(folder/'journal.json',{name:{'before':None,'after':'0'*64}})
        row['state']='importing';r.save(self.root,row);r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertEqual(path.read_text(),'Human edit')

    def test_process_lock_blocks_second_coordinator(self):
        with r.locked(self.root):
            with self.assertRaises(c.ProjectError):r.reconcile(self.root)

    def test_publication_requires_separate_approval(self):
        row=self.prepare()
        with self.assertRaises(c.ProjectError):r.publish(self.root,row['id'])

    def test_mismatched_relay_model_is_not_imported(self):
        row=self.prepare();self.submit(row);self.response(row)
        self.register(row,'complete',model='unexpected-model')
        before=r.inventory(self.root);r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertEqual(r.inventory(self.root),before)

    def test_result_change_after_capture_is_rejected(self):
        row=self.prepare();self.submit(row);path=self.response(row)
        r.reconcile(self.root,False)
        with path.open('ab') as out:out.write(b'changed')
        r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'needs_review')
        self.assertFalse((self.root/'guide-results').exists())

    def init_git(self):
        for args in [('init','-b','main'),('config','user.name','Offline Fixture'),
                     ('config','user.email','fixture@example.invalid'),('add','.'),
                     ('commit','-m','Initial offline fixture')]:
            subprocess.run(['git','-C',str(self.root),*args],check=True,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        # Keep coordinator state private exactly as in the real repository.
        exclude=self.root/'.git/info/exclude'
        with exclude.open('a') as out:out.write('\n/private/\n')

    def test_exact_file_publication_and_unrelated_edit_guard(self):
        self.init_git()
        row=self.prepare();self.submit(row);self.response(row);r.reconcile(self.root,True)
        unrelated=self.root/'unrelated.txt';unrelated.write_text('Human work')
        with self.assertRaises(c.ProjectError):r.publish(self.root,row['id'],True)
        unrelated.unlink()
        outcome=r.publish(self.root,row['id'],True)
        self.assertIn('commit',outcome)
        self.assertEqual(subprocess.check_output(['git','-C',str(self.root),'status','--porcelain'],text=True),'')
        paths=subprocess.check_output(['git','-C',str(self.root),'diff-tree','--no-commit-id','--name-only','-r',outcome['commit']],text=True)
        self.assertEqual(set(paths.splitlines()),set(outcome['outputs']))
        self.assertNotIn('catalog.json',paths)

    def test_translation_issue_round_trip_preserves_snapshot(self):
        from translation_jobs import prompt_catalogue,intake,MARKER
        recipe=prompt_catalogue(self.root)[0]
        req={'schema_version':1,'work':'gutenberg-36','target':'ja','nodes':['n0001','n0004'],
             'source_fingerprint':c.source_fingerprint(self.root/'books/gutenberg-36'),
             'scope':'all','prompt':{'id':recipe['id'],'sha256':recipe['sha256']},
             'reference':{'mode':'none','revision':None},'instructions':''}
        intake(self.root,[{'number':77,'state':'open','user':{'login':'hiroshi-manabe'},
                           'body':MARKER+'\n```json\n'+json.dumps(req)+'\n```'}])
        row=self.prepare(translation_issue=77);self.submit(row);self.response(row);r.reconcile(self.root,True)
        current=self.latest(row)
        self.assertEqual(current['state'],'imported',current.get('reason'))
        self.assertTrue((self.root/'translation-results/issue-77.json').exists())
        self.assertTrue(list((self.root/'revisions/gutenberg-36/ja').glob('*.json')))
        self.assertFalse(c.read_json(self.root/'catalog.json')['revisions'])

    def test_ordered_material_request_uses_existing_translation_return_contract(self):
        from translation_jobs import prompt_catalogue,intake,MARKER_V2
        from materials import discover
        recipe=prompt_catalogue(self.root)[0]
        material=next(x for x in discover(self.root) if x['id']=='notes.work.gutenberg-36')
        req={'schema_version':2,'work':'gutenberg-36','target':'ja','nodes':['n0004'],
             'source_fingerprint':c.source_fingerprint(self.root/'books/gutenberg-36'),
             'scope':'all','prompt':{'id':recipe['id'],'sha256':recipe['sha256']},
             'reference':{'mode':'none','revision':None},'instructions':'',
             'materials':[{'id':material['id'],'sha256':material['sha256']}]}
        intake(self.root,[{'number':78,'state':'open','user':{'login':'hiroshi-manabe'},
                          'body':MARKER_V2+'\n```json\n'+json.dumps(req)+'\n```'}])
        row=self.prepare(translation_issue=78)
        metadata,job=r.info(r.request_path(self.root,row))
        self.assertEqual(metadata['adapter'],'translation')
        self.assertEqual(job['request']['schema_version'],2)
        self.assertIn('source notes',job['assembled_input'])
        self.submit(row);self.response(row);r.reconcile(self.root,True)
        self.assertEqual(self.latest(row)['state'],'imported')


if __name__=='__main__':unittest.main()
