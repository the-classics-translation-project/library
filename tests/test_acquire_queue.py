"""Automatic US/Japan source admission, evidence integrity and safe queue writes."""
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from legacy_v1 import read_json, write_json, digest, ProjectError
from source_import import prepare
from source_rights import (assess_metadata, parse_metadata, check_package, japan_expiry_bound,
                           fetch_metadata, EXTENSION_DATE, WARTIME_DAYS)
from acquire_queue import acquire_queued, validate_record, stage_acquisitions
from intake import queue_status, task_brief

AS_OF = date(2026, 1, 1)


def metadata(eid=36, death='1851', publication='$aLondon :$bPublisher, $c1818.',
             rights='Public domain in the USA.', credit='', extra='', language='en', name='Writer, Example'):
    return f'''<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:pg="http://www.gutenberg.org/2009/pgterms/" xmlns:dc="http://purl.org/dc/terms/"
      xmlns:rel="http://id.loc.gov/vocabulary/relators/">
      <pg:ebook rdf:about="ebooks/{eid}"><dc:title>Test Book</dc:title>
      <dc:rights>{escape(rights)}</dc:rights><dc:creator><pg:agent><pg:name>{escape(name)}</pg:name>
      <pg:deathdate>{escape(death)}</pg:deathdate></pg:agent></dc:creator>
      <dc:language><rdf:Description><rdf:value>{language}</rdf:value></rdf:Description></dc:language>
      <dc:type><rdf:Description><rdf:value>Text</rdf:value></rdf:Description></dc:type>
      <dc:issued>2004-10-01</dc:issued><pg:marc260>{escape(publication)}</pg:marc260>
      <pg:marc508>{escape(credit)}</pg:marc508>{extra}</pg:ebook></rdf:RDF>'''.encode()


def package(eid=36, body='A synthetic test paragraph.', author='Example Writer', title='Test Book'):
    return (f'The Project Gutenberg eBook\r\nTitle: {title}\r\nAuthor: {author}\r\n'
            f'Release date: October 1, 2004 [eBook #{eid}]\r\nLanguage: English\r\n'
            '*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***\r\n\r\n'
            f'{body}\r\n\r\n*** END OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***\r\n'
            'Project Gutenberg license retained here.\r\n').encode()


