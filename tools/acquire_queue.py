"""Acquire only sources admitted by the recorded US/Japan policy; hold the rest."""
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import ParseError
from shutil import copyfile
from zoneinfo import ZoneInfo
from legacy_v1 import check, read_json, write_json, digest, object_hash, ProjectError
from intake import validate_queue
from source_import import fetch_gutenberg, validate_blocks
from source_rights import (RULE_VERSION, LEGACY_RULE_VERSION, REFERENCES, official_url, fetch_metadata,
                           parse_metadata, assess_metadata, check_package, validate_supplement)


def today() -> date:
    # Do not admit a work early at a territory's year/day boundary.
    return min(datetime.now(ZoneInfo('Asia/Tokyo')).date(),
               datetime.now(ZoneInfo('Pacific/Honolulu')).date())


def _stable(record: dict) -> dict:
    """Provider download counters/XML node IDs and timestamps are not decisions."""
    return {key: record.get(key) for key in ('schema_version', 'rule_version', 'work', 'ebook_id',
            'evidence', 'countries', 'eligible', 'status', 'reasons', 'acquisition', 'package_sha256', 'references', 'admission_evidence')}


def save_record(work_dir: Path, record: dict, metadata_raw: bytes | None) -> bool:
    path = work_dir/'rights.json'
    if path.exists() and _stable(read_json(path)) == _stable(record):
        return False
    work_dir.mkdir(parents=True, exist_ok=True)
    if metadata_raw is not None:
        (work_dir/'rights-metadata.rdf').write_bytes(metadata_raw)
    write_json(path, record)
    return True


