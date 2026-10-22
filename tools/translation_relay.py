"""Offline package/accept boundary for the browser relay. Never submits jobs."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import fcntl
import json
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from uuid import uuid4
import zipfile

import ctp as c

MAX_BYTES = 32 * 1024 * 1024


def decode_json(data):
    return json.loads(data.decode('utf-8'), object_pairs_hook=c.pairs,
                      parse_constant=c.invalid_constant)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


@contextmanager
def locked(root):
    folder = root/'private/relay'
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield folder


def inventory(folder):
    c.check(not folder.is_symlink(), 'Edition directory is a symbolic link')
    if not folder.exists():
        return None
    result = {}
    for path in sorted(folder.rglob('*')):
        c.check(not path.is_symlink(), 'Edition contains a symbolic link')
        if path.is_file():
            result[path.relative_to(folder).as_posix()] = c.digest(path.read_bytes())
    return result


def ready(root, work_id):
    c.ident(work_id)
    wd = root/'books'/work_id
    c.check(wd.resolve().is_relative_to((root/'books').resolve()), 'Unsafe work path')
    work, tree = c.validate_work(wd)
    c.check(c.is_tree(work) and bool(tree), 'A structured schema-v2 source is required')
    from acquire_queue import validate_record
    rights = c.read_json(wd/'rights.json')
    c.check(rights.get('work') == work_id, 'Rights record belongs to another work')
    validate_record(wd, rights['ebook_id'])
    c.check(rights.get('eligible') is True and rights.get('status') == 'acquired',
            'Source must be admitted and acquired')
    return wd, work, tree


def read_zip(path):
    """Read bounded regular UTF-8 files without extracting arbitrary paths."""
    try:
        with zipfile.ZipFile(io.BytesIO(path) if isinstance(path, bytes) else path) as archive:
            infos = archive.infolist()
            c.check(len(infos) <= 2000, 'Too many ZIP members')
            c.check(sum(i.file_size for i in infos) <= MAX_BYTES, 'ZIP is too large')
            result = {}
            for info in infos:
                name = info.filename
                parts = PurePosixPath(name).parts
                c.check(name and not name.startswith('/') and '\\' not in name
                        and all(p not in ('..', '.') for p in parts)
                        and PurePosixPath(name).as_posix() == name
                        and not any(ord(ch) < 32 for ch in name), 'Unsafe ZIP member')
                mode = info.external_attr >> 16
                c.check(not info.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG),
                        'ZIP members must be regular files')
                c.check(name not in result, 'Duplicate ZIP member')
                data = archive.read(info)
                data.decode('utf-8')
                result[name] = data
            return result
    except (zipfile.BadZipFile, UnicodeError, RuntimeError) as exc:
        raise c.ProjectError(f'Invalid ZIP: {exc}') from exc


def package(root, work_id, edition_id, nodes, model, language=None, direction='ltr',
            kind='translation', context_nodes=()):
    root = root.resolve()
    c.ident(edition_id)
    c.check(isinstance(model, str) and model.strip() and '\n' not in model and '\r' not in model,
            'Specify one Chat UI model choice')
    with locked(root) as jobs:
        wd, work, tree = ready(root, work_id)
        base = wd/'editions'/edition_id
        c.check(base.resolve().is_relative_to(wd.resolve()), 'Unsafe edition path')
        before = inventory(base)
        if before is not None:
            _, ed, _ = c.load_work(wd, edition_id)
            c.check(language is None or language == ed['language'], 'Target language conflicts with edition')
        else:
            c.check(language is not None, 'New editions require --language')
            ed = {'schema_version': 2, 'id': edition_id, 'language': language,
                  'direction': direction, 'kind': kind, 'status': 'draft',
                  'description': f'{language} {kind} draft', 'rights_note': 'Not cleared for distribution',
                  'production': {'ai_use': 'ChatGPT relay draft', 'human_review': 'Not performed', 'runs': []},
                  'nodes': {}}
            c.validate_tree_edition(tree, ed)
        ordered = [n for n, _ in c.walk(tree)]
        by_id = {n['id']: n for n in ordered}
        c.check(nodes and len(nodes) == len(set(nodes)) and set(nodes) <= set(by_id),
                'Select unique existing source node IDs')
        c.check(len(context_nodes) == len(set(context_nodes)) and set(context_nodes) <= set(by_id)
                and not set(context_nodes) & set(nodes), 'Invalid or overlapping context nodes')
        selected = [n for n in ordered if n['id'] in nodes]
        c.check(all(set(n) & {'label', 'text'} for n in selected), 'Selected node has no literary fields')
        fields = {n['id']: [f for f in ('label', 'text') if f in n] for n in selected}
        files = {}
        for name, path in [('policy.md', root/'docs/editorial-policy.md'),
                           ('translate.md', root/'prompts/translate.md'),
                           ('work-notes.md', wd/'notes.md'), ('edition-notes.md', base/'notes.md'),
                           ('glossary.md', base/'glossary.md')]:
            if path.exists():
                files[name] = path.read_bytes()
        source = []
        for n in ordered:
            if n['id'] not in set(nodes) | set(context_nodes):
                continue
            item = {'id': n['id'], 'role': 'translate' if n['id'] in nodes else 'context'}
            if 'label' in n:
                item['label'] = n['label']
            if 'text' in n:
                item['text'] = c.source_file(wd, n['text']).read_text(encoding='utf-8')
            source.append(item)
        files['source.json'] = json_bytes(source)
        files['tree.json'] = json_bytes(tree)
        attempt = 'ctp-' + uuid4().hex
        output = attempt + '-result.zip'
        manifest = {'schema_version': 1, 'attempt': attempt, 'work': work_id, 'edition': edition_id,
                    'language': ed['language'], 'model_requested': model, 'output_filename': output,
                    'source_fingerprint': c.source_fingerprint(wd), 'fields': fields,
                    'context_nodes': list(context_nodes), 'edition_before': before, 'edition_seed': ed}
        files['manifest.json'] = json_bytes(manifest)
        template = (root/'prompts/relay-translation.md').read_text(encoding='utf-8')
        files['README.md'] = (f'---\nmodel: {model}\noutput_filename: {output}\n---\n\n' + template).encode()
        c.check(sum(map(len, files.values())) <= MAX_BYTES, 'Package exceeds size limit; select fewer nodes')
        for data in files.values():
            data.decode('utf-8')
        folder = jobs/attempt
        folder.mkdir()
        path = folder/(attempt+'.zip')
        with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        c.write_json(folder/'job.json', {'package_sha256': c.digest(path.read_bytes()),
                                       'manifest': manifest})
        return {'attempt': attempt, 'package': str(path), 'output_filename': output,
                'submitted': False, 'model_called': False}


def import_result(root, attempt, result_path, observed_model='unknown', chat_url=None):
    root = root.resolve()
    c.ident(attempt)
    c.check(observed_model.strip(), 'Observed model must be a label or unknown')
    if chat_url is not None:
        import re
        c.check(re.fullmatch(r'https://chatgpt\.com/c/[A-Za-z0-9-]+', chat_url), 'Invalid Chat URL')
    with locked(root) as jobs:
        folder = jobs/attempt
        job = c.read_json(folder/'job.json')
        m = job['manifest']
        c.check(m['attempt'] == attempt, 'Attempt identity mismatch')
        package_path = folder/(attempt+'.zip')
        package_bytes = package_path.read_bytes()
        c.check(c.digest(package_bytes) == job['package_sha256'], 'Submitted package changed')
        inputs = read_zip(package_bytes)
        c.check(decode_json(inputs['manifest.json']) == m, 'Package manifest mismatch')
        wd, work, tree = ready(root, m['work'])
        base = wd/'editions'/m['edition']
        c.ident(m['edition'])
        c.check(base.resolve().is_relative_to(wd.resolve()), 'Unsafe edition path')
        receipt = base/'relay'/attempt/'receipt.json'
        c.check(not receipt.exists(), 'Attempt already imported')
        c.check(c.source_fingerprint(wd) == m['source_fingerprint'], 'Source changed since packaging')
        c.check(inventory(base) == m['edition_before'], 'Edition changed since packaging; prepare a new attempt')
        result_bytes = result_path.read_bytes()
        files = read_zip(result_bytes)
        c.check('result.json' in files, 'Missing result.json')
        result = decode_json(files['result.json'])
        c.check(isinstance(result, dict) and set(result) == {'schema_version', 'attempt', 'work', 'edition', 'language', 'status', 'nodes'},
                'Unexpected result fields')
        c.check(result['schema_version'] == 1, 'Unknown result schema')
        for key in ('attempt', 'work', 'edition', 'language'):
            c.check(result[key] == m[key], f'Result {key} mismatch')
        c.check(result['status'] == 'complete', 'Incomplete result retained externally; no edition changes made')
        c.check(isinstance(result['nodes'], dict) and set(result['nodes']) == set(m['fields']), 'Result node coverage mismatch')
        expected = {'result.json', 'glossary.md', 'notes.md'}
        for nid, fields in m['fields'].items():
            target = result['nodes'][nid]
            c.check(isinstance(target, dict) and set(target) == set(fields), f'{nid}: field coverage mismatch')
            for field, value in target.items():
                c.check(isinstance(value, str) and value.strip(), 'Empty translated field')
                if field == 'text':
                    c.check(value == f'text/{nid}.md', 'Unexpected body path')
                    expected.add(value)
        c.check(set(files) == expected, 'Missing or unexpected result files')
        c.check(all(data.decode('utf-8').strip() for data in files.values()), 'Empty result file')
        # Prepare a full replacement and provenance in isolation. Keep the old edition
        # as a private backup, including on successful import.
        with tempfile.TemporaryDirectory(prefix='import-', dir=jobs) as temp:
            stage_root = Path(temp)
            stage_work = stage_root/'books'/m['work']
            shutil.copytree(wd, stage_work)
            stage_base = stage_work/'editions'/m['edition']
            stage_base.mkdir(parents=True, exist_ok=True)
            ed = copy.deepcopy(m['edition_seed'])
            ed['status'] = 'draft'
            ed['production']['human_review'] = 'Not performed for this imported draft'
            ed['production']['ai_use'] = 'ChatGPT relay; see generation records'
            archive = stage_base/'relay'/attempt
            archive.mkdir(parents=True)
            (archive/'request.zip').write_bytes(package_bytes)
            (archive/'result.zip').write_bytes(result_bytes)
            for name, data in inputs.items():
                dest = archive/'input'/name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            generated = []
            for nid, target in result['nodes'].items():
                ed['nodes'][nid] = dict(target)
                if 'text' in target:
                    dest = stage_base/target['text']
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(files[target['text']])
                    generated.append(dest)
            # Glossaries are cumulative proposed editorial memory; the request asks
            # the worker to preserve useful existing entries. Notes remain proposals.
            for name, dest in [('glossary.md', stage_base/'glossary.md'),
                               ('notes.md', archive/'suggested-notes.md')]:
                dest.write_bytes(files[name]); generated.append(dest)
            if not (stage_base/'notes.md').exists():
                (stage_base/'notes.md').write_text('# Editorial notes\n\n## Decisions\n\nNone yet.\n\n## Observations\n\nSee relay attempt notes; proposals are not adopted decisions.\n\n## Open questions\n\nLiterary review remains outstanding.\n')
            c.write_json(stage_base/'edition.json', ed)
            generated.append(stage_base/'edition.json')
            captured = [{'path': name, 'text': data.decode('utf-8'), 'sha256': c.digest(data)}
                        for name, data in inputs.items() if name != 'README.md']
            run_path = c.record_run(stage_root, m['work'], m['edition'], observed_model,
                                    'chatgpt', 'retranslation' if any(n in m['edition_seed']['nodes'] for n in m['fields']) else 'translation',
                                    [archive/'input/README.md'],
                                    'Please read the README.md at the root of the attached ZIP and follow its instructions.',
                                    generated, captured_inputs=captured)
            run = c.read_json(run_path)
            run['git_context'] = c.git_context(root)
            run['relay'] = {'attempt': attempt, 'model_requested': m['model_requested'],
                            'chat_url': chat_url, 'request_sha256': job['package_sha256'],
                            'result_sha256': c.digest(result_bytes)}
            c.write_json(run_path, run)
            c.write_json(archive/'receipt.json', run['relay'])
            c.load_work(stage_work, m['edition']); c.validate_run(run)
            # Recheck immediately before installation; the lock serializes adapters.
            c.check(inventory(base) == m['edition_before'], 'Edition changed during import')
            c.check(c.source_fingerprint(wd) == m['source_fingerprint'], 'Source changed during import')
            backup = folder/'edition-before'
            c.check(not backup.exists(), 'Previous interrupted import: inspect edition-before before retrying')
            base.parent.mkdir(parents=True, exist_ok=True)
            if base.exists():
                os.rename(base, backup)
            try:
                os.rename(stage_base, base)
            except BaseException:
                if backup.exists():
                    os.rename(backup, base)
                raise
        return {'edition': str(base), 'run': run['id'], 'status': 'draft',
                'missing': c.missing_fields(tree, ed), 'published': False}