class RightsTests(unittest.TestCase):
    def assess(self, **kwargs):
        return assess_metadata(parse_metadata(metadata(**kwargs), 36), AS_OF)

    def test_named_lifetime_work_passes(self):
        result = self.assess()
        self.assertTrue(result['eligible'])
        self.assertEqual(result['countries']['US']['status'], 'pass')
        self.assertEqual(result['countries']['JP']['status'], 'pass')

    def test_permission_only_us_work_is_held(self):
        self.assertFalse(self.assess(rights='Copyrighted. Read the copyright notice inside this book for details.')['eligible'])

    def test_missing_or_approximate_death_is_held(self):
        for death in ('', '1851?', 'circa 1851', '0', '3000'):
            with self.subTest(death=death): self.assertFalse(self.assess(death=death)['eligible'])

    def test_anonymous_or_collective_author_is_held(self):
        for name in ('Anonymous', 'Various', 'Unknown author'):
            with self.subTest(name=name): self.assertFalse(self.assess(name=name)['eligible'])

    def test_release_date_never_substitutes_for_source_publication(self):
        result = self.assess(publication='')
        self.assertFalse(result['eligible'])
        self.assertIn('source_publication_missing', [r['code'] for r in result['reasons']])
        raw = metadata().replace(b'<pg:marc260>$aLondon :$bPublisher, $c1818.</pg:marc260>', b'')
        result = assess_metadata(parse_metadata(raw, 36), AS_OF)
        self.assertIn('source_publication_missing', [r['code'] for r in result['reasons']])

    def test_ambiguous_publication_is_held(self):
        for value in ('$c[1818?]', '$c1818-1831.', '$c1818; 2000.', '$c1818.$c1831.'):
            with self.subTest(value=value): self.assertFalse(self.assess(publication=value)['eligible'])

    def test_later_or_posthumous_source_is_held(self):
        self.assertFalse(self.assess(publication='$c1950.')['eligible'])
        self.assertFalse(self.assess(death='2000', publication='$c1980.')['eligible'])

    def test_non_english_source_is_held(self):
        self.assertFalse(self.assess(language='fr')['eligible'])

    def test_every_contributor_is_checked(self):
        extra = '<rel:trl><pg:agent><pg:name>Translator, Example</pg:name><pg:deathdate>1980</pg:deathdate></pg:agent></rel:trl>'
        result = self.assess(extra=extra)
        self.assertFalse(result['eligible'])
        self.assertEqual(len(result['countries']['JP']['contributor_terms']), 2)

    def test_generic_unknown_or_unresolved_contributor_is_held(self):
        for extra in ('<dc:contributor rdf:resource="external-agent"/>',
                      '<rel:zzz><pg:agent><pg:name>Person</pg:name><pg:deathdate>1800</pg:deathdate></pg:agent></rel:zzz>',
                      '<rel:edt><pg:agent><pg:name>Editor</pg:name></pg:agent></rel:edt>'):
            with self.subTest(extra=extra): self.assertFalse(self.assess(extra=extra)['eligible'])

    def test_separate_revision_or_introduction_is_held(self):
        for credit in ('Revised by Modern Person', 'Introduction by New Writer', 'Translated by Someone'):
            with self.subTest(credit=credit): self.assertFalse(self.assess(credit=credit)['eligible'])
        self.assertTrue(self.assess(credit='Produced by the Online Distributed Proofreading Team')['eligible'])

    def test_wartime_upper_bound_and_non_revival(self):
        old, basis = japan_expiry_bound(1946)
        self.assertEqual(old, date(1996, 12, 31) + timedelta(days=4180))
        self.assertLess(old, EXTENSION_DATE)
        self.assertIn('no revival', basis)
        # A term still covered by the allowance at extension must receive life+70.
        later, basis = japan_expiry_bound(1957)
        self.assertEqual(later, date(2027, 12, 31) + timedelta(days=WARTIME_DAYS))
        self.assertNotIn('no revival', basis)

    def test_expiry_day_is_not_admitted_early(self):
        facts = parse_metadata(metadata(death='1957'), 36)
        bound, _ = japan_expiry_bound(1957)
        self.assertFalse(assess_metadata(facts, bound)['eligible'])
        self.assertTrue(assess_metadata(facts, bound + timedelta(days=1))['eligible'])

    def test_xml_identity_and_entities_are_rejected(self):
        with self.assertRaises(ProjectError): parse_metadata(metadata(eid=99), 36)
        with self.assertRaises(ProjectError): parse_metadata(b'<!DOCTYPE rdf [<!ENTITY x "test">]>' + metadata(), 36)

    def test_metadata_external_redirect_is_rejected(self):
        with patch('source_rights.urlopen') as opener:
            opener.return_value.__enter__.return_value.geturl.return_value = 'https://example.com/36.rdf'
            with self.assertRaises(ProjectError): fetch_metadata(36)

    def test_package_identity_and_added_matter(self):
        facts = parse_metadata(metadata(), 36)
        self.assertEqual(check_package(package(), 36, facts), [])
        for raw in (package(eid=99), package(author='Different Person'), package(title='Other Book'),
                    package(body='Introduction by Modern Writer'), package(body='Copyright 2020'),
                    package().replace(b'Language: English', b'Copyright: Modern Publisher\r\nLanguage: English'),
                    package(title='Book Test'),
                    package(body="[Transcriber's Note: Additional explanation]"),
                    package().replace(b'END OF THE', b'START OF THE')):
            with self.subTest(raw=raw[:80]): self.assertTrue(check_package(raw, 36, facts))


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

    def fake_metadata(self, eid):
        raw = metadata(eid=eid)
        return raw, {'requested_url': f'https://www.gutenberg.org/ebooks/{eid}.rdf',
                     'resolved_url': f'https://www.gutenberg.org/ebooks/{eid}.rdf', 'sha256': digest(raw)}

    def fake_fetch(self, output, eid):
        source = output/'download.txt'
        source.write_bytes(package(eid))
        dest = output/'books'/f'gutenberg-{eid}'/'acquisition'
        blocks = prepare(source, dest)
        write_json(dest/'provenance.json', {'schema_version': 1, 'provider': 'gutenberg', 'ebook_id': eid,
            'requested_url': f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt',
            'resolved_url': f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt',
            'raw_sha256': blocks['raw_sha256'], 'source_edition_verified': False, 'rights_checked': False})

    def acquire(self, metadata_fetch=None, source_fetch=None):
        with patch('acquire_queue.fetch_metadata', side_effect=metadata_fetch or self.fake_metadata), \
             patch('acquire_queue.fetch_gutenberg', side_effect=source_fetch or self.fake_fetch):
            return acquire_queued(self.root, self.output, AS_OF)

    def test_pass_saves_exact_bytes_evidence_and_is_idempotent(self):
        report = self.acquire()
        self.assertEqual(len(report['acquired']), 2)
        wd = self.root/'books/gutenberg-36'
        self.assertEqual((wd/'acquisition/acquired.txt').read_bytes(), package())
        record = validate_record(wd, 36)
        self.assertTrue(record['eligible'])
        self.assertFalse((wd/'work.json').exists())
        self.assertFalse((self.root/'catalog.json').exists())
        before = (wd/'rights.json').read_bytes()
        with patch('acquire_queue.fetch_metadata') as fetch:
            again = acquire_queued(self.root, self.output, AS_OF)
        self.assertEqual(len(again['skipped']), 2)
        fetch.assert_not_called()
        self.assertEqual((wd/'rights.json').read_bytes(), before)

    def test_hold_records_reason_without_downloading(self):
        def missing(eid):
            raw, info = self.fake_metadata(eid)
            raw = raw.replace(b'<pg:deathdate>1851</pg:deathdate>', b'')
            return raw, dict(info, sha256=digest(raw))
        with patch('acquire_queue.fetch_gutenberg') as fetch:
            with patch('acquire_queue.fetch_metadata', side_effect=missing):
                report = acquire_queued(self.root, self.output, AS_OF)
        fetch.assert_not_called()
        self.assertEqual(len(report['held']), 2)
        self.assertFalse((self.root/'books/gutenberg-36/acquisition').exists())
        self.assertEqual(validate_record(self.root/'books/gutenberg-36', 36)['status'], 'held')
        self.assertEqual(queue_status(self.root)[0]['stage'], 'source on hold')
        self.assertIn('exact death year', task_brief(self.root))

    def test_partial_network_failure_preserves_success_and_retry_succeeds(self):
        def fetch(output, eid):
            if eid == 36: raise OSError('provider unavailable')
            self.fake_fetch(output, eid)
        report = self.acquire(source_fetch=fetch)
        self.assertEqual(report['acquired'], ['gutenberg-41445'])
        self.assertEqual(report['failed'][0]['work'], 'gutenberg-36')
        self.assertEqual(validate_record(self.root/'books/gutenberg-36', 36)['status'], 'held')
        again = self.acquire()
        self.assertEqual(again['acquired'], ['gutenberg-36'])
        self.assertEqual(again['skipped'], ['gutenberg-41445'])

    def test_metadata_network_error_is_a_durable_hold(self):
        def fail(eid): raise OSError('metadata unavailable')
        report = self.acquire(metadata_fetch=fail)
        self.assertEqual(len(report['failed']), 2)
        self.assertEqual(validate_record(self.root/'books/gutenberg-36', 36)['reasons'][0]['code'], 'acquisition_error')

    def test_unchanged_hold_does_not_rewrite_records(self):
        def fail(eid): raise OSError('metadata unavailable')
        self.acquire(metadata_fetch=fail)
        before = (self.root/'books/gutenberg-36/rights.json').read_bytes()
        again = self.acquire(metadata_fetch=fail)
        self.assertEqual(again['changed'], [])
        self.assertEqual((self.root/'books/gutenberg-36/rights.json').read_bytes(), before)

    def test_malformed_metadata_is_held(self):
        def broken(eid):
            raw, info = self.fake_metadata(eid)
            raw = b'not XML'
            return raw, dict(info, sha256=digest(raw))
        report = self.acquire(metadata_fetch=broken)
        self.assertEqual(len(report['failed']), 2)
        validate_record(self.root/'books/gutenberg-36', 36)

    def test_changed_package_id_or_contributions_never_reach_books(self):
        def bad(output, eid):
            self.fake_fetch(output, eid)
            dest = output/'books'/f'gutenberg-{eid}'/'acquisition'
            from shutil import rmtree
            rmtree(dest)
            source = output/'bad.txt'
            source.write_bytes(package(eid, body='Revised by Someone Else'))
            blocks = prepare(source, dest)
            write_json(dest/'provenance.json', {'ebook_id': eid, 'raw_sha256': blocks['raw_sha256'],
                'requested_url': f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt',
                'resolved_url': f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt'})
        report = self.acquire(source_fetch=bad)
        self.assertEqual(report['acquired'], [])
        self.assertFalse((self.root/'books/gutenberg-36/acquisition').exists())
        validate_record(self.root/'books/gutenberg-36', 36)

    def test_saved_metadata_or_raw_tampering_is_detected(self):
        self.acquire()
        wd = self.root/'books/gutenberg-36'
        raw = wd/'rights-metadata.rdf'
        original = raw.read_bytes()
        raw.write_bytes(original + b'changed')
        with self.assertRaises(ProjectError): validate_record(wd, 36)
        raw.write_bytes(original)
        (wd/'acquisition/acquired.txt').write_text('changed')
        with self.assertRaises(ProjectError): validate_record(wd, 36)
        report = self.acquire()
        self.assertTrue(report['failed'])
        self.assertEqual((wd/'acquisition/acquired.txt').read_text(), 'changed')

    def test_fabricated_country_pass_does_not_admit_a_held_source(self):
        self.acquire()
        wd = self.root/'books/gutenberg-36'
        record = read_json(wd/'rights.json')
        record['countries']['JP']['contributor_terms'][0]['death_year'] = 1700
        write_json(wd/'rights.json', record)
        with self.assertRaises(ProjectError): validate_record(wd, 36)

    def test_no_network_call_for_an_invalid_queue(self):
        queue = read_json(self.root/'queue.json')
        queue['works'][0]['id'] = '../../outside'
        write_json(self.root/'queue.json', queue)
        with patch('acquire_queue.fetch_metadata') as fetch:
            with self.assertRaises(ProjectError): acquire_queued(self.root, self.output, AS_OF)
        fetch.assert_not_called()

    def test_exact_staging_excludes_unrelated_files_and_held_text(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        report = self.acquire()
        wd = self.root/'books/gutenberg-36'
        (wd/'unrelated.txt').write_text('Never stage me')
        stage_acquisitions(self.root, self.output)
        names = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=self.root, text=True)
        self.assertIn('acquisition/acquired.txt', names)
        self.assertNotIn('unrelated.txt', names)
        self.assertNotIn('project.json', names)
        self.assertNotIn('build/', names)
        self.assertEqual(len(report['acquired']), 2)

    def test_reassessing_complete_metadata_releases_a_hold(self):
        def incomplete(eid):
            raw, info = self.fake_metadata(eid)
            raw = raw.replace(b'<pg:deathdate>1851</pg:deathdate>', b'')
            return raw, dict(info, sha256=digest(raw))
        self.assertEqual(len(self.acquire(metadata_fetch=incomplete)['held']), 2)
        self.assertEqual(len(self.acquire()['acquired']), 2)
        self.assertTrue(validate_record(self.root/'books/gutenberg-36', 36)['eligible'])

    def test_existing_manual_source_is_held_and_not_staged(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.fake_fetch(self.root, 36)
        report = self.acquire()
        wd = self.root/'books/gutenberg-36'
        self.assertEqual((wd/'acquisition/acquired.txt').read_bytes(), package())
        self.assertEqual(read_json(wd/'rights.json')['reasons'][0]['code'], 'existing_source_unassessed')
        self.assertFalse(report['failed'])
        stage_acquisitions(self.root, self.output)
        names = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=self.root, text=True)
        self.assertIn('books/gutenberg-36/rights.json', names)
        self.assertNotIn('books/gutenberg-36/acquisition/', names)
        self.assertIn('books/gutenberg-41445/acquisition/acquired.txt', names)

    def test_held_first_work_does_not_block_actionable_task(self):
        def missing_first(eid):
            raw, info = self.fake_metadata(eid)
            if eid == 36: raw = raw.replace(b'1851', b'')
            return raw, dict(info, sha256=digest(raw))
        self.acquire(metadata_fetch=missing_first)
        brief = task_brief(self.root)
        self.assertIn('Work: `gutenberg-41445`', brief)
        self.assertIn('## Sources on hold', brief)



class CitedAdmissionTests(unittest.TestCase):
    """The original Gutenberg RDF records are fixtures; no internet required."""
    ROOT = Path(__file__).resolve().parents[1]

    def supplement(self, ebook_id):
        return read_json(self.ROOT/'books'/f'gutenberg-{ebook_id}'/'admission-evidence.json')

    def test_real_saved_gutenberg_metadata_with_documented_evidence(self):
        for eid in (36, 41445):
            with self.subTest(ebook_id=eid):
                raw = (self.ROOT/'books'/f'gutenberg-{eid}'/'rights-metadata.rdf').read_bytes()
                facts = parse_metadata(raw, eid)
                self.assertFalse(assess_metadata(facts, AS_OF)['eligible'])
                accepted = assess_metadata(facts, AS_OF, self.supplement(eid))
                self.assertTrue(accepted['eligible'], accepted['reasons'])
                self.assertEqual(accepted['countries']['US']['status'], 'pass')
                self.assertEqual(accepted['countries']['JP']['status'], 'pass')

    def test_legacy_holds_still_replay_with_new_supplements_present(self):
        for eid in (36, 41445):
            with self.subTest(ebook_id=eid):
                record = validate_record(self.ROOT/'books'/f'gutenberg-{eid}', eid)
                self.assertEqual(record['rule_version'], 'gutenberg-us-jp-v1')
                self.assertEqual(record['status'], 'held')

    def test_external_publication_only_fixes_the_missing_field(self):
        from source_rights import validate_supplement
        extra = self.supplement(36)
        facts = parse_metadata(metadata(publication=''), 36)
        # This synthetic fixture has a different title from the cited first edition.
        self.assertIn('publication_evidence_title_mismatch',
                      [r['code'] for r in assess_metadata(facts, AS_OF, extra)['reasons']])
        copy = __import__('copy').deepcopy(extra)
        copy['publication']['title'] = 'Test Book'
        copy['publication']['year'] = 1818
        self.assertTrue(assess_metadata(facts, AS_OF, copy)['eligible'])
        facts['rights'] = ['Copyrighted']
        self.assertFalse(assess_metadata(facts, AS_OF, copy)['eligible'])
        facts['rights'] = ['Public domain in the USA.']
        facts['publication_statements'] = ['$aLondon :$c1910.']
        self.assertIn('publication_evidence_conflict',
                      [r['code'] for r in assess_metadata(facts, AS_OF, copy)['reasons']])
        copy['publication']['year'] = 2020
        with self.assertRaises(ProjectError):
            validate_supplement(copy, 36)

    def test_revision_credit_and_exact_photo_reprint_note(self):
        evidence = self.supplement(41445)
        credit = 'Produced by volunteers\nRevised by Richard Tonsing.'
        rawmeta = metadata(eid=41445, credit=credit)
        facts = parse_metadata(rawmeta, 41445)
        self.assertFalse(assess_metadata(facts, AS_OF)['eligible'])
        self.assertTrue(assess_metadata(facts, AS_OF, evidence)['eligible'])
        original = package(eid=41445, body=(evidence['transcriber_note']['text'] +
                    '\nA synthetic historical paragraph.'))
        original = original.replace(b'Language: English',
                     b'Language: English\r\nCredits: Produced by volunteers\r\n Revised by Richard Tonsing.')
        self.assertTrue(check_package(original, 41445, facts))
        self.assertEqual(check_package(original, 41445, facts, evidence), [])
        self.assertTrue(check_package(original.replace(b'Revised by Richard Tonsing.',
                                                      b'Revised by Another Person.'),
                                      41445, facts, evidence))
        self.assertTrue(check_package(original.replace(b'A synthetic historical paragraph.',
                                                      b'Introduction by a Modern Writer.'),
                                      41445, facts, evidence))
        self.assertTrue(check_package(original.replace(b'A synthetic historical paragraph.',
                                                      b'Copyright 2026 Modern Editor.'),
                                      41445, facts, evidence))
        self.assertTrue(check_package(original.replace('photo-reprint'.encode(), b'new adaptation'),
                                      41445, facts, evidence))

    def test_extra_metadata_revision_still_blocks_an_exception(self):
        evidence = self.supplement(41445)
        facts = parse_metadata(metadata(eid=41445,
                             credit='Revised by Richard Tonsing.\nIntroduction by New Writer.'), 41445)
        self.assertFalse(assess_metadata(facts, AS_OF, evidence)['eligible'])

    def test_acquisition_cites_and_pins_supplement_hash(self):
        from shutil import copyfile
        from acquire_queue import acquire_queued, validate_record, stage_acquisitions
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root/'project.json', {'repository':'owner/library','targets':[{'id':'ja'}]})
            write_json(root/'queue.json', {'schema_version':1,'works':[
                {'id':'gutenberg-36','source':{'type':'gutenberg','id':36},
                 'targets':['ja'],'requests':[]}]})
            wd = root/'books/gutenberg-36'
            wd.mkdir(parents=True)
            evidence = self.supplement(36)
            evidence['publication']['title'] = 'Test Book'
            evidence['publication']['year'] = 1818
            write_json(wd/'admission-evidence.json', evidence)
            def fake_metadata(eid):
                raw = metadata(eid=eid, publication='')
                return raw, {'requested_url':f'https://www.gutenberg.org/ebooks/{eid}.rdf',
                             'resolved_url':f'https://www.gutenberg.org/ebooks/{eid}.rdf',
                             'sha256':digest(raw)}
            def fake_source(output, eid):
                target = output/'books'/f'gutenberg-{eid}'/'acquisition'
                raw = output/'download.txt'
                raw.write_bytes(package(eid=eid))
                blocks = prepare(raw, target)
                write_json(target/'provenance.json', {
                    'ebook_id':eid, 'raw_sha256':blocks['raw_sha256'],
                    'requested_url':f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt',
                    'resolved_url':f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt'})
            with patch('acquire_queue.fetch_metadata', side_effect=fake_metadata), \
                 patch('acquire_queue.fetch_gutenberg', side_effect=fake_source):
                outcome = acquire_queued(root, root/'build/source-downloads', AS_OF)
            self.assertEqual(outcome['acquired'], ['gutenberg-36'], outcome)
            record = validate_record(wd, 36)
            self.assertEqual(record['rule_version'], 'gutenberg-us-jp-v2')
            self.assertEqual(record['status'], 'acquired')
            self.assertEqual(record['admission_evidence']['file'], 'admission-evidence.json')
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            stage_acquisitions(root, root/'build/source-downloads')
            staged = subprocess.check_output(['git','diff','--cached','--name-only'],
                                             cwd=root, text=True)
            self.assertIn('books/gutenberg-36/admission-evidence.json', staged)
            before = (wd/'admission-evidence.json').read_bytes()
            (wd/'admission-evidence.json').write_bytes(before + b' ')
            with self.assertRaises(ProjectError):
                validate_record(wd, 36)

if __name__ == '__main__':
    unittest.main()
