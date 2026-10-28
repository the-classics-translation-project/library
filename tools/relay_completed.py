"""Import already-authorized direct relay results; never submit or change relay state."""
from __future__ import annotations

import os
from pathlib import Path
import re

import ctp as c
from relay_coordinator import DEFAULT_RELAY, canonical_model, transport_rows
from translation_relay import import_result

MAX_RESULT_BYTES = 32 * 1024 * 1024


def _check_authorization(folder, attempt, job):
    manifest = job['manifest']
    c.ident(manifest['work']);c.ident(manifest['edition'])
    c.check(manifest['attempt'] == attempt and
            manifest['output_filename'] == attempt+'-result.zip',
            'Direct attempt identity or output filename differs')
    request = folder/(attempt+'.zip')
    c.check(request.is_file() and not request.is_symlink() and
            c.digest(request.read_bytes()) == job['package_sha256'],
            'Archived direct request is missing or changed')
    path = folder/'authorization.json'
    c.check(path.is_file() and not path.is_symlink(),
            'Direct relay submission has no owner authorization record')
    authorization = c.read_json(path)
    expected = {'attempt':attempt, 'request_sha256':job['package_sha256'],
                'model_requested':manifest['model_requested'], 'work':manifest['work'],
                'target':manifest['language'],
                'context_nodes':manifest['context_nodes']}
    nodes=authorization.get('nodes')
    c.check(all(authorization.get(key)==value for key,value in expected.items()) and
            isinstance(nodes,list) and len(nodes)==len(set(nodes)) and
            set(nodes)==set(manifest['fields']) and
            isinstance(authorization.get('authorization'),str) and
            bool(authorization['authorization'].strip()) and
            isinstance(authorization.get('authorized_at'),str) and
            bool(authorization['authorized_at'].strip()),
            'Direct relay authorization does not match its exact request')
    return manifest


def _capture(folder, result):
    c.check(result.is_file() and not result.is_symlink(),
            'Relay says complete but exact result file is missing')
    c.check(result.stat().st_size <= MAX_RESULT_BYTES, 'Direct result ZIP too large')
    raw=result.read_bytes()
    captured=folder/'response.zip'
    if captured.exists():
        c.check(not captured.is_symlink() and captured.read_bytes()==raw,
                'Direct result changed after private capture')
    else:
        with captured.open('xb') as out:
            out.write(raw);out.flush();os.fsync(out.fileno())
    return captured


def import_direct_completed(root: Path, relay: Path = DEFAULT_RELAY) -> dict:
    """Observe a read-only transport ledger and import eligible direct drafts once."""
    root=root.resolve();relay=relay.resolve()
    rows=transport_rows(relay)
    imported=[];held=[];pending=[];existing=[]
    for folder in sorted((root/'private/relay').glob('ctp-*')):
        if folder.is_symlink() or not folder.is_dir():
            held.append({'attempt':folder.name,'reason':'Unsafe direct attempt directory'})
            continue
        if not (folder/'job.json').is_file():continue
        attempt=folder.name
        if (folder/'publication.json').is_symlink():
            held.append({'attempt':attempt,'reason':'Unsafe publication marker'})
            continue
        if (folder/'publication.json').exists():
            existing.append(attempt);continue
        try:
            c.ident(attempt)
            c.check(not (folder/'job.json').is_symlink(), 'Unsafe direct job record')
            job=c.read_json(folder/'job.json')
            name=attempt+'.zip'
            matches=[row for row in rows if row['input_name']==name]
            c.check(len(matches)<=1,'Duplicate direct relay input name')
            if not matches:
                pending.append(attempt);continue
            found=matches[0]
            manifest=job['manifest']
            c.check(found['sha256']==job['package_sha256'] and
                    found['output_filename']==manifest['output_filename'] and
                    canonical_model(found['model'])==canonical_model(manifest['model_requested']),
                    'Direct relay request hash, model or output filename differs')
            if found['status']=='needs_review':
                held.append({'attempt':attempt,
                             'reason':found['review_reason'] or 'Relay needs review'})
                continue
            if found['status']!='complete':
                pending.append(attempt);continue
            c.check(isinstance(found['chat_url'],str) and
                    re.fullmatch(r'https://chatgpt\.com/c/[A-Za-z0-9-]+',found['chat_url']),
                    'Completed direct relay job has no valid Chat URL')
            manifest=_check_authorization(folder,attempt,job)
            receipt=root/'books'/manifest['work']/'editions'/manifest['edition']/'relay'/attempt/'receipt.json'
            c.check(not receipt.exists(),
                    'Direct result was installed without a publication manifest; inspect recovery')
            result=_capture(folder,relay/'output'/manifest['output_filename'])
            outcome=import_result(root,attempt,result,observed_model='unknown',
                                  chat_url=found['chat_url'])
            imported.append({'attempt':attempt,'edition':manifest['edition'],
                             'result_sha256':c.digest(result.read_bytes()),
                             'run':outcome['run']})
        except (c.ProjectError,OSError,ValueError,KeyError,TypeError) as exc:
            held.append({'attempt':attempt,'reason':str(exc)})
    return {'imported':imported,'held':held,'pending':pending,'existing':existing,
            'model_called':False,'relay_submitted':False,'relay_queue_mutated':False}
