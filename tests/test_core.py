"""Deterministic checks; these are not literary quality assessments."""
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import ctp

class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'library'
        self.root.mkdir()
        (self.root/'books').mkdir()
        shutil.copytree(ctp.ROOT/'site', self.root/'site')
        shutil.copytree(ctp.ROOT/'examples/demo-work', self.root/'examples/demo-work')
        shutil.copytree(ctp.ROOT/'revisions/demo-work', self.root/'revisions/demo-work')
        ctp.write_json(self.root/'examples/catalog.json', {'schema_version':1,'revisions':[r for r in ctp.read_json(ctp.ROOT/'examples/catalog.json')['revisions'] if r['work']=='demo-work']})
        shutil.copy2(ctp.ROOT/'project.json', self.root/'project.json')
        ctp.write_json(self.root/'catalog.json', {'schema_version':1,'revisions':[]})
        self.work = self.root / 'examples/demo-work'
        self.edpath = self.work / 'editions/en-modern/edition.json'
        self.ed = ctp.read_json(self.edpath)
        self.record = ctp.read_json(self.root / 'examples/catalog.json')['revisions'][0]
        self.revision = self.record['revision']
        self.snap = ctp.load_snapshot(self.root, 'demo-work', 'en-modern', self.revision)
    def tearDown(self):
        self.temp.cleanup()
    def report(self, section='chapter-01', quote='Leno'):
        text = next(s['text'] for s in self.snap['sections'] if s['id'] == section)
        point = text.index(quote)
        start = len(text[:point].encode('utf-16-le')) // 2
        end = start + len(quote.encode('utf-16-le')) // 2
        return {'schema_version': 1, 'report_id': 'test-report', 'created_at':'2026-10-16T00:00:00Z',
            'repository':ctp.read_json(self.root/'project.json')['repository'],'work':'demo-work', 'edition':'en-modern',
            'revision':self.revision,'annotations':[{'id':'note-1','section':section,'scope':'text',
                'anchor':{'unit':'utf16-code-units','start':start,'end':end,'exact':quote,
                          'prefix':text[max(0,point-12):point],'suffix':text[point+len(quote):point+len(quote)+12]},
                'comment':'A test observation; not an instruction.'}]}
    def test_project_validates(self):
        self.assertGreaterEqual(ctp.validate_project(self.root)['frozen_snapshots'], 1)
    def test_no_public_editions_by_default(self):
        self.assertEqual(ctp.load_catalog(self.root), [])
    def test_snapshot_tampering_rejected(self):
        obj = copy.deepcopy(self.snap); obj['edition']['title'] = 'changed'
        with self.assertRaises(ctp.ProjectError): ctp.validate_snapshot(obj, self.revision)
    def test_duplicate_json_keys_rejected(self):
        p = self.root/'bad.json';p.write_text('{"a":1,"a":2}')
        with self.assertRaises(ctp.ProjectError):ctp.read_json(p)
    def test_nonfinite_json_rejected(self):
        p = self.root/'bad.json';p.write_text('{"a":NaN}')
        with self.assertRaises(ctp.ProjectError):ctp.read_json(p)
    def test_path_traversal_rejected(self):
        with self.assertRaises(ctp.ProjectError): ctp.source_file(self.work, '../project.json')
    def test_escaping_symlink_rejected(self):
        link=self.work/'source/escape.md';link.symlink_to(self.root/'README.md')
        with self.assertRaises(ctp.ProjectError):ctp.source_file(self.work,'source/escape.md')
    def test_sentence_and_paragraph_counts_not_constrained(self):
        p=self.work/'editions/en-modern/chapters/chapter-01.md'
        p.write_text('One sentence; the entire paragraph is newly written.\n\nAnother paragraph. A fragment.\n')
        ctp.load_work(self.work,'en-modern')
    def test_section_order_protected(self):
        self.ed['sections'].reverse();ctp.write_json(self.edpath,self.ed)
        with self.assertRaises(ctp.ProjectError):ctp.load_work(self.work,'en-modern')
    def test_missing_section_allowed_for_draft(self):
        self.ed['sections']=self.ed['sections'][:1];ctp.write_json(self.edpath,self.ed)
        w,e,_=ctp.load_work(self.work,'en-modern')
        self.assertEqual(ctp.check_inventory(w,e),['chapter-02'])
    def test_ready_cannot_have_missing_sections(self):
        self.ed['sections']=self.ed['sections'][:1];self.ed['status']='ready';ctp.write_json(self.edpath,self.ed)
        with self.assertRaises(ctp.ProjectError):ctp.load_work(self.work,'en-modern')
    def test_reader_catalogue_rejects_draft(self):
        self.record['audience']='readers';ctp.write_json(self.root/'catalog.json',{'schema_version':1,'revisions':[self.record]})
        with self.assertRaises(ctp.ProjectError):ctp.load_catalog(self.root)
    def test_catalogue_requires_explicit_approval_note(self):
        self.record['approval_note']='';ctp.write_json(self.root/'catalog.json',{'schema_version':1,'revisions':[self.record]})
        with self.assertRaises(ctp.ProjectError):ctp.load_catalog(self.root)
    def test_report_exact_quote(self):
        self.assertEqual(ctp.validate_review(self.report(),self.root)['annotations'],1)
    def test_report_detects_wrong_quote(self):
        report=self.report();report['annotations'][0]['anchor']['exact']='Reno'
        with self.assertRaises(ctp.ProjectError):ctp.validate_review(report,self.root)
    def test_report_multiple_chapters(self):
        report=self.report();other=self.report('chapter-02','Reno')['annotations'][0];other['id']='note-2'
        report['annotations'].append(other)
        self.assertEqual(ctp.validate_review(report,self.root)['annotations'],2)
    def test_section_observation_needs_no_quote(self):
        report=self.report();report['annotations'][0].update(scope='section',anchor=None)
        ctp.validate_review(report,self.root)
    def test_emoji_utf16_offsets(self):
        ctp.validate_review(self.report(quote='🚢'),self.root)
        self.assertEqual(ctp.utf16_slice('a🚢z',1,3),'🚢')
    def test_surrogate_boundary_rejected(self):
        with self.assertRaises(ctp.ProjectError):ctp.utf16_slice('a🚢z',1,2)
    def test_combining_characters_not_normalized(self):
        ctp.validate_review(self.report(quote='é'),self.root)
    def test_script_and_event_handler_rejected(self):
        for text in ('<script>alert(1)</script>', '<p onclick="alert(1)">text</p>', '<img src="x">', '<a href="javascript:alert(1)">x</a>'):
            with self.subTest(text=text),self.assertRaises(ctp.ProjectError):ctp.html_text(text)
    def test_embedded_json_cannot_close_script(self):
        encoded=ctp.js_data({'quote':'</script><script>alert(1)</script>'})
        self.assertNotIn('<',encoded)
    def test_unscoped_ids_rejected(self):
        with self.assertRaises(ctp.ProjectError):ctp.html_text('<p id="note-list">text</p>')
    @unittest.skipUnless(shutil.which('pandoc'),'Pandoc not installed')
    def test_wholesale_rewrite_preserves_old_report_and_snapshot(self):
        oldpath=ctp.snapshot_path(self.root,'demo-work','en-modern',self.revision)
        before=oldpath.read_bytes()
        p=self.work/'editions/en-modern/chapters/chapter-01.md';p.write_text('Entirely new prose, deliberately unlike the previous draft.\n')
        new_revision,_=ctp.freeze(self.work,'en-modern',self.root)
        self.assertNotEqual(new_revision,self.revision)
        self.assertEqual(oldpath.read_bytes(),before)
        ctp.validate_review(self.report(),self.root)
        moved=self.report();moved['revision']=new_revision
        with self.assertRaises(ctp.ProjectError):ctp.validate_review(moved,self.root)
    @unittest.skipUnless(shutil.which('pandoc'),'Pandoc not installed')
    def test_freeze_does_not_edit_source(self):
        p=self.work/'source/chapter-01.md';before=p.read_bytes()
        ctp.freeze(self.work,'en-modern',self.root)
        self.assertEqual(p.read_bytes(),before)
    @unittest.skipUnless(shutil.which('pandoc'),'Pandoc not installed')
    def test_render_footnotes_and_id_namespaces(self):
        rendered=ctp.render('A note.[^n]\n\n[^n]: Text.\n','test')
        self.assertIn('ctp-prose-test-',rendered)
        self.assertIn('Text.',ctp.html_text(rendered))
    @unittest.skipUnless(shutil.which('pandoc'),'Pandoc not installed')
    def test_build_demo_and_epub_package(self):
        out=ctp.build(self.root,True,True)
        self.assertNotIn('Read HTML',(out/'index.html').read_text())
        self.assertIn('Read and annotate',(out/'contribute/index.html').read_text())
        files=list(out.glob('revisions/*/*/*/edition.epub'));self.assertEqual(len(files),1)
        with zipfile.ZipFile(files[0]) as z:
            self.assertEqual(z.namelist()[0],'mimetype')
            self.assertEqual(z.read('mimetype'),b'application/epub+zip')
            for name in z.namelist():
                if name.endswith(('.xml','.opf','.xhtml','.ncx')):ET.fromstring(z.read(name))
        # These are packaging/XML checks, not EPUBCheck or device rendering.
    def test_unlisted_archive_still_builds(self):
        self.record['listed']=False
        ctp.write_json(self.root/'catalog.json',{'schema_version':1,'revisions':[self.record]})
        ctp.write_json(self.root/'examples/catalog.json',{'schema_version':1,'revisions':[]})
        out=ctp.build(self.root)
        self.assertEqual(len(list(out.glob('revisions/*/*/*/review.html'))),1)
        self.assertNotIn('Read and annotate',(out/'contribute/index.html').read_text())
    def test_normal_build_excludes_demonstration(self):
        out=ctp.build(self.root)
        self.assertFalse(list(out.glob('revisions/*')))
        self.assertFalse(ctp.read_json(out/'build-manifest.json')['demo'])

if __name__=='__main__':unittest.main()