def acquire_queued(root: Path, output: Path, as_of: date | None = None) -> dict:
    config = read_json(root/'project.json')
    queue = read_json(root/'queue.json')
    validate_queue(queue, config)
    as_of = as_of or today()
    output.mkdir(parents=True, exist_ok=True)
    report = {'schema_version': 1, 'acquired': [], 'held': [], 'skipped': [], 'failed': [], 'changed': []}
    for work in queue['works']:
        wid, eid = work['id'], work['source']['id']
        wd = root/'books'/wid
        dest = wd/'acquisition'
        record = {'schema_version': 1, 'rule_version': RULE_VERSION, 'work': wid, 'ebook_id': eid,
                  'evaluated_on': as_of.isoformat(), 'references': REFERENCES,
                  'metadata': None, 'evidence': None, 'countries': {'US': {'status': 'hold'}, 'JP': {'status': 'hold'}},
                  'eligible': False, 'status': 'held', 'reasons': [], 'admission_evidence': None}
        supplement_path = wd/'admission-evidence.json'
        supplement = None
        if supplement_path.exists():
            raw_supplement = supplement_path.read_bytes()
            supplement = validate_supplement(read_json(supplement_path), eid)
            record['admission_evidence'] = {'file': 'admission-evidence.json',
                                            'sha256': digest(raw_supplement)}
        raw = None
        # Existing acquired packages are immutable. Validate the original decision,
        # rather than silently replacing their text with today's provider package.
        if dest.exists():
            try:
                validate_blocks(dest)
                if not (wd/'rights.json').exists():
                    record['reasons'] = [{'country': 'acquisition', 'code': 'existing_source_unassessed',
                        'detail': 'Existing manually acquired source has no automatic admission record; it was not overwritten or staged.'}]
                    if save_record(wd, record, None):
                        report['changed'].append(wid)
                    report['held'].append({'work': wid, 'reasons': record['reasons']})
                else:
                    saved = validate_record(wd, eid)
                    if saved['status'] == 'acquired':
                        report['skipped'].append(wid)
                    else:
                        report['held'].append({'work': wid, 'reasons': saved['reasons']})
            except (ProjectError, OSError, ValueError, KeyError, TypeError) as exc:
                # Do not replace a historical rights record to hide a broken source.
                report['failed'].append({'work': wid, 'error': str(exc)})
            continue
        try:
            raw, metadata = fetch_metadata(eid)
            record['metadata'] = metadata
            facts = parse_metadata(raw, eid)
            record['evidence'] = facts
            result = assess_metadata(facts, as_of, supplement)
            record.update(result)
            if result['eligible']:
                # Nothing from a failed/held download reaches canonical books/.
                with TemporaryDirectory(dir=output) as temporary:
                    staging = Path(temporary)
                    fetch_gutenberg(staging, eid)
                    package = staging/'books'/wid/'acquisition'
                    blocks = validate_blocks(package)
                    provenance = read_json(package/'provenance.json')
                    check(official_url(provenance['resolved_url']), 'Source redirected outside the official HTTPS provider')
                    check(provenance['ebook_id'] == eid and provenance['raw_sha256'] == blocks['raw_sha256'], 'Source identity/hash mismatch')
                    record['package_sha256'] = blocks['raw_sha256']
                    problems = check_package((package/'acquired.txt').read_bytes(), eid, facts, supplement)
                    if problems:
                        record.update(eligible=False, reasons=record['reasons'] + problems)
                    else:
                        provenance.update(rights_checked=True, rights_assessment='../rights.json')
                        write_json(package/'provenance.json', provenance)
                        record.update(status='acquired', acquisition={'raw_sha256': blocks['raw_sha256'],
                                      'blocks_sha256': object_hash(blocks), 'source_url': provenance['requested_url']})
                        # Save bytes+assessment as one staged directory. Do not
                        # leave an acquired package behind if recording fails.
                        target = staging/'admitted'
                        target.mkdir()
                        package.replace(target/'acquisition')
                        (target/'rights-metadata.rdf').write_bytes(raw)
                        write_json(target/'rights.json', record)
                        if supplement is not None:
                            copyfile(supplement_path, target/'admission-evidence.json')
                        validate_record(target, eid)
                        wd.mkdir(parents=True, exist_ok=True)
                        check(not dest.exists(), 'Acquisition appeared during processing; refusing overwrite')
                        (target/'acquisition').replace(dest)
                        try:
                            (target/'rights-metadata.rdf').replace(wd/'rights-metadata.rdf')
                            (target/'rights.json').replace(wd/'rights.json')
                        except OSError:
                            # Return the new bytes to temporary storage on failure.
                            dest.replace(target/'acquisition')
                            raise
                        report['acquired'].append(wid)
                        report['changed'].append(wid)
                        continue
        except (ProjectError, OSError, ValueError, ParseError, KeyError, TypeError) as exc:
            record.update(status='held', eligible=False)
            record['reasons'].append({'country': 'acquisition', 'code': 'acquisition_error', 'detail': str(exc)})
            report['failed'].append({'work': wid, 'error': str(exc)})
        report['held'].append({'work': wid, 'reasons': record['reasons']})
        if save_record(wd, record, raw):
            report['changed'].append(wid)
    write_json(output/'report.json', report)
    return report


