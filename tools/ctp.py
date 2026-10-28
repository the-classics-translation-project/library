#!/usr/bin/env python3
"""The Classics Translation Project: local-first editorial and publishing tools.

Network/model calls are never implicit in validation, snapshotting or building.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any
import legacy_v1 as legacy
# Preserve the v1 utility/test interface and read existing immutable v1 snapshots.
from legacy_v1 import *
from source_import import walk, validate_tree, validate_blocks, compile_plan, prepare, apply

VERSION = '0.1.0'

def is_tree(obj: dict) -> bool:
    return obj.get('schema_version') == 2

def validate_work_metadata(work: dict) -> None:
    if not is_tree(work):
        legacy.validate_metadata(work); return
    for field in ('id','language','author','source_edition','source_provenance','rights_note'):
        nonempty(work, field)
    ident(work['id'])
    check(isinstance(work.get('source'), dict), 'Work needs a source provenance object')
    check(work.get('status') in ('imported','reviewed'), 'Invalid source status')
    check(work.get('structure') == 'structure.json', 'The canonical tree is structure.json')

def validate_work(work_dir: Path) -> tuple[dict, dict]:
    work = read_json(work_dir/'work.json'); validate_work_metadata(work)
    check(work['id'] == work_dir.name, 'Work directory does not match its ID')
    if not is_tree(work):
        for s in work['sections']: read_markdown(source_file(work_dir, s['file']))
        return work, {}
    tree = read_json(work_dir/'structure.json'); nodes = validate_tree(tree)
    files = []
    for n in nodes:
        if 'text' in n:
            p = source_file(work_dir, n['text']); read_markdown(p); files.append(str(p))
    check(len(files) == len(set(files)), 'Two source nodes refer to the same body file')
    if (work_dir/'acquisition/blocks.json').exists():
        record = validate_blocks(work_dir/'acquisition')
        plan = read_json(work_dir/'acquisition/plan.json')
        expected, texts, audit = compile_plan(record, plan)
        # v0.1 imports are immutable; explicit migration support can be added later.
        check(tree == expected, 'Canonical tree differs from its source plan; document a migration rather than regenerating IDs')
        for filename, text in texts.items():
            check((work_dir/filename).read_text(encoding='utf-8') == text, 'Structured source body changed')
        check(read_json(work_dir/'acquisition/audit.json') == audit, 'Source audit mismatch')
    return work, tree

def missing_fields(tree: dict, edition: dict) -> list[dict]:
    mapping = edition['nodes']; missing = []
    for n, _ in walk(tree):
        t = mapping.get(n['id'], {})
        for f in ('label','text'):
            if f in n and f not in t: missing.append({'node':n['id'], 'field':f})
    return missing

def validate_tree_edition(tree: dict, ed: dict, base: Path | None = None) -> None:
    check(is_tree(ed), 'Tree editions use schema_version 2')
    for f in ('id','language','rights_note','description'): nonempty(ed, f)
    ident(ed['id'])
    check(bool(re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*', ed['language'])), 'Invalid language tag')
    check(ed.get('direction') in ('ltr','rtl'), 'direction must be ltr or rtl')
    check(ed.get('status') in ('draft','ready'), 'Invalid edition status')
    check(ed.get('kind') in ('modernization','translation'), 'Invalid edition kind')
    check(isinstance(ed.get('production'),dict), 'Missing production record')
    check(isinstance(ed.get('nodes'),dict), 'Edition needs a node mapping')
    source = {n['id']:n for n, _ in walk(tree)}
    paths = []
    for nid, target in ed['nodes'].items():
        check(nid in source, f'Unknown target node {nid}')
        check(isinstance(target,dict) and set(target) <= {'label','text'}, 'Targets only contain label and/or text')
        for field, value in target.items():
            check(field in source[nid], f'{nid}: target invents a {field} absent from source')
            check(isinstance(value,str) and bool(value.strip()), 'A translated field is empty')
            if field == 'text' and base is not None:
                p = source_file(base,value); read_markdown(p); paths.append(str(p))
    check(len(paths) == len(set(paths)), 'Two target nodes refer to the same body file')
    if ed['status'] == 'ready': check(not missing_fields(tree,ed), 'Ready edition lacks translated labels or bodies')

def load_work(work_dir: Path, edition_id: str) -> tuple[dict,dict,Path]:
    work_dir = work_dir.resolve(); ident(edition_id)
    work, tree = validate_work(work_dir)
    if not is_tree(work): return legacy.load_work(work_dir,edition_id)
    base = work_dir/'editions'/edition_id
    ed = read_json(base/'edition.json')
    check(ed['id'] == edition_id, 'Edition ID mismatch')
    validate_tree_edition(tree,ed,base)
    return work,ed,base

def source_fingerprint(work_dir: Path) -> str:
    work, tree = validate_work(work_dir)
    values = {'work':work, 'tree':tree, 'texts':{}}
    for n, _ in walk(tree):
        if 'text' in n: values['texts'][n['id']] = read_markdown(source_file(work_dir,n['text']))
    return object_hash(values)

def freeze(work_dir: Path, edition_id: str, root: Path = ROOT) -> tuple[str,Path]:
    work, ed, eddir = load_work(work_dir,edition_id)
    if not is_tree(work): return legacy.freeze(work_dir,edition_id,root)
    tree = read_json(work_dir/'structure.json')
    check(bool(ed['nodes']), 'No target fields to snapshot')
    # Partial drafts may be frozen for history before the root title is translated.
    # Only ready reader releases require every source label/body (validated elsewhere).
    def content(value, namespace):
        fragment = render(value, namespace)
        return {'markdown':value, 'markdown_sha256':digest(value.encode()), 'html':fragment, 'text':html_text(fragment)}
    source, target = {}, {}
    for n, _ in walk(tree):
        nid = n['id']; s, t = {}, {}
        if 'label' in n: s['label'] = n['label']
        if 'text' in n: s['text'] = content(read_markdown(source_file(work_dir,n['text'])), 'source-'+nid)
        e = ed['nodes'].get(nid,{})
        if 'label' in e: t['label'] = e['label']
        if 'text' in e: t['text'] = content(read_markdown(source_file(eddir,e['text'])), 'target-'+nid)
        source[nid] = s
        if t: target[nid] = t
    runs = []
    for rid in ed['production'].get('runs',[]):
        ident(rid); run = read_json(eddir/'runs'/(rid+'.json'))
        validate_run(run,root)
        runs.append(run)
    obj = {'schema_version':2, 'work':work, 'edition':ed, 'tree':tree, 'source_nodes':source, 'target_nodes':target,
           'source_fingerprint':source_fingerprint(work_dir), 'missing':missing_fields(tree,ed),
           'production_runs':runs, 'renderer':{'name':'pandoc','version':pandoc('--version').splitlines()[0], 'format':MARKDOWN},
           'git_context':git_context(root)}
    revision = object_hash(obj); validate_snapshot(obj,revision)
    path = snapshot_path(root,work['id'],ed['id'],revision)
    if path.exists(): check(read_json(path)==obj, 'Existing snapshot differs')
    else: write_json(path,obj)
    return revision,path

def field_map(obj: dict) -> dict:
    fields = {}
    for n, depth in walk(obj['tree']):
        nid = n['id']; target = obj['target_nodes'].get(nid,{})
        if 'label' in target:
            fields[nid+':label'] = {'node':nid,'field':'label','text':target['label'], 'html':esc(target['label']), 'depth':depth}
        if 'text' in target:
            fields[nid+':text'] = {'node':nid,'field':'text','text':target['text']['text'], 'html':target['text']['html'], 'depth':depth}
    # This is bibliographic credit, not translated prose, but it is still annotatable.
    author = obj['edition'].get('author_credit',obj['work']['author'])
    fields[obj['tree']['id']+':credit'] = {'node':obj['tree']['id'],'field':'credit','text':author,'html':esc(author),'depth':0}
    return fields

def validate_snapshot(obj: dict, revision: str) -> None:
    if not is_tree(obj): legacy.validate_snapshot(obj,revision); return
    check(bool(HASH.fullmatch(revision)) and object_hash(obj)==revision, 'Snapshot hash mismatch')
    validate_work_metadata(obj['work']); nodes = validate_tree(obj['tree'])
    validate_tree_edition(obj['tree'],obj['edition'])
    check(obj['missing']==missing_fields(obj['tree'],obj['edition']), 'Incorrect missing-field inventory')
    check(set(obj['source_nodes']) == {n['id'] for n in nodes}, 'Incomplete frozen source-node inventory')
    expected_target = {k for k,v in obj['edition']['nodes'].items() if v}
    check(set(obj['target_nodes']) == expected_target, 'Incorrect frozen target-node inventory')
    for source_side in (True,False):
        frozen = obj['source_nodes'] if source_side else obj['target_nodes']
        expected = {n['id']:n for n in nodes} if source_side else obj['edition']['nodes']
        for nid, data in frozen.items():
            check(set(data) == (set(expected[nid]) & {'label','text'}), 'Frozen node fields mismatch')
            if 'label' in data: check(data['label'] == expected[nid]['label'], 'Frozen label mismatch')
            if 'text' in data:
                v = data['text']
                check(v['markdown_sha256']==digest(v['markdown'].encode()), 'Frozen Markdown hash mismatch')
                check(v['text']==html_text(v['html']), 'Frozen HTML/text mismatch')
    for run in obj.get('production_runs',[]): validate_run(run)

def load_snapshot(root: Path, work: str, edition: str, revision: str) -> dict:
    obj = read_json(snapshot_path(root,work,edition,revision)); validate_snapshot(obj,revision)
    check(obj['work']['id']==work and obj['edition']['id']==edition, 'Snapshot identity mismatch')
    return obj

def load_catalog(root: Path, demo: bool = False) -> list[tuple[dict,dict]]:
    files = [root/'catalog.json']
    if demo and (root/'examples/catalog.json').exists(): files.append(root/'examples/catalog.json')
    results, seen = [], set()
    for filename in files:
        data = read_json(filename); schema(data)
        for r in data['revisions']:
            check(r['revision'] not in seen, 'Duplicate listed revision'); seen.add(r['revision'])
            for f in ('approved_by','approval_note'): nonempty(r,f)
            check(r['audience'] in ('review','readers') and type(r['listed']) is bool, 'Invalid catalogue entry')
            obj = load_snapshot(root,r['work'],r['edition'],r['revision'])
            if r['audience']=='readers':
                check(obj['edition']['status']=='ready' and not obj.get('missing',obj.get('missing_sections')), 'Reader listing needs a complete ready edition')
            results.append((r,obj))
    return results

def validate_run(run: dict, root: Path | None = None) -> None:
    check(run.get('schema_version')==1, 'Unknown run schema')
    for f in ('id','operation','created_at','interface','model_label','context_completeness'): nonempty(run,f)
    ident(run['id'])
    for key in ('inputs','outputs','prompts'):
        check(isinstance(run.get(key),list), f'Run lacks {key}')
    check(bool(run['prompts']), 'Generation run needs a captured prompt')
    for item in run['prompts']+run['inputs']:
        check(item['sha256']==digest(item['text'].encode()), 'Run context text/hash mismatch')
    for item in run['outputs']:
        check(bool(HASH.fullmatch(item.get('sha256',''))), 'Run output lacks SHA-256')
        path = Path(item['path'])
        check(not path.is_absolute() and '..' not in path.parts, 'Unsafe run output path')
    # Historical output hashes do not have to match the current editable file.

def record_run(root: Path, work_id: str, edition_id: str, model: str, interface: str,
               operation: str, prompts: list[Path], extra: str, output: list[Path],
               *, captured_inputs: list[dict] | None = None) -> Path:
    from datetime import datetime, timezone
    from uuid import uuid4
    root = root.resolve()
    ident(work_id); ident(edition_id)
    workdir = root/'books'/work_id
    if not workdir.exists(): workdir = root/'examples'/work_id
    work, ed, eddir = load_work(workdir,edition_id)
    def capture(path: Path):
        path = path.resolve(); check(path.is_relative_to(root.resolve()), 'Context must be inside repository')
        text = path.read_text(encoding='utf-8')
        return {'path':path.relative_to(root).as_posix(),'sha256':digest(text.encode()),'text':text}
    captured_prompts = [capture(p) for p in prompts]
    if extra: captured_prompts.append({'path':'session-instructions','text':extra,'sha256':digest(extra.encode())})
    note_paths = [root/'docs/editorial-policy.md',workdir/'notes.md',eddir/'notes.md',eddir/'glossary.md']
    inputs = captured_inputs if captured_inputs is not None else [capture(p) for p in note_paths if p.exists()]
    outputs = []
    for path in output:
        path = path.resolve(); check(path.is_relative_to(eddir.resolve()), 'Output must be inside this edition')
        outputs.append({'path':path.relative_to(root).as_posix(),'sha256':digest(path.read_bytes())})
    run = {'schema_version':1,'id':'run-'+uuid4().hex,'operation':operation,'created_at':datetime.now(timezone.utc).isoformat(),
           'work':work_id,'edition':edition_id,'interface':interface,'model_label':model,'model_snapshot':None,
           'context_completeness':'Captured project prompts, notes and supplied session instructions; not a complete ChatGPT conversation or hidden system context.',
           'source_fingerprint':source_fingerprint(workdir),'git_context':git_context(root),'prompts':captured_prompts,'inputs':inputs,'outputs':outputs}
    validate_run(run,root); path = eddir/'runs'/(run['id']+'.json'); write_json(path,run)
    ed['production'].setdefault('runs',[]).append(run['id']); write_json(eddir/'edition.json',ed)
    return path

def validate_review(report: dict, root: Path = ROOT) -> dict:
    if report.get('schema_version')==1: return legacy.validate_review(report,root)
    check(report.get('schema_version')==2, 'Unknown report schema')
    for f in ('report_id','created_at'): nonempty(report,f)
    check(report.get('repository')==read_json(root/'project.json')['repository'], 'Wrong report repository')
    snap = load_snapshot(root,report['work'],report['edition'],report['revision'])
    check(is_tree(snap), 'A v2 report requires a tree snapshot')
    fields = field_map(snap); ids=set()
    check(isinstance(report.get('annotations'),list) and bool(report['annotations']), 'No annotations')
    for note in report['annotations']:
        nid = nonempty(note,'id'); check(nid not in ids,'Duplicate annotation'); ids.add(nid)
        nonempty(note,'comment')
        key = f'{note.get("node")}:{note.get("field")}'
        check(key in fields, 'Unknown node/field')
        check(note.get('scope') in ('text','field'), 'Unknown observation scope')
        if note['scope']=='field':
            check(note.get('anchor') is None,'Whole-field observation must not have offsets'); continue
        a = note.get('anchor'); check(isinstance(a,dict) and a.get('unit')=='utf16-code-units','Missing UTF-16 anchor')
        text = fields[key]['text']; selected = utf16_slice(text,a['start'],a['end'])
        check(bool(selected) and selected==a['exact'],'Quoted text does not match this revision')
        check(isinstance(a.get('prefix'),str) and isinstance(a.get('suffix'),str),'Missing quotation context')
        check(utf16_slice(text,0,a['start']).endswith(a['prefix']),'Prefix mismatch')
        check(utf16_slice(text,a['end'],len(text.encode('utf-16-le'))//2).startswith(a['suffix']),'Suffix mismatch')
    return {'revision':report['revision'],'annotations':len(ids),'anchors':'valid'}

def validate_project(root: Path = ROOT) -> dict:
    config=read_json(root/'project.json'); schema(config); nonempty(config,'name')
    check(bool(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',config['repository'])),'Invalid repository')
    editions, works, snapshots, runs=0,0,0,0
    for parent in ('books','examples'):
        for path in (root/parent).glob('*/work.json'):
            validate_work(path.parent); works+=1
            for edpath in (path.parent/'editions').glob('*/edition.json'):
                load_work(path.parent,edpath.parent.name); editions+=1
                for run in (edpath.parent/'runs').glob('*.json'):
                    validate_run(read_json(run),root); runs+=1
    for path in (root/'revisions').glob('*/*/*.json'):
        load_snapshot(root,path.parents[1].name,path.parent.name,path.stem); snapshots+=1
    load_catalog(root,False)
    if (root/'examples/catalog.json').exists(): load_catalog(root,True)
    if (root/'queue.json').exists():
        from intake import validate_queue
        queue=read_json(root/'queue.json')
        validate_queue(queue,config)
    from translation_jobs import prompt_catalogue, validate_results
    prompt_catalogue(root); validate_results(root)
    from guide_requests import guide_prompt, validate_guide_results
    if (root/'prompts/whole-work-guide.md').is_file(): guide_prompt(root)
    validate_guide_results(root)
    from independent_guide_jobs import validate_records
    validate_records(root)
    from translation_jobs import _guide
    for pointer in (root/'books').glob('*/reference/current.json'):
        _guide(pointer.parent)
    for pointer in (root/'books').glob('*/editions/*/reference/current.json'):
        _guide(pointer.parent)
    from acquire_queue import validate_record
    for rights_path in (root/'books').glob('*/rights.json'):
        record=read_json(rights_path)
        check(type(record.get('ebook_id')) is int and 0<record['ebook_id']<10_000_000, 'Invalid rights record Gutenberg ID')
        check(rights_path.parent.name == f"gutenberg-{record['ebook_id']}", 'Rights record directory mismatch')
        validate_record(rights_path.parent,record['ebook_id'])
    return {'works':works,'editable_editions':editions,'frozen_snapshots':snapshots,'generation_runs':runs,
            'note':'Structure, provenance and exact references only; not a literary quality guarantee.'}

def build(root: Path = ROOT, demo: bool = False, epub: bool = False) -> Path:
    from site_builder import build_site
    return build_site(root,demo,epub)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',action='version',version=VERSION)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('validate')
    p=sub.add_parser('snapshot'); p.add_argument('work_directory',type=Path); p.add_argument('edition_id')
    p=sub.add_parser('build'); p.add_argument('--demo',action='store_true'); p.add_argument('--epub',action='store_true')
    p=sub.add_parser('check-review'); p.add_argument('report',type=Path)
    p=sub.add_parser('acquire-queued'); p.add_argument('--output',type=Path,default=ROOT/'build/source-downloads')
    p=sub.add_parser('stage-acquisitions'); p.add_argument('--output',type=Path,default=ROOT/'build/source-downloads')
    p=sub.add_parser('source-fetch'); p.add_argument('gutenberg_id',type=int)
    p=sub.add_parser('source-prepare'); p.add_argument('raw_file',type=Path); p.add_argument('work_directory',type=Path)
    p=sub.add_parser('source-apply'); p.add_argument('work_directory',type=Path); p.add_argument('plan',type=Path)
    p=sub.add_parser('catalogue-refresh'); p.add_argument('--csv',type=Path)
    p=sub.add_parser('intake'); p.add_argument('--issues',type=Path); p.add_argument('--github',action='store_true')
    p=sub.add_parser('translation-intake'); p.add_argument('--issues',type=Path); p.add_argument('--github',action='store_true')
    sub.add_parser('translation-pending')
    p=sub.add_parser('guide-intake'); p.add_argument('--issues',type=Path); p.add_argument('--github',action='store_true')
    sub.add_parser('guide-pending')
    sub.add_parser('guide-task-plan', help='Read-only work/target guide discovery')
    p=sub.add_parser('guide-task-export', help='Create one independent guide ZIP; never submit')
    p.add_argument('task_type', choices=['work_analysis','target_guide'])
    p.add_argument('work'); p.add_argument('--target')
    p.add_argument('--model', default='6 Extra High'); p.add_argument('--attempt', default='initial')
    p.add_argument('--force', action='store_true'); p.add_argument('--output', type=Path, required=True)
    p=sub.add_parser('guide-task-import', help='Import a guide with its exact original request ZIP')
    p.add_argument('request_zip', type=Path); p.add_argument('response_zip', type=Path)
    sub.add_parser('prompt-list')
    p=sub.add_parser('translation-export'); p.add_argument('issue',type=int); p.add_argument('--output',type=Path,required=True); p.add_argument('--model',default='6 Extra High')
    p=sub.add_parser('translation-preview', help='Write the exact assembled input for an accepted v2 request')
    p.add_argument('issue',type=int); p.add_argument('--output',type=Path)
    p=sub.add_parser('translation-import'); p.add_argument('response_zip',type=Path)
    p=sub.add_parser('guide-export'); p.add_argument('work',nargs='?'); p.add_argument('target',nargs='?'); p.add_argument('--issue',type=int); p.add_argument('--output',type=Path,required=True); p.add_argument('--model',default='6 Extra High')
    p=sub.add_parser('guide-import'); p.add_argument('response_zip',type=Path)
    p=sub.add_parser('task'); p.add_argument('--output',type=Path,default=ROOT/'build/next-task.md')
    p=sub.add_parser('record-run'); p.add_argument('work'); p.add_argument('edition'); p.add_argument('--model',required=True); p.add_argument('--interface',default='chatgpt'); p.add_argument('--operation',default='translation'); p.add_argument('--prompt',type=Path,action='append',required=True); p.add_argument('--instructions',default=''); p.add_argument('--output',type=Path,action='append',required=True)
    p=sub.add_parser('relay-package', help='Prepare a local ZIP; never submit')
    p.add_argument('work'); p.add_argument('edition'); p.add_argument('--node', action='append', required=True)
    p.add_argument('--context-node', action='append', default=[]); p.add_argument('--model', default='6 Extra High')
    p.add_argument('--material', action='append', default=[], help='Ordered material ID@SHA-256; repeat to add')
    p.add_argument('--language'); p.add_argument('--direction', choices=['ltr','rtl'], default='ltr')
    p.add_argument('--kind', choices=['translation','modernization'], default='translation')
    p=sub.add_parser('relay-import', help='Validate and import one returned ZIP as a draft')
    p.add_argument('attempt'); p.add_argument('result', type=Path)
    p.add_argument('--observed-model', default='unknown'); p.add_argument('--chat-url')
    p=sub.add_parser('relay-recover', help='Restore a verified prior edition after an interrupted direct import')
    p.add_argument('attempt')
    p=sub.add_parser('relay-direct-reconcile', help='Import exact completed, authorized direct relay results')
    p.add_argument('--relay',type=Path,default=Path.home()/'Software/chatgpt-relay')
    p=sub.add_parser('relay-coordinator', help='Opt-in local package, submit and import coordination')
    p.add_argument('--relay',type=Path,default=Path.home()/'Software/chatgpt-relay')
    modes=p.add_subparsers(dest='mode',required=True)
    modes.add_parser('status',help='Read-only plan and attempt status')
    modes.add_parser('sync',help='Prepare eligible guide tasks from accepted requests; never submit')
    q=modes.add_parser('prepare',help='Archive one task; never submit')
    choice=q.add_mutually_exclusive_group(required=True)
    choice.add_argument('--guide-issue',type=int); choice.add_argument('--translation-issue',type=int)
    choice.add_argument('--task-type',choices=['work_analysis','target_guide'])
    q.add_argument('--work'); q.add_argument('--target'); q.add_argument('--model',default='6 Extra High')
    q.add_argument('--retry-of')
    q=modes.add_parser('adopt',help='Archive an already prepared compatible request ZIP')
    q.add_argument('request_zip',type=Path)
    q=modes.add_parser('submit',help='Explicitly authorize and atomically deliver this attempt')
    q.add_argument('attempt'); q.add_argument('--authorization',required=True)
    q=modes.add_parser('reconcile',help='Observe relay status; optionally import valid returned files')
    q.add_argument('--import-ready',action='store_true')
    q.add_argument('--recover-completed',action='store_true',
                   help='Recheck earlier transport holds only when their exact relay result is complete')
    q=modes.add_parser('resume',help='Retry observation/import after review; never resend')
    q.add_argument('attempt')
    q=modes.add_parser('publish',help='Approve exact imported files for public Git distribution')
    q.add_argument('attempt'); q.add_argument('--approve-git-distribution',action='store_true')
    q.add_argument('--push',action='store_true')
    q=sub.add_parser('draft-publish',help='Publish imported draft guides and translations under standing policy')
    q.add_argument('--no-push',action='store_true',help='Commit locally without pushing (offline verification)')
    args=parser.parse_args()
    try:
        if args.command=='validate': result=validate_project()
        elif args.command=='draft-publish':
            from draft_distribution import publish_ready
            result=publish_ready(ROOT,not args.no_push)
        elif args.command=='relay-coordinator':
            import relay_coordinator as coordinator
            if args.mode=='status':result=coordinator.status(ROOT)
            elif args.mode=='sync':result=coordinator.sync_proposals(ROOT,args.relay)
            elif args.mode=='prepare':
                result=coordinator.prepare(ROOT,args.relay,args.guide_issue,args.translation_issue,
                    args.task_type,args.work,args.target,args.model,args.retry_of)
            elif args.mode=='adopt':result=coordinator.adopt(ROOT,args.request_zip,args.relay)
            elif args.mode=='submit':result=coordinator.submit(ROOT,args.attempt,args.authorization)
            elif args.mode=='reconcile':
                check(not args.recover_completed or args.import_ready,
                      '--recover-completed requires --import-ready')
                result=coordinator.reconcile(ROOT,args.import_ready,args.recover_completed)
            elif args.mode=='resume':result=coordinator.resume(ROOT,args.attempt)
            else:result=coordinator.publish(ROOT,args.attempt,args.approve_git_distribution,args.push)
        elif args.command=='relay-package':
            from translation_relay import package
            result=package(ROOT,args.work,args.edition,args.node,args.model,args.language,args.direction,args.kind,args.context_node,args.material)
        elif args.command=='relay-import':
            from translation_relay import import_result
            result=import_result(ROOT,args.attempt,args.result,args.observed_model,args.chat_url)
        elif args.command=='relay-recover':
            from translation_relay import recover_interrupted_import
            result=recover_interrupted_import(ROOT,args.attempt)
        elif args.command=='relay-direct-reconcile':
            from relay_completed import import_direct_completed
            result=import_direct_completed(ROOT,args.relay)
        elif args.command=='snapshot':
            rev,path=freeze(args.work_directory,args.edition_id); result={'revision':rev,'path':str(path),'published':False}
        elif args.command=='build': result={'built':str(build(demo=args.demo,epub=args.epub)),'deployed':False}
        elif args.command=='check-review': result=validate_review(read_json(args.report))
        elif args.command=='acquire-queued':
            from acquire_queue import acquire_queued
            result=acquire_queued(ROOT,args.output)
        elif args.command=='stage-acquisitions':
            from acquire_queue import stage_acquisitions
            stage_acquisitions(ROOT,args.output); result={'staged':'Only validated acquisition files and rights records from this run'}
        elif args.command=='translation-intake':
            from translation_jobs import intake
            from intake import fetch_issues
            check(args.issues is not None or args.github,'Provide trusted issues export or --github')
            issues=read_json(args.issues) if args.issues is not None else fetch_issues(read_json(ROOT/'project.json')['repository'])
            result=intake(ROOT,issues)
        elif args.command=='guide-intake':
            from guide_requests import intake_guide
            from intake import fetch_issues
            check(bool(args.issues)!=bool(args.github),'Choose --issues file or --github')
            issues=fetch_issues(read_json(ROOT/'project.json')['repository']) if args.github else read_json(args.issues)
            result=intake_guide(ROOT,issues)
        elif args.command=='guide-task-plan':
            from guide_task_planner import discover
            result=discover(ROOT)
        elif args.command=='guide-task-export':
            from independent_guide_jobs import export
            result=export(ROOT,args.task_type,args.work,args.target,args.output,
                          args.model,args.attempt,args.force)
        elif args.command=='guide-task-import':
            from independent_guide_jobs import import_result
            result=import_result(ROOT,args.request_zip,args.response_zip)
        elif args.command=='guide-pending':
            from guide_requests import pending_guides
            result=pending_guides(ROOT)
        elif args.command=='translation-pending':
            from translation_jobs import validate_queue
            entries=validate_queue(ROOT)['requests']
            result={'requests':[{'issue':e['issue'],'work':e['request']['work'],'target':e['request']['target']}
                                for e in entries if not (ROOT/'translation-results'/('issue-'+str(e['issue'])+'.json')).exists()]}
        elif args.command=='prompt-list':
            from translation_jobs import prompt_catalogue
            result={'prompts':prompt_catalogue(ROOT)}
        elif args.command=='translation-export':
            from translation_jobs import export_translation
            result=export_translation(ROOT,args.issue,args.output,args.model)
        elif args.command=='translation-preview':
            from translation_jobs import prepare_job,request_entry
            job,manifest=prepare_job(ROOT,request_entry(ROOT,args.issue))
            check('assembled_input' in job,'An accepted v2 materials request is required')
            output=args.output or ROOT/'build'/('translation-preview-'+str(args.issue)+'.md')
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(job['assembled_input'],encoding='utf-8')
            result={'output':str(output),'job_sha256':manifest['job_sha256'],
                    'input_sha256':digest(job['assembled_input'].encode()),'submitted':False}
        elif args.command=='translation-import':
            from translation_jobs import import_translation
            result=import_translation(ROOT,args.response_zip)
        elif args.command=='guide-export':
            if args.issue is None:
                from translation_jobs import export_guide
                check(args.work is not None and args.target is not None,
                      'Pass WORK TARGET, or use --issue ISSUE')
                result=export_guide(ROOT,args.work,args.target,args.output,args.model)
            else:
                from guide_requests import export_guide_issue
                check(args.work is None and args.target is None,
                      '--issue exports use the saved work/target request')
                result=export_guide_issue(ROOT,args.issue,args.output,args.model)
        elif args.command=='guide-import':
            from translation_jobs import import_guide
            result=import_guide(ROOT,args.response_zip)
        elif args.command=='source-fetch':
            from source_import import fetch_gutenberg
            result=fetch_gutenberg(ROOT,args.gutenberg_id)
        elif args.command=='source-prepare':
            b=prepare(args.raw_file,args.work_directory/'acquisition'); result={'blocks':len(b['blocks']),'blocks_sha256':object_hash(b)}
        elif args.command=='source-apply': result=apply(args.work_directory,args.plan)
        elif args.command=='catalogue-refresh':
            from intake import refresh_catalogue
            result=refresh_catalogue(ROOT,args.csv)
        elif args.command=='intake':
            from intake import import_issues, fetch_issues
            check(bool(args.issues)!=bool(args.github),'Choose --issues file or --github')
            issues=fetch_issues(read_json(ROOT/'project.json')['repository']) if args.github else read_json(args.issues)
            result=import_issues(ROOT,issues)
        elif args.command=='task':
            from intake import task_brief
            text=task_brief(ROOT); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding='utf-8'); result={'task':str(args.output),'model_called':False}
        else:
            result={'record':str(record_run(ROOT,args.work,args.edition,args.model,args.interface,args.operation,args.prompt,args.instructions,args.output))}
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except (ProjectError,KeyError,TypeError,ValueError,OSError) as exc:
        print(f'Error: {exc}',file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
