"""Offline request/ZIP protocol for translating canonical source-tree fields.

No model or network calls. GitHub Issues are untrusted data.
"""
from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile
import json
import re
import tempfile
from legacy_v1 import check, read_json, write_json, digest, object_hash, ProjectError
from source_import import walk

MARKER = '<!-- ctp:translation-request:v1 -->'
VARIABLE = re.compile(r'\{\{([a-z_]+)\}\}')
ALLOWED = {'target_language','target_language_code','source_language','work_title'}
HASH = re.compile(r'[0-9a-f]{64}')
PROMPT_ID = re.compile(r'[a-z0-9][a-z0-9_-]{0,63}')

def _ctp():
    import ctp
    return ctp

def prompt_catalogue(root: Path) -> list[dict]:
    result=[]
    for path in sorted((root/'prompts/translation').glob('*.md')):
        check(PROMPT_ID.fullmatch(path.stem) is not None,'Invalid prompt filename')
        text=path.read_text(encoding='utf-8')
        check(bool(text.strip()) and len(text)<100000,'Empty/oversized prompt')
        check(set(VARIABLE.findall(text))<=ALLOWED and
              '{{' not in VARIABLE.sub('',text),'Unsupported prompt template variable')
        title=next((s[2:].strip() for s in text.splitlines() if s.startswith('# ')),path.stem)
        check(bool(title) and len(title)<=120,'Invalid prompt title')
        result.append({'id':path.stem,'title':title,'sha256':digest(text.encode())})
    return result

def prompt_text(root: Path, ident: str) -> str:
    check(isinstance(ident,str) and PROMPT_ID.fullmatch(ident) is not None,'Invalid prompt ID')
    path=root/'prompts/translation'/(ident+'.md')
    check(path.is_file(),'Unknown translation prompt')
    return path.read_text(encoding='utf-8')

def render_prompt(template: str, variables: dict) -> str:
    check(set(VARIABLE.findall(template))<=ALLOWED,'Unknown template variable')
    result=VARIABLE.sub(lambda m:variables[m.group(1)],template)
    check('{{' not in result and '}}' not in result,'Unexpanded prompt variable')
    return result

def expanded_nodes(tree: dict, selected: list[str]) -> list[dict]:
    check(isinstance(selected,list) and 0<len(selected)<=500 and
          all(isinstance(x,str) for x in selected) and len(selected)==len(set(selected)),
          'Invalid node selection')
    nodes=[n for n,_ in walk(tree)]
    by_id={n['id']:n for n in nodes}
    check(set(selected)<=set(by_id),'Unknown source node')
    ids=set()
    def add(n):
        ids.add(n['id'])
        for child in n.get('children',[]): add(child)
    for ident in selected:add(by_id[ident])
    return [n for n in nodes if n['id'] in ids]

def validate_request(root: Path, r: dict, pinned_prompt: str | None = None) -> list[dict]:
    c=_ctp()
    required={'schema_version','work','target','nodes','source_fingerprint',
              'scope','prompt','reference','instructions'}
    check(isinstance(r,dict) and set(r)==required and r['schema_version']==1,
          'Unknown translation-request schema')
    check(isinstance(r['work'],str) and re.fullmatch(r'gutenberg-[0-9]{1,7}',r['work']),
          'Invalid source work')
    wd=root/'books'/r['work']
    _,tree=c.validate_work(wd)
    check(isinstance(r['source_fingerprint'],str) and
          HASH.fullmatch(r['source_fingerprint']) and
          r['source_fingerprint']==c.source_fingerprint(wd),
          'Translation request has stale source fingerprint')
    check(r['target'] in {x['id'] for x in read_json(root/'project.json')['targets']},
          'Unsupported target language')
    nodes=expanded_nodes(tree,r['nodes'])
    check(r['scope'] in ('all','missing'),'Invalid translation scope')
    check(isinstance(r['instructions'],str) and len(r['instructions'])<=4000,
          'Invalid additional instructions')
    p=r['prompt']
    check(isinstance(p,dict) and set(p)=={'id','sha256'} and
          isinstance(p['sha256'],str) and HASH.fullmatch(p['sha256']),
          'Invalid prompt reference')
    actual=pinned_prompt if pinned_prompt is not None else prompt_text(root,p['id'])
    check(digest(actual.encode())==p['sha256'],'Prompt changed since Issue creation')
    ref=r['reference']
    check(isinstance(ref,dict) and set(ref)=={'mode','revision'} and
          ref['mode'] in ('none','notes','text'),'Invalid translation reference')
    if ref['mode']=='text':
        check(isinstance(ref['revision'],str) and HASH.fullmatch(ref['revision']),
              'Exact frozen reference revision required')
        snap=c.load_snapshot(root,r['work'],r['target'],ref['revision'])
        check(snap['edition']['language']==r['target'] and
              snap['source_fingerprint']==r['source_fingerprint'],
              'Reference revision incompatible with request')
    else:
        check(ref['revision'] is None,'Unexpected reference revision')
    return nodes

