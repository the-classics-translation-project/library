"""Version 2 translation return ZIP shared by Issue and direct relay adapters."""
from __future__ import annotations

from pathlib import Path
import re

import ctp as c
from translation_relay import decode_json, read_zip

SHA = re.compile(r'[0-9a-f]{64}')


def open_result(path: Path) -> tuple[dict[str, bytes], dict]:
    files = read_zip(path)
    c.check('result.json' in files, 'Unified result.json is missing')
    result = decode_json(files['result.json'])
    c.check(isinstance(result, dict) and
            set(result) == {'schema_version', 'kind', 'adapter', 'request_id',
                            'input_sha256', 'status', 'model_label', 'nodes', 'auxiliary'} and
            type(result['schema_version']) is int and result['schema_version'] == 2 and
            result['kind'] == 'translation', 'Unknown unified result schema')
    return files, result


def validate(files: dict[str, bytes], result: dict, *, adapter: str,
             request_id: str, input_sha256: str, fields: dict[str, list[str]],
             auxiliary: dict[str, str]) -> tuple[dict[str, dict[str, str]], dict[str, bytes], str]:
    c.check(result['adapter'] == adapter and result['request_id'] == request_id and
            isinstance(result['input_sha256'], str) and
            SHA.fullmatch(result['input_sha256']) and
            result['input_sha256'] == input_sha256,
            'Unified result belongs to another request')
    c.check(result['status'] == 'complete', 'Incomplete unified result')
    model = result['model_label']
    c.check(isinstance(model, str) and 0 < len(model.strip()) <= 160,
            'Unified result model label missing')
    c.check(isinstance(result['nodes'], dict) and
            set(result['nodes']) == set(fields) and
            result['auxiliary'] == auxiliary,
            'Unified result coverage or auxiliary files differ')
    expected = {'result.json', *auxiliary.values()}
    values: dict[str, dict[str, str]] = {}
    for node_id, expected_fields in fields.items():
        c.ident(node_id)
        mapping = result['nodes'][node_id]
        c.check(isinstance(mapping, dict) and set(mapping) == set(expected_fields),
                'Unified result field coverage differs: '+node_id)
        values[node_id] = {}
        for field in expected_fields:
            name = 'text/'+node_id+('.label.md' if field == 'label' else '.md')
            c.check(mapping[field] == name, 'Unexpected unified output path: '+node_id)
            expected.add(name)
            c.check(name in files and 0 < len(files[name]) <= 2000000,
                    'Missing or oversized unified output: '+name)
            body = files[name].decode('utf-8')
            c.check(body.strip() and '\x00' not in body and not body.startswith('\ufeff'),
                    'Invalid unified output text: '+name)
            if field == 'label':
                body = body.strip()
                c.check('\n' not in body and '\r' not in body,
                        'Translated label must be one line')
            values[node_id][field] = body
    c.check(set(files) == expected, 'Unexpected unified ZIP members')
    extras = {}
    for key, name in auxiliary.items():
        c.check(name in files and 0 < len(files[name]) <= 2000000 and
                files[name].decode('utf-8').strip() and b'\x00' not in files[name],
                'Invalid unified auxiliary file: '+name)
        extras[key] = files[name]
    return values, extras, model
