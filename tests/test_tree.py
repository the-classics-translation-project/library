from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp
from source_import import validate_tree, compile_plan, apply
from intake import parse_issue, import_issues, parse_catalogue, MARKER

class TreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        shutil.copytree(ctp.ROOT/'examples/tree-work',self.root/'examples/tree-work')
        shutil.copytree(ctp.ROOT/'site',self.root/'site')
        shutil.copy2(ctp.ROOT/'project.json',self.root/'project.json')
        ctp.write_json(self.root/'catalog.json',{'schema_version':1,'revisions':[]})
        ctp.write_json(self.root/'queue.json',{'schema_version':1,'works':[]})
        self.w=self.root/'examples/tree-work'; self.edpath=self.w/'editions/en-modern/edition.json'
        self.ed=ctp.read_json(self.edpath);self.tree=ctp.read_json(self.w/'structure.json')
        self.config=ctp.read_json(self.root/'project.json')
    def tearDown(self):self.tmp.cleanup()
    def freeze(self):
        rev,path=ctp.freeze(self.w,'en-modern',self.root);return rev,ctp.read_json(path)
    def report(self,rev,snap,node='n0001',field='label',quote='Last Ferry'):
        text=ctp.field_map(snap)[node+':'+field]['text'];start=text.index(quote)
        a={'unit':'utf16-code-units','start':len(text[:start].encode('utf-16-le'))//2,'end':len(text[:start+len(quote)].encode('utf-16-le'))//2,'exact':quote,'prefix':text[:start],'suffix':text[start+len(quote):]}
        return {'schema_version':2,'report_id':'review-test','created_at':'2026-10-16','repository':self.config['repository'],'work':'tree-work','edition':'en-modern','revision':rev,'annotations':[{'id':'note-1','node':node,'field':field,'scope':'text','anchor':a,'comment':'Test'}]}
    def test_arbitrary_tree_and_branch_text(self):
        w,t=ctp.validate_work(self.w);self.assertEqual(len(validate_tree(t)),5);self.assertIn('text',t['children'][0]);self.assertNotIn('label',t['children'][0]['children'][0])
    def test_raw_bytes_and_newline_normalization(self):
        from source_import import prepare, validate_blocks
        raw=self.root/'raw.txt';raw.write_bytes(b'\xef\xbb\xbfTitle\r\n\r\nBody.\r\n')
        dest=self.root/'prepared';prepare(raw,dest);validate_blocks(dest)
        self.assertEqual((dest/'acquired.txt').read_bytes(),raw.read_bytes())
        self.assertEqual((dest/'normalized.txt').read_text(),'Title\n\nBody.\n')
    def test_partial_acquisition_is_not_overwritten(self):
        from source_import import prepare
        raw=self.root/'raw.txt';raw.write_text('New source')
        dest=self.root/'prepared';dest.mkdir();(dest/'acquired.txt').write_text('Original bytes')
        with self.assertRaises(ctp.ProjectError):prepare(raw,dest)
        self.assertEqual((dest/'acquired.txt').read_text(),'Original bytes')
    def test_unlabeled_root_does_not_invent_visible_title(self):
        from site_builder import reader
        rev,snap=self.freeze();root=snap['tree']['id']
        del snap['tree']['label'];snap['edition']['nodes'].pop(root);snap['target_nodes'].pop(root)
        output=reader(snap,rev,self.config,'')
        self.assertNotIn('<h1>tree-work</h1>',output)
    def test_duplicate_node_id_rejected(self):
        self.tree['children'][0]['id']=self.tree['id']
        with self.assertRaises(ctp.ProjectError):validate_tree(self.tree)
    def test_semantic_id_rejected(self):
        self.tree['id']='volume-1'
        with self.assertRaises(ctp.ProjectError):validate_tree(self.tree)
    def test_missing_label_detected(self):
        del self.ed['nodes']['n0004']['label'];self.assertIn({'node':'n0004','field':'label'},ctp.missing_fields(self.tree,self.ed))
    def test_missing_label_blocks_ready(self):
        del self.ed['nodes']['n0004']['label'];self.ed['status']='ready'
        with self.assertRaises(ctp.ProjectError):ctp.validate_tree_edition(self.tree,self.ed)
    def test_no_invented_target_heading(self):
        self.ed['nodes']['n0003']={'label':'Invented'}
        with self.assertRaises(ctp.ProjectError):ctp.validate_tree_edition(self.tree,self.ed)
    def test_unknown_target_node(self):
        self.ed['nodes']['n9999']={'label':'New'}
        with self.assertRaises(ctp.ProjectError):ctp.validate_tree_edition(self.tree,self.ed)
    def test_repeated_file_rejected(self):
        self.ed['nodes']['n0005']['text']=self.ed['nodes']['n0004']['text']
        with self.assertRaises(ctp.ProjectError):ctp.validate_tree_edition(self.tree,self.ed,self.edpath.parent)
    def test_source_text_cannot_silently_change(self):
        (self.w/'source/n0004.md').write_text('lost original')
        with self.assertRaises(ctp.ProjectError):ctp.validate_work(self.w)
    def test_source_plan_accounts_for_every_block(self):
        record=ctp.read_json(self.w/'acquisition/blocks.json');plan=ctp.read_json(self.w/'acquisition/plan.json')
        t,files,audit=compile_plan(record,plan);self.assertEqual(audit['assigned_blocks'],len(record['blocks']));self.assertEqual(t,self.tree)
    def test_ai_cannot_retype_labels(self):
        r=ctp.read_json(self.w/'acquisition/blocks.json');p=ctp.read_json(self.w/'acquisition/plan.json');p['tree']['label']='invented'
        with self.assertRaises(ctp.ProjectError):compile_plan(r,p)
    def test_block_omission_rejected(self):
        r=ctp.read_json(self.w/'acquisition/blocks.json');p=ctp.read_json(self.w/'acquisition/plan.json');p['tree']['children'][0]['text_blocks']=[]
        with self.assertRaises(ctp.ProjectError):compile_plan(r,p)
    def test_block_duplication_rejected(self):
        r=ctp.read_json(self.w/'acquisition/blocks.json');p=ctp.read_json(self.w/'acquisition/plan.json');p['tree']['text_blocks']=p['tree']['label_blocks']
        with self.assertRaises(ctp.ProjectError):compile_plan(r,p)
    def test_no_automatic_reimport_or_renumber(self):
        with self.assertRaises(ctp.ProjectError):apply(self.w,self.w/'acquisition/plan.json')
    def test_title_can_be_annotated(self):
        rev,snap=self.freeze();self.assertEqual(ctp.validate_review(self.report(rev,snap),self.root)['annotations'],1)
    def test_heading_can_be_annotated(self):
        rev,snap=self.freeze();ctp.validate_review(self.report(rev,snap,'n0004','label','quay'),self.root)
    def test_body_can_be_annotated(self):
        rev,snap=self.freeze();ctp.validate_review(self.report(rev,snap,'n0004','text','Mara'),self.root)
    def test_quote_tampering_rejected(self):
        rev,snap=self.freeze();r=self.report(rev,snap);r['annotations'][0]['anchor']['exact']='different'
        with self.assertRaises(ctp.ProjectError):ctp.validate_review(r,self.root)
    def test_full_retranslation_keeps_old_report(self):
        rev,snap=self.freeze();r=self.report(rev,snap,'n0004','text','Mara')
        (self.w/'editions/en-modern/text/n0004.md').write_text('A newly written paragraph.\n\nA different structure.\n')
        newer,_=self.freeze();self.assertNotEqual(rev,newer);ctp.validate_review(r,self.root)
    def test_source_label_is_not_translated_fallback(self):
        del self.ed['nodes']['n0001']['label'];ctp.write_json(self.edpath,self.ed)
        with self.assertRaises(ctp.ProjectError):self.freeze()
    def test_generation_prompt_tampering_rejected(self):
        r=ctp.read_json(next((self.edpath.parent/'runs').glob('*.json')));r['prompts'][0]['text']='changed'
        with self.assertRaises(ctp.ProjectError):ctp.validate_run(r)
    def test_tree_epub_toc_and_xml(self):
        from site_builder import epub
        rev,snap=self.freeze();out=self.root/'edition.epub';epub(snap,rev,out,self.root)
        with zipfile.ZipFile(out) as z:
            self.assertEqual(z.namelist()[0],'mimetype');self.assertEqual(z.getinfo('mimetype').compress_type,zipfile.ZIP_STORED)
            for name in z.namelist():
                if name.endswith(('.xml','.opf','.xhtml')):ET.fromstring(z.read(name))
            nav=ET.fromstring(z.read('EPUB/nav.xhtml'));ns={'x':'http://www.w3.org/1999/xhtml'}
            self.assertGreaterEqual(len(nav.findall('.//x:ol',ns)),4)
            self.assertNotIn('EPUB/n0003.xhtml',z.namelist())  # no blank spine page for an unlabeled grouping
            self.assertTrue(nav.findall('.//x:li/x:span',ns))
    def issue(self,author='hiroshi-manabe',eid=41445,targets=None):
        r={'schema_version':1,'source':{'type':'gutenberg','id':eid},'targets':targets or ['en']}
        return {'number':7,'state':'open','user':{'login':author},'body':MARKER+'\n\n```json\n'+json.dumps(r)+'\n```\n'}
    def test_authorized_intake(self):
        result=import_issues(self.root,[self.issue()]);self.assertTrue(result['changed']);self.assertEqual(result['accepted'],[7])
    def test_intake_is_idempotent(self):
        import_issues(self.root,[self.issue()]);self.assertFalse(import_issues(self.root,[self.issue()])['changed'])
    def test_new_target_merges_without_erasing_old(self):
        import_issues(self.root,[self.issue()]);import_issues(self.root,[self.issue(targets=['ja'])]);self.assertEqual(ctp.read_json(self.root/'queue.json')['works'][0]['targets'],['en','ja'])
    def test_outsider_cannot_queue_work(self):
        result=import_issues(self.root,[self.issue('outsider')]);self.assertFalse(result['changed']);self.assertEqual(len(result['rejected']),1)
    def test_arbitrary_url_rejected(self):
        issue=self.issue();issue['body']=issue['body'].replace('"id": 41445','"url": "file:///secrets"')
        with self.assertRaises(ctp.ProjectError):parse_issue(issue,self.config)
    def test_unregistered_language_rejected(self):
        with self.assertRaises(ctp.ProjectError):parse_issue(self.issue(targets=['run-shell-command']),self.config)
    def test_duplicate_marker_rejected(self):
        issue=self.issue();issue['body']+=MARKER
        with self.assertRaises(ctp.ProjectError):parse_issue(issue,self.config)
    def test_catalogue_csv_unicode(self):
        data='Text#,Title,Authors,Language,Type\n1,"日本語, title",作者,ja,Text\n'.encode();self.assertEqual(parse_catalogue(data)[0]['title'],'日本語, title')
    def test_catalogue_wrong_columns_rejected(self):
        with self.assertRaises(ctp.ProjectError):parse_catalogue(b'name,value\na,1\n')

if __name__=='__main__':unittest.main()
