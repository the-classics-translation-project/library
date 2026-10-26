"""End-to-end deterministic ZIP translation contract, without any model call."""
from pathlib import Path
from zipfile import ZipFile
import copy
import json
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp
from legacy_v1 import ProjectError, digest
from translation_jobs import (
    prompt_catalogue, render_prompt, expanded_nodes, validate_request,
    parse_issue, intake, validate_queue, export_translation, import_translation,
    export_guide, import_guide, validate_results, MARKER
)

class TranslationZipTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        wd=self.root/'books/gutenberg-36'
        shutil.copytree(ctp.ROOT/'examples/tree-work',wd)
        shutil.rmtree(wd/'editions')
        metadata=ctp.read_json(wd/'work.json')
        metadata['id']='gutenberg-36'
        ctp.write_json(wd/'work.json',metadata)
        ctp.write_json(wd/'rights.json',{'status':'acquired','eligible':True})
        shutil.copy(ctp.ROOT/'project.json',self.root/'project.json')
        (self.root/'prompts/translation').mkdir(parents=True)
        shutil.copy(ctp.ROOT/'prompts/translation/contemporary.md',
                    self.root/'prompts/translation/contemporary.md')
        (self.root/'docs').mkdir()
        shutil.copy(ctp.ROOT/'docs/editorial-policy.md',self.root/'docs/editorial-policy.md')
        (self.root/'catalog.json').write_text('{"schema_version":1,"revisions":[]}')
        self.work=wd
        self.prompt=prompt_catalogue(self.root)[0]
        self.tree=ctp.read_json(wd/'structure.json')
        self.fp=ctp.source_fingerprint(wd)

    def request(self, scope='all', reference=None, nodes=None):
        return {'schema_version':1,'work':'gutenberg-36','target':'ja',
                'nodes':nodes or ['n0004'],'source_fingerprint':self.fp,
                'scope':scope,'prompt':{'id':self.prompt['id'],
                        'sha256':self.prompt['sha256']},
                'reference':reference or {'mode':'none','revision':None},
                'instructions':''}

    def issue(self,number,req=None,author='hiroshi-manabe'):
        req=req or self.request()
        fence=chr(96)*3
        return {'number':number,'state':'open','user':{'login':author},
                'body':MARKER+'\n'+fence+'json\n'+json.dumps(req)+'\n'+fence}

    def reply(self,issue,model='GPT-6',value='Translated into Japanese'):
        from translation_jobs import prepare_job, request_entry, zip_files
        _,manifest=prepare_job(self.root,request_entry(self.root,issue))
        translated={nid:{field:value for field in fields}
                    for nid,fields in manifest['requested_fields'].items()}
        out=self.root/f'answer-{issue}.zip'
        response={'schema_version':1,'kind':'translation','issue':issue,
                  'job_sha256':manifest['job_sha256'],'model_label':model,
                  'translations':translated}
        zip_files(out,{'response.json':response})
        return out

    def test_prompt_substitution_and_source_tree_expansion(self):
        text=render_prompt('In {{target_language}} ({{target_language_code}}).',
             {'target_language':'Japanese','target_language_code':'ja'})
        self.assertEqual(text,'In Japanese (ja).')
        with self.assertRaises(ProjectError):
            render_prompt('{{shell}}',{'shell':'echo'})
        selected=expanded_nodes(self.tree,[self.tree['id']])
        self.assertEqual(len(selected),len(list(ctp.walk(self.tree))))
        self.assertIn('n0004',[n['id'] for n in selected])

    def test_authorized_immutable_issues_and_pinned_prompt(self):
        self.assertIsNone(parse_issue(self.root,{'state':'open','body':'ordinary issue'}))
        self.assertEqual(intake(self.root,[self.issue(42,author='attacker')])['accepted'],[])
        self.assertEqual(intake(self.root,[self.issue(42)])['accepted'],[42])
        self.assertEqual(intake(self.root,[self.issue(42)])['changed'],False)
        self.assertEqual(validate_queue(self.root)['requests'][0]['prompt_text'],
                         (self.root/'prompts/translation/contemporary.md').read_text())
        path=self.root/'prompts/translation/contemporary.md'
        path.write_text('# Edited later\nTranslate into {{target_language}}.')
        # Already accepted requests stay pinned to their original prompt.
        self.assertEqual(validate_queue(self.root)['requests'][0]['issue'],42)
        with self.assertRaises(ProjectError):
            validate_request(self.root,self.request())

    def test_v2_material_order_and_accepted_snapshot_survive_later_edits(self):
        from materials import discover
        from translation_jobs import MARKER_V2,prepare_job,request_entry
        (self.root/'queue.json').write_text(json.dumps({'schema_version':1,'works':[
            {'id':'gutenberg-36','targets':['ja']}]}))
        material=self.root/'materials/files/ja.md';material.parent.mkdir(parents=True)
        material.write_text('# Japanese guide\n\nUse natural dialogue.\n')
        manifest={'schema_version':1,'entries':[{'id':'style.ja','path':'materials/files/ja.md',
            'title':'Japanese guide','description':'Draft style note','scope':'target_language',
            'kind':'reference','work':None,'target':'ja','tags':['draft']}]}
        (self.root/'materials/manifest.json').write_text(json.dumps(manifest))
        row=next(x for x in discover(self.root) if x['id']=='style.ja')
        request=self.request();request['schema_version']=2
        request['materials']=[{'id':'style.ja','sha256':row['sha256']}]
        fence=chr(96)*3
        issue=self.issue(48,request)
        issue['body']=MARKER_V2+'\n'+fence+'json\n'+json.dumps(request)+'\n'+fence
        self.assertEqual(intake(self.root,[issue])['accepted'],[48])
        pinned=validate_queue(self.root)['requests'][0]['materials_snapshot']
        self.assertEqual(pinned[0]['text'],material.read_text())
        material.write_text('# Replaced later\n\nDifferent advice.\n')
        self.assertEqual(validate_queue(self.root)['requests'][0]['materials_snapshot'],pinned)
        job,metadata=prepare_job(self.root,request_entry(self.root,48))
        self.assertIn('Use natural dialogue.',job['assembled_input'])
        self.assertNotIn('Different advice.',job['assembled_input'])
        self.assertEqual(job['ordered_materials'],pinned)
        out=self.root/'v2-request.zip';export_translation(self.root,48,out)
        with ZipFile(out) as archive:
            packaged=json.loads(archive.read('input/job.json'))
            self.assertEqual(packaged['assembled_input'],job['assembled_input'])
            self.assertIn('ordered materials',archive.read('README.md').decode())
        self.assertEqual(metadata['job_sha256'],json.loads(ZipFile(out).read('input/manifest.json'))['job_sha256'])
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from io import StringIO
        preview=self.root/'full-preview.md';screen=StringIO()
        with patch.object(ctp,'ROOT',self.root),patch.object(sys,'argv',
             ['ctp','translation-preview','48','--output',str(preview)]),redirect_stdout(screen):
            self.assertEqual(ctp.main(),0)
        self.assertEqual(preview.read_text(),job['assembled_input'])
        self.assertFalse(json.loads(screen.getvalue())['submitted'])

    def test_zip_export_import_retranslation_and_history(self):
        self.assertEqual(intake(self.root,[self.issue(42)])['accepted'],[42])
        out=self.root/'request.zip'
        self.assertEqual(export_translation(self.root,42,out)['issue'],42)
        with ZipFile(out) as z:
            self.assertEqual(set(z.namelist()),
                    {'README.md','input/job.json','input/manifest.json'})
            job=json.loads(z.read('input/job.json'))
            self.assertIn('Japanese',job['expanded_prompt'])
            self.assertTrue(job['source_nodes'])
        response=self.reply(42)
        imported=import_translation(self.root,response)
        self.assertFalse(imported['published'])
        self.assertIsNone(imported['previous_revision'])
        self.assertTrue((self.work/'editions/ja/text/n0004.md').exists())
        self.assertTrue((self.root/'revisions/gutenberg-36/ja'/
                         (imported['revision']+'.json')).exists())
        self.assertTrue(import_translation(self.root,response)['already_imported'])
        validate_results(self.root)
        old=imported['revision']
        ref={'mode':'text','revision':old}
        self.assertEqual(intake(self.root,[self.issue(43,self.request(reference=ref))])['accepted'],[43])
        from translation_jobs import prepare_job, request_entry
        job,manifest=prepare_job(self.root,request_entry(self.root,43))
        self.assertIn('n0004',job['previous_translation'])
        response2=self.reply(43,value='A fresh Japanese rendition')
        changed=import_translation(self.root,response2)
        self.assertEqual(changed['previous_revision'],old)
        self.assertNotEqual(changed['revision'],old)
        prior=ctp.load_snapshot(self.root,'gutenberg-36','ja',old)
        self.assertEqual(prior['target_nodes']['n0004']['text']['markdown'],
                         'Translated into Japanese')
        validate_results(self.root)

    def test_reference_requires_actual_frozen_revision(self):
        r=self.request(reference={'mode':'text','revision':'a'*64})
        with self.assertRaises((ProjectError,FileNotFoundError)):
            validate_request(self.root,r)

    def test_bad_reply_and_wrong_input_are_rejected_without_writes(self):
        from translation_jobs import zip_files
        intake(self.root,[self.issue(42)])
        response=self.reply(42)
        with ZipFile(response) as z:
            record=json.loads(z.read('response.json'))
        record['job_sha256']='b'*64
        wrong=self.root/'wrong.zip'
        zip_files(wrong,{'response.json':record})
        with self.assertRaises(ProjectError):
            import_translation(self.root,wrong)
        record['job_sha256']='a'*64
        extra=self.root/'extra.zip'
        zip_files(extra,{'response.json':record,'bad/path':'not allowed'})
        with self.assertRaises(ProjectError):
            import_translation(self.root,extra)
        self.assertFalse((self.work/'editions/ja').exists())

    def test_guide_zip_and_immutable_reference_files(self):
        package=self.root/'guide.zip'
        job=export_guide(self.root,'gutenberg-36','ja',package)
        with ZipFile(package) as z:
            self.assertEqual(set(z.namelist()),
                {'README.md','input/job.json','input/manifest.json'})
        from translation_jobs import zip_files
        answer=self.root/'guide-answer.zip'
        response={'schema_version':1,'kind':'guide','work':'gutenberg-36',
            'target':'ja','job_sha256':job['job_sha256'],'model_label':'unknown',
            'work_guide':'Recurring character and place names.',
            'target_guide':'Name consistency and terminology.'}
        zip_files(answer,{'response.json':response})
        result=import_guide(self.root,answer)
        self.assertTrue((self.root/result['files']['work_guide']).is_file())
        self.assertTrue((self.root/result['files']['target_guide']).is_file())
        self.assertTrue((self.work/'reference/current.json').exists())
        self.assertTrue((self.work/'editions/ja/reference/current.json').exists())

if __name__=='__main__':unittest.main()