def validate_record(work_dir: Path, ebook_id: int) -> dict:
    record = read_json(work_dir/'rights.json')
    version = record.get('rule_version')
    check(record.get('schema_version') == 1 and version in {RULE_VERSION, LEGACY_RULE_VERSION},
          'Unknown automatic rights policy')
    supplement = None
    if version == RULE_VERSION and record.get('admission_evidence') is not None:
        evidence = record['admission_evidence']
        check(evidence.get('file') == 'admission-evidence.json' and
              isinstance(evidence.get('sha256'), str), 'Invalid admission evidence reference')
        p = work_dir/'admission-evidence.json'
        check(digest(p.read_bytes()) == evidence['sha256'], 'Admission evidence hash changed')
        supplement = validate_supplement(read_json(p), ebook_id)
    if version == LEGACY_RULE_VERSION:
        check('admission_evidence' not in record,
              'A legacy record cannot silently acquire modern evidence')
    check(record.get('ebook_id') == ebook_id and record.get('work') == f'gutenberg-{ebook_id}', 'Rights record identity mismatch')
    check(record.get('references') == REFERENCES, 'Rights rule references changed')
    as_of = date.fromisoformat(record['evaluated_on'])
    check(as_of <= today(), 'Rights record was evaluated in the future')
    check(record.get('status') in {'acquired', 'held'}, 'Unknown acquisition status')
    check(isinstance(record.get('reasons'), list), 'Rights record needs reasons')
    for reason in record['reasons']:
        check(isinstance(reason, dict) and all(isinstance(reason.get(k), str) and reason[k] for k in ('country', 'code', 'detail')), 'Invalid hold reason')
    if record.get('metadata') is not None:
        raw = (work_dir/'rights-metadata.rdf').read_bytes()
        check(digest(raw) == record['metadata']['sha256'], 'Rights metadata changed')
        check(record['metadata']['requested_url'] == f'https://www.gutenberg.org/ebooks/{ebook_id}.rdf'
              and official_url(record['metadata']['resolved_url']), 'Rights metadata URL mismatch')
    if record.get('evidence') is not None:
        check(record.get('metadata') is not None, 'Extracted evidence needs retained metadata')
        facts = parse_metadata(raw, ebook_id)
        check(facts == record['evidence'], 'Rights evidence differs from saved metadata')
        result = assess_metadata(facts, as_of, supplement)
        check(record['countries'] == result['countries'], 'Country assessment does not match the rule calculation')
        check(all(r in record['reasons'] for r in result['reasons']), 'Recorded hold reasons omit a rule failure')
    else:
        result = {'eligible': False}
    if record['status'] == 'acquired':
        check(record.get('eligible') is True and result['eligible'] and not record['reasons'], 'Source does not pass both territory checks')
        blocks = validate_blocks(work_dir/'acquisition')
        check(record.get('package_sha256') == blocks['raw_sha256'], 'Assessed source hash mismatch')
        provenance = read_json(work_dir/'acquisition/provenance.json')
        check(record['acquisition'] == {'raw_sha256': blocks['raw_sha256'], 'blocks_sha256': object_hash(blocks),
                                      'source_url': f'https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt'}, 'Acquisition no longer matches the rights decision')
        check(provenance['ebook_id'] == ebook_id and provenance['raw_sha256'] == blocks['raw_sha256']
              and provenance['requested_url'] == record['acquisition']['source_url'] and official_url(provenance['resolved_url'])
              and provenance.get('rights_checked') is True and provenance.get('rights_assessment') == '../rights.json', 'Source provenance differs from the admission record')
        check(not check_package((work_dir/'acquisition/acquired.txt').read_bytes(), ebook_id, facts, supplement), 'Source package does not pass identity/contribution checks')
    else:
        check(record.get('eligible') is False and bool(record['reasons']), 'Held sources need a reason and must not be eligible')
    return record


def stage_acquisitions(root: Path, output: Path) -> None:
    """Stage an exact allowlist; never stage a whole work or download directory."""
    import subprocess
    queue = read_json(root/'queue.json')
    validate_queue(queue, read_json(root/'project.json'))
    allowed = {w['id']: w['source']['id'] for w in queue['works']}
    report = read_json(output/'report.json')
    paths = []
    for wid in report['changed']:
        check(wid in allowed, 'Work is not in the authorized queue')
        wd = root/'books'/wid
        record = validate_record(wd, allowed[wid])
        names = ['rights.json']
        if record.get('admission_evidence') is not None:
            names.append('admission-evidence.json')
        if record.get('metadata') is not None:
            names.append('rights-metadata.rdf')
        if record['status'] == 'acquired':
            names += ['acquisition/'+name for name in ('acquired.txt', 'normalized.txt', 'blocks.json', 'provenance.json')]
        paths.extend(str(Path('books')/wid/name) for name in names)
    if paths:
        subprocess.run(['git', 'add', '--', *paths], cwd=root, check=True)
