"""Material discovery, version pinning and assembled-input boundaries."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp as c
import materials


class MaterialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        def put(name,text):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text,encoding='utf-8');return path
        self.put=put
        put('queue.json',json.dumps({'schema_version':1,'works':[
            {'id':'gutenberg-36','targets':['ja']}]}))
        put('docs/editorial-policy.md','# Editorial policy\n\nProject baseline.\n')
        put('prompts/translation/contemporary.md','# Contemporary recipe\n\nTranslate.\n')
        put('books/gutenberg-36/notes.md','# Work notes\n\nSource facts.\n')
        guide='# Guide\n\nDraft terminology.\n'
        self.guide_hash=hashlib.sha256(guide.encode()).hexdigest()
        put('books/gutenberg-36/editions/ja/reference/'+self.guide_hash+'.md',guide)
        put('books/gutenberg-36/editions/ja/reference/current.json',
            json.dumps({'sha256':self.guide_hash}))
        put('materials/files/ja.md','# Japanese style\n\nTarget instructions.\n')
        put('materials/manifest.json',json.dumps({'schema_version':1,'entries':[
            {'id':'style.ja','path':'materials/files/ja.md','title':'Japanese style',
             'description':'Language guidance','scope':'target_language',
             'kind':'instruction','work':None,'target':'ja','tags':['style']}
        ]}))

    def test_four_scopes_and_metadata_only(self):
        rows=materials.discover(self.root)
        self.assertEqual({'general','target_language','work','work_target'},
                         {r['scope'] for r in rows})
        public=materials.public_metadata(self.root)
        self.assertEqual(public,[])
        self.assertTrue(all('path' not in r and 'text' not in r for r in public))
        self.assertTrue(all(materials.applicable(r,'gutenberg-36','ja') for r in public))
        self.assertFalse(materials.applicable(next(r for r in rows if r['id']=='style.ja'),
                                              'gutenberg-36','en'))

    def test_public_manifest_excludes_untracked_private_guide(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        subprocess.run(['git','-C',str(self.root),'add','docs/editorial-policy.md',
                        'materials/files/ja.md',
                        'books/gutenberg-36/editions/ja/reference/'+self.guide_hash+'.md'],check=True)
        for key,value in [('user.name','Fixture'),('user.email','fixture@example.invalid')]:
            subprocess.run(['git','-C',str(self.root),'config',key,value],check=True)
        subprocess.run(['git','-C',str(self.root),'commit','-qm','Approved fixture files'],check=True)
        public=materials.public_metadata(self.root)
        self.assertEqual({row['id'] for row in public},{'policy.editorial','style.ja'})
        self.assertTrue(all('path' not in row and 'text' not in row for row in public))
        style=self.root/'materials/files/ja.md';saved=style.read_bytes()
        style.write_text('# Uncommitted draft title\n')
        self.assertNotIn('style.ja',{row['id'] for row in materials.public_metadata(self.root)})
        style.write_bytes(saved)
        subprocess.run(['git','-C',str(self.root),'add',
                        'books/gutenberg-36/editions/ja/reference/current.json'],check=True)
        self.assertNotIn('guide.target.gutenberg-36.ja',
                         {row['id'] for row in materials.public_metadata(self.root)})
        subprocess.run(['git','-C',str(self.root),'commit','-qm','Approved guide pointer'],check=True)
        self.assertIn('guide.target.gutenberg-36.ja',
                      {row['id'] for row in materials.public_metadata(self.root)})

    def test_order_and_immutable_version_resolution(self):
        rows={r['id']:r for r in materials.discover(self.root)}
        selected=[{'id':i,'sha256':rows[i]['sha256']}
                  for i in ('style.ja','guide.target.gutenberg-36.ja')]
        got=materials.resolve(self.root,'gutenberg-36','ja',selected)
        self.assertEqual([x['id'] for x in got],[x['id'] for x in selected])
        self.assertEqual(got[1]['sha256'],self.guide_hash)
        preview=materials.assembled_translation('Base',got,[{'id':'n0001','fields':{'label':'Title'}}],
                                                {'work_notes':'Notes'}, {},'ZIP contract')
        self.assertLess(preview.index('Japanese style'),preview.index('## Material 2'))
        self.assertLess(preview.index('## Material 2'),preview.index('Selected source fields'))
        self.assertIn('Fixed return contract\nZIP contract',preview)

        old='# Older guide\n\nPrior wording.\n'
        old_hash=hashlib.sha256(old.encode()).hexdigest()
        self.put('books/gutenberg-36/editions/ja/reference/'+old_hash+'.md',old)
        selected[1]['sha256']=old_hash
        prior=materials.resolve(self.root,'gutenberg-36','ja',selected)[1]
        self.assertEqual(prior['text'],old)
        self.assertEqual(prior['title'],'Older guide')

    def test_stale_duplicate_and_wrong_target_are_rejected(self):
        rows={r['id']:r for r in materials.discover(self.root)}
        ref={'id':'guide.target.gutenberg-36.ja','sha256':rows['guide.target.gutenberg-36.ja']['sha256']}
        with self.assertRaises(c.ProjectError):materials.resolve(self.root,'gutenberg-36','en',[ref])
        with self.assertRaises(c.ProjectError):materials.resolve(self.root,'gutenberg-36','ja',[ref,ref])
        with self.assertRaises(c.ProjectError):materials.resolve(self.root,'gutenberg-36','ja',
            [{'id':ref['id'],'sha256':'0'*64}])
        self.put('books/gutenberg-36/editions/ja/reference/'+self.guide_hash+'.md','# Changed\n')
        with self.assertRaises(c.ProjectError):materials.discover(self.root)

    def test_built_admin_contains_only_safe_material_metadata(self):
        from site_builder import admin
        root=c.ROOT
        html=admin(root,c.read_json(root/'project.json'),(root/'site/site.css').read_text())
        match=re.search(r'<script id="admin-data" type="application/json">(.*?)</script>',
                        html,re.S)
        self.assertIsNotNone(match)
        data=json.loads(match.group(1))
        self.assertTrue(data['materials'])
        self.assertTrue(all('text' not in row and 'path' not in row
                            for row in data['materials']))
        self.assertIn('material-pools',html)


if __name__=='__main__':unittest.main()
