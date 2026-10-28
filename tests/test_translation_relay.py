"""Offline relay contract tests: no browser, queue or model calls."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import ctp as c
import translation_relay as r


class RelayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wid = 'gutenberg-36'
        self.wd = self.root/'books'/self.wid
        shutil.copytree(c.ROOT/'books'/self.wid, self.wd)
        # Source fixtures must not inherit local real guide/edition output.
        for name in ('editions','reference'):
            shutil.rmtree(self.wd/name,ignore_errors=True)
        shutil.copytree(c.ROOT/'prompts', self.root/'prompts')
        shutil.copy2(c.ROOT/'queue.json', self.root/'queue.json')
        shutil.copy2(c.ROOT/'project.json', self.root/'project.json')
        (self.root/'docs').mkdir()
        shutil.copy2(c.ROOT/'docs/editorial-policy.md', self.root/'docs/editorial-policy.md')
        self.base = self.wd/'editions/ja'
        self.nodes = ['n0001', 'n0004']

    def package(self, **kwargs):
        return r.package(self.root, self.wid, 'ja', self.nodes, 'test-model', language='ja', **kwargs)

    def result(self, job, edit=None, extra=None):
        with zipfile.ZipFile(job['package']) as z:
            manifest = json.loads(z.read('manifest.json'))
        obj = {k: manifest[k] for k in ('attempt','work','edition','language')}
        obj.update(schema_version=1, status='complete', nodes={})
        files = {'glossary.md': '# Glossary\n\nTest entries.', 'notes.md': '# Observations\n\nSynthetic fixture only.'}
        for nid, fields in manifest['fields'].items():
            obj['nodes'][nid] = {}
            for field in fields:
                obj['nodes'][nid][field] = 'Synthetic label' if field == 'label' else f'text/{nid}.md'
                if field == 'text':
                    files[f'text/{nid}.md'] = 'Synthetic translated body.'
        if edit:
            edit(obj)
        files['result.json'] = json.dumps(obj)
        files.update(extra or {})
        path = self.root/'result.zip'
        with zipfile.ZipFile(path, 'w') as z:
            for name, text in files.items():
                z.writestr(name, text)
        return path

    def accept(self, job, **kwargs):
        return r.import_result(self.root, job['attempt'], self.result(job), **kwargs)

    def test_package_is_local_ordered_and_explicit(self):
        self.nodes.reverse()
        job = self.package(context_nodes=['n0005'])
        self.assertFalse(job['submitted'])
        self.assertFalse(self.base.exists())
        with zipfile.ZipFile(job['package']) as z:
            m = json.loads(z.read('manifest.json'))
            self.assertEqual(list(m['fields']), ['n0001','n0004'])
            source = json.loads(z.read('source.json'))
            self.assertEqual(source[-1]['role'], 'context')
            self.assertIn('model: test-model', z.read('README.md').decode())
        self.assertNotEqual(job['attempt'], self.package()['attempt'])

    def test_unified_direct_return_imports_and_wrong_input_is_held(self):
        job=self.package(unified=True)
        with zipfile.ZipFile(job['package']) as z:
            manifest=json.loads(z.read('manifest.json'))
            self.assertEqual(manifest['schema_version'],2)
            self.assertEqual(manifest['job_sha256'],
                c.object_hash({k:v for k,v in manifest.items() if k!='job_sha256'}))
        nodes={};files={'glossary.md':'# Glossary\n\nSynthetic.',
                        'notes.md':'# Observations\n\nSynthetic.'}
        for nid,fields in manifest['fields'].items():
            nodes[nid]={}
            for field in fields:
                name='text/'+nid+('.label.md' if field=='label' else '.md')
                nodes[nid][field]=name
                files[name]='Synthetic label' if field=='label' else 'Synthetic prose.\n'
        result={'schema_version':2,'kind':'translation','adapter':'direct',
                'request_id':job['attempt'],'input_sha256':'0'*64,
                'status':'complete','model_label':'unknown','nodes':nodes,
                'auxiliary':{'glossary':'glossary.md','notes':'notes.md'}}
        path=self.root/'unified-result.zip'
        def write():
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('result.json',json.dumps(result))
                for name,body in files.items():z.writestr(name,body)
        write()
        with self.assertRaisesRegex(c.ProjectError,'another request'):
            r.import_result(self.root,job['attempt'],path)
        self.assertFalse(self.base.exists())
        result['input_sha256']=manifest['job_sha256'];write()
        outcome=r.import_result(self.root,job['attempt'],path,observed_model='unknown')
        self.assertEqual(outcome['status'],'draft')
        self.assertEqual((self.base/'text/n0004.md').read_text(),'Synthetic prose.\n')
        self.assertEqual((self.base/'glossary.md').read_text(),'# Glossary\n\nSynthetic.')
        self.assertEqual(c.read_json(self.base/'runs'/(outcome['run']+'.json'))['model_label'],
                         'unknown')

    def test_first_translation_preserves_preexisting_guide_directory(self):
        body=b'# Synthetic terminology guide\n'
        folder=self.base/'reference';folder.mkdir(parents=True)
        sha=c.digest(body);guide=folder/(sha+'.md');guide.write_bytes(body)
        c.write_json(folder/'current.json',{'sha256':sha})
        job=self.package()
        self.assertFalse((self.base/'edition.json').exists())
        self.accept(job)
        self.assertEqual(guide.read_bytes(),body)
        self.assertEqual(c.read_json(folder/'current.json'),{'sha256':sha})
        c.load_work(self.wd,'ja')

    def test_ordered_materials_make_exact_private_preview_without_changing_return_zip(self):
        (self.root/'docs/editorial-policy.md').write_text(
            '# Editorial policy\n\nTranslate into {{target_language}}.\n')
        folder=self.wd/'reference';folder.mkdir(parents=True)
        first=b'# Synthetic work reference\n\nWork context.\n'
        sha=c.digest(first);(folder/(sha+'.md')).write_bytes(first)
        c.write_json(folder/'current.json',{'sha256':sha})
        from materials import discover
        items={item['id']:item for item in discover(self.root)}
        ids=['guide.work.'+self.wid,'policy.editorial']
        selected=[ident+'@'+items[ident]['sha256'] for ident in ids]
        job=self.package(materials=selected)
        with zipfile.ZipFile(job['package']) as z:
            preview=z.read('assembled-input.md')
            manifest=json.loads(z.read('manifest.json'))
            self.assertEqual(manifest['materials'],
                             [{'id':ident,'sha256':items[ident]['sha256']} for ident in ids])
            self.assertEqual(manifest['assembled_input_sha256'],c.digest(preview))
            self.assertIn('Synthetic work reference',preview.decode())
            self.assertIn('Translate into Japanese.',preview.decode())
            self.assertLess(preview.index(b'Synthetic work reference'),
                            preview.index(b'Editorial policy'))
        self.assertEqual(Path(job['preview']).read_bytes(),preview)
        self.accept(job)
        self.assertTrue((self.base/'edition.json').exists())

    def test_import_records_exact_inputs_and_draft(self):
        job = self.package()
        old_notes = (self.wd/'notes.md').read_text()
        (self.wd/'notes.md').write_text('Changed after submission')
        outcome = self.accept(job)
        self.assertEqual(outcome['status'], 'draft')
        self.assertTrue(outcome['missing'])
        _, ed, _ = c.load_work(self.wd, 'ja')
        run = c.read_json(self.base/'runs'/(outcome['run']+'.json'))
        c.validate_run(run)
        self.assertEqual(run['model_label'], 'unknown')
        self.assertEqual(run['relay']['model_requested'], 'test-model')
        self.assertEqual(next(v['text'] for v in run['inputs'] if v['path']=='work-notes.md'), old_notes)
        self.assertTrue(any(v['path'].endswith('edition.json') for v in run['outputs']))
        self.assertTrue((self.base/'glossary.md').exists())
        self.assertEqual(ed['production']['runs'], [outcome['run']])
        with self.assertRaisesRegex(c.ProjectError, 'already imported'):
            self.accept(job)

    def test_import_can_freeze_with_provenance(self):
        job = self.package(); outcome = self.accept(job)
        revision, path = c.freeze(self.wd, 'ja', self.root)
        frozen = c.read_json(path)
        c.validate_snapshot(frozen, revision)
        self.assertEqual(frozen['production_runs'][0]['id'], outcome['run'])
        self.assertTrue(frozen['missing'])
        self.assertEqual(frozen['edition']['status'], 'draft')

    def test_cli_package_and_import_dispatch(self):
        import contextlib
        import io
        output = io.StringIO()
        with patch.object(c, 'ROOT', self.root), patch.object(sys, 'argv',
                ['ctp', 'relay-package', self.wid, 'ja', '--language', 'ja',
                 '--model', 'test-model', '--node', 'n0001', '--node', 'n0004']), contextlib.redirect_stdout(output):
            self.assertEqual(c.main(), 0)
        job = json.loads(output.getvalue())
        path = self.result(job)
        with patch.object(c, 'ROOT', self.root), patch.object(sys, 'argv',
                ['ctp', 'relay-import', job['attempt'], str(path)]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(c.main(), 0)
        self.assertTrue((self.base/'edition.json').exists())

    def test_retranslation_preserves_previous_edition_and_runs(self):
        first = self.package(); self.accept(first)
        before = r.inventory(self.base)
        second = self.package(); self.accept(second)
        backup = self.root/'private/relay'/second['attempt']/'edition-before'
        self.assertEqual(r.inventory(backup), before)
        self.assertEqual(len(c.read_json(self.base/'edition.json')['production']['runs']), 2)

    def test_interrupted_direct_import_restores_only_verified_prior_edition(self):
        self.accept(self.package())
        before=r.inventory(self.base)
        second=self.package()
        backup=self.root/'private/relay'/second['attempt']/'edition-before'
        os.rename(self.base,backup)
        restored=r.recover_interrupted_import(self.root,second['attempt'])
        self.assertEqual(restored['restored'],str(self.base.resolve()))
        self.assertEqual(r.inventory(self.base),before)
        self.assertFalse(backup.exists())

        third=self.package()
        backup=self.root/'private/relay'/third['attempt']/'edition-before'
        os.rename(self.base,backup)
        self.base.mkdir()
        (self.base/'notes.md').write_text('Intervening human edit')
        with self.assertRaisesRegex(c.ProjectError,'Edition path exists'):
            r.recover_interrupted_import(self.root,third['attempt'])
        self.assertEqual((self.base/'notes.md').read_text(),'Intervening human edit')
        self.assertEqual(r.inventory(backup),before)
        shutil.rmtree(self.base)
        (backup/'notes.md').write_text('Corrupted backup')
        with self.assertRaisesRegex(c.ProjectError,'backup differs'):
            r.recover_interrupted_import(self.root,third['attempt'])
        self.assertFalse(self.base.exists())

    def test_rejects_stale_edition(self):
        self.accept(self.package())
        job = self.package()
        (self.base/'glossary.md').write_text('New human decision')
        before = r.inventory(self.base)
        with self.assertRaisesRegex(c.ProjectError, 'Edition changed'):
            self.accept(job)
        self.assertEqual(r.inventory(self.base), before)

    def test_rejects_source_change(self):
        job = self.package()
        p = self.wd/'work.json'; obj = c.read_json(p); obj['author'] += ' changed'; c.write_json(p,obj)
        with self.assertRaisesRegex(c.ProjectError, 'Source changed'):
            self.accept(job)
        self.assertFalse(self.base.exists())

    def test_rejects_tampered_request(self):
        job = self.package()
        with open(job['package'], 'ab') as f:
            f.write(b'changed')
        with self.assertRaisesRegex(c.ProjectError, 'package changed'):
            self.accept(job)

    def test_incomplete_wrong_identity_and_missing_fields_do_not_write(self):
        job = self.package()
        edits = [lambda x: x.update(status='incomplete'), lambda x: x.update(attempt='wrong'),
                 lambda x: x['nodes'].pop('n0004'), lambda x: x['nodes']['n0001'].pop('label'),
                 lambda x: x['nodes']['n0004'].update(label='')]
        for edit in edits:
            with self.subTest(edit=edit):
                with self.assertRaises(c.ProjectError):
                    r.import_result(self.root, job['attempt'], self.result(job, edit))
                self.assertFalse(self.base.exists())

    def test_unsafe_extra_and_duplicate_members_rejected(self):
        job = self.package()
        for name in ('../escape.md', '/escape.md', 'extra.md'):
            with self.assertRaises(c.ProjectError):
                r.import_result(self.root, job['attempt'], self.result(job, extra={name:'bad'}))
        path = self.result(job)
        with zipfile.ZipFile(path, 'a') as z:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                z.writestr('glossary.md','duplicate')
        with self.assertRaisesRegex(c.ProjectError, 'Duplicate'):
            r.import_result(self.root, job['attempt'], path)
        self.assertFalse(self.base.exists())

    def test_body_path_cannot_escape(self):
        job = self.package()
        path = self.result(job, lambda x: x['nodes']['n0004'].update(text='../escape'))
        with self.assertRaises(c.ProjectError):
            r.import_result(self.root, job['attempt'], path)

    def test_readiness_and_selection_guards(self):
        for nodes in (['n9999'], ['n0001','n0001']):
            self.nodes = nodes
            with self.assertRaises(c.ProjectError):
                self.package()
        self.nodes = ['n0001']
        (self.wd/'structure.json').unlink()
        with self.assertRaises(c.ProjectError):
            self.package()

    def test_held_source_rejected(self):
        p = self.wd/'rights.json'; obj=c.read_json(p); obj['status']='held'; obj['eligible']=False; c.write_json(p,obj)
        with self.assertRaises(c.ProjectError):
            self.package()

    def test_failed_provenance_leaves_edition_untouched(self):
        self.accept(self.package()); job=self.package(); before=r.inventory(self.base)
        with patch.object(c, 'record_run', side_effect=c.ProjectError('failure')):
            with self.assertRaises(c.ProjectError):
                self.accept(job)
        self.assertEqual(r.inventory(self.base), before)

    def test_install_failure_rolls_back(self):
        self.accept(self.package()); job=self.package(); before=r.inventory(self.base)
        rename = r.os.rename
        def fail_stage(src, dest):
            if 'import-' in str(src):
                raise OSError('simulated install failure')
            return rename(src,dest)
        with patch.object(r.os, 'rename', side_effect=fail_stage):
            with self.assertRaises(OSError):
                self.accept(job)
        self.assertEqual(r.inventory(self.base), before)

    def test_symlink_and_size_limit(self):
        path=self.root/'unsafe.zip'
        info=zipfile.ZipInfo('link'); info.create_system=3; info.external_attr=0o120777 << 16
        with zipfile.ZipFile(path,'w') as z:
            z.writestr(info,'target')
        with self.assertRaises(c.ProjectError): r.read_zip(path)
        job=self.package()
        with patch.object(r, 'MAX_BYTES', 1):
            with self.assertRaises(c.ProjectError): r.read_zip(Path(job['package']))


if __name__ == '__main__':
    unittest.main()
