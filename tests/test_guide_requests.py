"""Offline guide Issue, Markdown ZIP and Admin status checks; no model/network use."""
from pathlib import Path
from zipfile import ZipFile
import json
import re
import subprocess
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp
import site_builder
from legacy_v1 import ProjectError, digest, read_json, write_json
from translation_jobs import zip_files, read_response, _guide
from guide_requests import (
    GUIDE_MARKER, guide_prompt, parse_guide_issue, validate_guide_request,
    intake_guide, validate_guide_queue, guide_entry, prepare_guide_issue,
    export_guide_issue, pending_guides, validate_guide_results
)


class WholeWorkGuideTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.work=self.root/'books/gutenberg-36'
        shutil.copytree(ctp.ROOT/'examples/tree-work',self.work)
        shutil.rmtree(self.work/'editions')
        obj=read_json(self.work/'work.json');obj['id']='gutenberg-36'
        write_json(self.work/'work.json',obj)
        write_json(self.work/'rights.json',
                   {'status':'acquired','eligible':True,'reasons':[]})
        shutil.copy(ctp.ROOT/'project.json',self.root/'project.json')
        (self.root/'prompts').mkdir()
        shutil.copy(ctp.ROOT/'prompts/whole-work-guide.md',
                    self.root/'prompts/whole-work-guide.md')
        (self.root/'site').mkdir()
        shutil.copy(ctp.ROOT/'site/admin.js',self.root/'site/admin.js')
        shutil.copy(ctp.ROOT/'site/translation-admin.js',
                    self.root/'site/translation-admin.js')
        write_json(self.root/'catalog.json',{'schema_version':1,'revisions':[]})
        write_json(self.root/'queue.json',{'schema_version':1,'works':[
            {'id':'gutenberg-36','source':{'type':'gutenberg','id':36},
             'targets':['ja'],'requests':[]}
        ]})
        self.src_hash=ctp.source_fingerprint(self.work)
        self.prompt_sha=digest(guide_prompt(self.root).encode())

    def request(self):
        return {'schema_version':1,'work':'gutenberg-36','target':'ja',
                'source_fingerprint':self.src_hash,
                'prompt_sha256':self.prompt_sha}

    def issue(self,number,req=None,author='hiroshi-manabe'):
        fence=chr(96)*3
        body='Generate work guide\n\n'+GUIDE_MARKER+'\n\n'+fence+'json\n'+(
            json.dumps(req if req is not None else self.request()))+'\n'+fence+'\n'
        return {'number':number,'state':'open',
                'user':{'login':author},'body':body}

    def answer(self,issue,work_text=None,target_text=None):
        entry=guide_entry(self.root,issue)
        _,manifest=prepare_guide_issue(self.root,entry)
        response={'schema_version':1,'kind':'guide',
                  'work':'gutenberg-36','target':'ja','issue':issue,
                  'job_sha256':manifest['job_sha256'],'model_label':'unknown',
                  'work_guide':work_text or
                      '# Characters and Names\n\nCharacter relationships.\n\n'
                      '## Open Questions\n\nAn unresolved ambiguity.',
                  'target_guide':target_text or
                      '# Recurring Terminology\n\nA preferred term with '
                      'contextual alternatives, not a fixed field schema.'}
        dest=self.root/('return-'+str(issue)+'.zip')
        zip_files(dest,{'response.json':response})
        return dest

    def test_authorization_idempotence_and_rejection(self):
        self.assertIsNone(parse_guide_issue(self.root,{'state':'open','body':'ordinary'}))
        self.assertEqual(intake_guide(self.root,[self.issue(70,author='stranger')])['accepted'],[])
        self.assertEqual(intake_guide(self.root,[self.issue(70)])['accepted'],[70])
        self.assertFalse(intake_guide(self.root,[self.issue(70)])['changed'])
        self.assertEqual([x['issue'] for x in pending_guides(self.root)['requests']],[70])
        req=self.request();req['work']='gutenberg-999'
        self.assertEqual(intake_guide(self.root,[self.issue(71,req)])['accepted'],[])
        req=self.request();req['source_fingerprint']='a'*64
        self.assertEqual(intake_guide(self.root,[self.issue(72,req)])['accepted'],[])
        req=self.request();req['prompt_sha256']='a'*64
        self.assertEqual(intake_guide(self.root,[self.issue(73,req)])['accepted'],[])
        req=self.request();req['extra']='arbitrary command'
        self.assertEqual(intake_guide(self.root,[self.issue(74,req)])['accepted'],[])
        self.assertEqual(len(validate_guide_queue(self.root)['requests']),1)

    def test_complete_issue_zip_round_trip_preserves_unstructured_markdown(self):
        intake_guide(self.root,[self.issue(70)])
        package=self.root/'guide-input.zip'
        summary=export_guide_issue(self.root,70,package)
        self.assertEqual(summary['issue'],70)
        self.assertFalse(summary['ai_called'])
        with ZipFile(package) as z:
            self.assertEqual(set(z.namelist()),
                {'README.md','input/job.json','input/manifest.json'})
            readme=z.read('README.md').decode('utf-8')
            self.assertIn('model: 6 Extra High',readme)
            self.assertIn('output_filename: guide-input-result.zip',readme)
            job=json.loads(z.read('input/job.json'))
            manifest=json.loads(z.read('input/manifest.json'))
            self.assertEqual(job['issue'],70)
            self.assertIn('Japanese',job['guide_instructions'])
            self.assertIn('## Target-language translation guide',
                          job['guide_instructions'])
            self.assertEqual(manifest['issue'],70)
            self.assertEqual(manifest['job_sha256'],summary['job_sha256'])
            self.assertGreater(len(job['source_nodes']),1)
        answer=self.answer(70,target_text='Freeform prose, not a row schema.')
        from translation_jobs import import_guide
        imported=import_guide(self.root,answer)
        self.assertEqual(imported['issue'],70)
        self.assertEqual(_guide(self.work/'editions/ja/reference'),
                         'Freeform prose, not a row schema.')
        self.assertEqual(import_guide(self.root,answer)['already_imported'],True)
        self.assertEqual(pending_guides(self.root)['requests'],[])
        validate_guide_results(self.root)
        record=read_json(self.root/'guide-results/issue-70.json')
        self.assertEqual(record['job_sha256'],summary['job_sha256'])
        self.assertTrue((self.root/record['run_record']).exists())

    def test_second_guide_request_preserves_prior_versions(self):
        from translation_jobs import import_guide
        intake_guide(self.root,[self.issue(70)])
        first=import_guide(self.root,self.answer(70))
        previous=(self.root/first['files']['target_guide']).read_text(encoding='utf-8')
        intake_guide(self.root,[self.issue(71)])
        second=import_guide(self.root,self.answer(71,target_text='An entirely new guide.'))
        self.assertNotEqual(first['files']['target_guide'],second['files']['target_guide'])
        self.assertTrue((self.root/first['files']['target_guide']).exists())
        self.assertEqual((self.root/first['files']['target_guide']).read_text(),previous)
        self.assertEqual(_guide(self.work/'editions/ja/reference'),'An entirely new guide.')
        validate_guide_results(self.root)
        self.assertEqual(len(list((self.work/'reference').glob('guide-run-*.json'))),2)

    def test_prompt_change_does_not_reinterpret_accepted_issue(self):
        intake_guide(self.root,[self.issue(70)])
        prompt=self.root/'prompts/whole-work-guide.md'
        prompt.write_text('# New prompt\nThis changed later, {{target_language}}.',
                          encoding='utf-8')
        validate_guide_queue(self.root)
        exported=self.root/'accepted-old-prompt.zip'
        export_guide_issue(self.root,70,exported)
        with ZipFile(exported) as z:
            job=json.loads(z.read('input/job.json'))
        self.assertIn('## Target-language translation guide',job['guide_instructions'])
        self.assertNotIn('This changed later',job['guide_instructions'])
        bad=self.issue(71)
        self.assertEqual(intake_guide(self.root,[bad])['accepted'],[])
        self.assertTrue(intake_guide(self.root,[bad])['rejected'])

    def test_wrong_zip_and_conflicting_duplicate_rejected(self):
        from translation_jobs import import_guide
        intake_guide(self.root,[self.issue(70)])
        response=self.answer(70)
        with ZipFile(response) as z:
            obj=json.loads(z.read('response.json'))
        wrong=dict(obj,job_sha256='a'*64)
        invalid=self.root/'invalid.zip'
        zip_files(invalid,{'response.json':wrong})
        with self.assertRaises(ProjectError):import_guide(self.root,invalid)
        with self.assertRaises(ProjectError):
            zip_files(self.root/'invalid-extra.zip',{'response.json':obj,'README.md':'extra'})
            import_guide(self.root,self.root/'invalid-extra.zip')
        self.assertFalse((self.work/'reference/current.json').exists())
        import_guide(self.root,response)
        different=self.root/'changed.zip'
        zip_files(different,{'response.json':dict(obj,work_guide='Contradictory revision')})
        with self.assertRaises(ProjectError):import_guide(self.root,different)
        self.assertEqual(_guide(self.work/'reference'),
                         obj['work_guide'])

    def test_admin_manifest_exposes_only_guide_status_and_hash(self):
        html=site_builder.admin(self.root,read_json(self.root/'project.json'),'')
        raw=re.search(r'<script id="admin-data" type="application/json">(.*?)</script>',
                      html,re.S).group(1)
        data=json.loads(raw)
        self.assertEqual(data['guide_prompt_sha256'],self.prompt_sha)
        self.assertEqual(data['sources'][0]['guides'],
                         {'work':False,'targets':[]})
        self.assertIn('Prepare guide-generation Issue',html)
        intake_guide(self.root,[self.issue(70)])
        from translation_jobs import import_guide
        imported=import_guide(self.root,self.answer(70))
        html=site_builder.admin(self.root,read_json(self.root/'project.json'),'')
        raw=re.search(r'<script id="admin-data" type="application/json">(.*?)</script>',
                      html,re.S).group(1)
        data=json.loads(raw)
        self.assertEqual(data['sources'][0]['guides'],
                         {'work':False,'targets':[]})
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add',
                        'books/gutenberg-36/reference',
                        'books/gutenberg-36/editions/ja/reference'],check=True)
        for key,value in [('user.name','Fixture'),('user.email','fixture@example.invalid')]:
            subprocess.run(['git','-C',str(self.root),'config',key,value],check=True)
        subprocess.run(['git','-C',str(self.root),'commit','-qm','Approved guide fixture'],check=True)
        html=site_builder.admin(self.root,read_json(self.root/'project.json'),'')
        raw=re.search(r'<script id="admin-data" type="application/json">(.*?)</script>',
                      html,re.S).group(1)
        data=json.loads(raw)
        self.assertEqual(data['sources'][0]['guides'],
                         {'work':True,'targets':['ja']})
        self.assertNotIn('Character relationships.',html)
        self.assertNotIn('a preferred term with contextual alternatives',html)


    def test_cli_issue_intake_export_and_import(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from unittest.mock import patch
        issues=self.root/'issues.json'
        write_json(issues,[self.issue(90)])
        def run(*arguments):
            out=StringIO()
            with patch.object(ctp,'ROOT',self.root), \
                 patch.object(sys,'argv',['ctp',*arguments]), redirect_stdout(out):
                status=ctp.main()
            self.assertEqual(status,0,out.getvalue())
            return json.loads(out.getvalue())
        intake=run('guide-intake','--issues',str(issues))
        self.assertEqual(intake['accepted'],[90])
        pending=run('guide-pending')
        self.assertEqual(pending['requests'][0]['issue'],90)
        package=self.root/'cli-guide.zip'
        result=run('guide-export','--issue','90','--output',str(package))
        self.assertEqual(result['issue'],90)
        self.assertTrue(package.exists())
        from translation_jobs import zip_files
        _,manifest=prepare_guide_issue(self.root,guide_entry(self.root,90))
        reply=self.root/'cli-return.zip'
        zip_files(reply,{'response.json':{
            'schema_version':1,'kind':'guide','issue':90,
            'work':'gutenberg-36','target':'ja',
            'job_sha256':manifest['job_sha256'],'model_label':'unknown',
            'work_guide':'Useful observations on the full original.',
            'target_guide':'Suggested terminology with contextual alternatives.'
        }})
        result=run('guide-import',str(reply))
        self.assertEqual(result['issue'],90)
        self.assertEqual(run('guide-pending')['requests'],[])


if __name__=='__main__':
    unittest.main()
