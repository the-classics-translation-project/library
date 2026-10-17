"""AI proposes block ownership; code preserves text and assigns opaque node IDs.

This module deliberately makes no model/API calls. Plans are ordinary JSON files.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from legacy_v1 import ProjectError, check, digest, object_hash, read_json, write_json

NODE_ID = re.compile(r'n[0-9]{4,}')

def walk(tree: dict, depth: int = 0):
    check(depth <= 128, 'Tree exceeds the defensive nesting limit of 128')
    check(isinstance(tree, dict), 'Each node must be an object')
    yield tree, depth
    children = tree.get('children', [])
    check(isinstance(children, list), 'children must be an array')
    for child in children:
        yield from walk(child, depth + 1)

def validate_tree(tree: dict) -> list[dict]:
    nodes = [n for n, _ in walk(tree)]
    ids = []
    for n in nodes:
        check(isinstance(n.get('id'), str) and bool(NODE_ID.fullmatch(n['id'])), 'Use an opaque ID such as n0001')
        check(set(n) <= {'id', 'label', 'text', 'children', 'source_refs'}, 'Unknown node field')
        ids.append(n['id'])
        if 'label' in n: check(isinstance(n['label'], str) and bool(n['label'].strip()), 'Absent labels must be omitted, not empty')
        if 'text' in n: check(isinstance(n['text'], str) and bool(n['text']), 'text must be a file path')
    check(len(ids) == len(set(ids)), 'Duplicate node IDs')
    return nodes

def prepare(raw_path: Path, dest: Path) -> dict:
    """Preserve received bytes; split a reversible normalized UTF-8 view.

    This first importer supports TXT/Markdown, not arbitrary HTML or PDFs.
    Acquisition and exclusions are explicit, never guessed from a book title.
    """
    check(raw_path.suffix.lower() in {'.txt', '.md'}, 'Import TXT/Markdown. Convert other formats explicitly and retain the original separately.')
    check(not any((dest/name).exists() for name in ('acquired.txt','normalized.txt','blocks.json')), 'Acquisition files already exist; inspect incomplete preparation instead of overwriting source bytes')
    raw = raw_path.read_bytes()
    check(len(raw) <= 64 * 1024 * 1024, 'Source exceeds 64 MiB limit')
    text = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    check(bool(text.strip()) and '\x00' not in text, 'Source is empty or contains NUL')
    blocks, pos = [], 0
    for i, m in enumerate(re.finditer(r'.+?(?:\n[ \t]*\n+|\Z)', text, re.S), 1):
        check(m.start() == pos, 'Block segmentation left a gap')
        block = m.group()
        blocks.append({'id': f'b{i:06d}', 'start': m.start(), 'end': m.end(), 'text': block, 'sha256': digest(block.encode())})
        pos = m.end()
    check(pos == len(text), 'Block segmentation incomplete')
    dest.mkdir(parents=True, exist_ok=True)
    (dest/'acquired.txt').write_bytes(raw)
    (dest/'normalized.txt').write_text(text, encoding='utf-8')
    record = {'schema_version': 1, 'raw_sha256': digest(raw), 'normalized_sha256': digest(text.encode()),
              'normalization': ['UTF-8 BOM removed if present', 'CRLF and CR converted to LF; no other textual changes'], 'blocks': blocks}
    write_json(dest/'blocks.json', record)
    return record

def validate_blocks(dest: Path) -> dict:
    record = read_json(dest/'blocks.json')
    check(digest((dest/'acquired.txt').read_bytes()) == record['raw_sha256'], 'Acquired source bytes changed')
    text = (dest/'normalized.txt').read_text(encoding='utf-8')
    check(digest(text.encode()) == record['normalized_sha256'], 'Normalized source changed')
    pos, seen = 0, set()
    for b in record['blocks']:
        check(b['id'] not in seen, 'Duplicate block ID'); seen.add(b['id'])
        check(b['start'] == pos and b['end'] > pos and b['text'] == text[pos:b['end']], 'Source block position mismatch')
        check(digest(b['text'].encode()) == b['sha256'], 'Source block hash mismatch')
        pos = b['end']
    check(pos == len(text), 'Source blocks do not cover normalized source')
    return record

def expand_refs(refs: list, blocks: list[dict]) -> list[str]:
    check(isinstance(refs, list), 'Block references must be an array')
    ids = [b['id'] for b in blocks]
    index = {bid: i for i, bid in enumerate(ids)}
    result = []
    for ref in refs:
        if isinstance(ref, str):
            check(ref in index, f'Unknown source block {ref}'); result.append(ref)
        else:
            check(isinstance(ref, list) and len(ref) == 2 and all(x in index for x in ref), 'Expected [first_block,last_block] range')
            start, end = (index[x] for x in ref)
            check(start <= end, 'Reversed block range')
            result.extend(ids[start:end + 1])
    return result

def compile_plan(record: dict, plan: dict) -> tuple[dict, dict[str, str], dict]:
    check(plan.get('blocks_sha256') == object_hash(record), 'Plan belongs to another source-block revision')
    blocks = record['blocks']; by_id = {b['id']: b for b in blocks}
    used, outputs = [], {}
    counter = 0
    def refs(spec, field):
        result = expand_refs(spec.get(field, []), blocks)
        used.extend(result)
        return result
    def node(spec, depth=0):
        nonlocal counter
        check(depth <= 128 and isinstance(spec, dict), 'Invalid/deep structure proposal')
        check(set(spec) <= {'label_blocks','text_blocks','children'}, 'AI plan must reference source blocks, not invent labels, text or IDs')
        counter += 1; nid = f'n{counter:04d}'
        result = {'id': nid}
        lab = refs(spec, 'label_blocks'); body = refs(spec, 'text_blocks')
        if lab:
            result['label'] = '\n'.join(by_id[x]['text'].strip() for x in lab)
            check(bool(result['label']), 'An empty block cannot label a node')
        if body:
            result['text'] = f'source/{nid}.md'
            outputs[result['text']] = ''.join(by_id[x]['text'] for x in body)
            check(bool(outputs[result['text']].strip()), 'Empty body node')
        result['source_refs'] = {'label':lab,'text':body}
        if spec.get('children'): result['children'] = [node(c, depth+1) for c in spec['children']]
        return result
    tree = node(plan['tree'])
    excluded = []
    for exclusion in plan.get('excluded', []):
        check(isinstance(exclusion.get('reason'), str) and bool(exclusion['reason'].strip()), 'Every exclusion needs a reason')
        excluded.extend(expand_refs(exclusion['blocks'], blocks))
    assigned = used + excluded
    check(len(assigned) == len(set(assigned)), 'A source block was used or excluded more than once')
    check(set(assigned) == set(by_id), 'Some source blocks are unaccounted for')
    source_order = [b['id'] for b in blocks if b['id'] not in set(excluded)]
    check(used == source_order, 'Tree changes source reading order; use unlabeled children for interleaved prose')
    validate_tree(tree)
    audit = {'schema_version': 1, 'blocks_sha256':object_hash(record), 'plan_sha256':object_hash(plan),
             'tree_sha256':object_hash(tree), 'assigned_blocks':len(used), 'excluded_blocks':len(excluded),
             'next_node_number':counter + 1,
             'claim':'Every normalized block is accounted for once, in order. This does not prove the hierarchy is correct.'}
    return tree, outputs, audit

def apply(work_dir: Path, plan_path: Path) -> dict:
    check(not (work_dir/'structure.json').exists(), 'Tree already exists. Use a documented migration; never reassign established IDs')
    record = validate_blocks(work_dir/'acquisition')
    plan = read_json(plan_path)
    tree, files, audit = compile_plan(record, plan)
    for name in files: check(not (work_dir/name).exists(), f'Would overwrite source {name}')
    for name, text in files.items():
        p = work_dir/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')
    write_json(work_dir/'structure.json', tree)
    write_json(work_dir/'acquisition/plan.json', plan)
    write_json(work_dir/'acquisition/audit.json', audit)
    return audit

def fetch_gutenberg(root: Path, ebook_id: int) -> dict:
    """Fetch one official UTF-8 text package. Never overwrite an acquisition."""
    from urllib.request import Request, urlopen
    from datetime import datetime, timezone
    from tempfile import TemporaryDirectory
    check(type(ebook_id) is int and 0 < ebook_id < 10_000_000, 'Invalid Gutenberg ID')
    dest=root/'books'/f'gutenberg-{ebook_id}'/'acquisition'
    check(not dest.exists(), 'An acquisition already exists; do not replace it')
    url=f'https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt'
    with urlopen(Request(url,headers={'User-Agent':'ClassicsTranslationProject/0.1 (single book download)'}),timeout=45) as response:
        content_type=response.headers.get('Content-Type','')
        check('html' not in content_type.lower(), 'Provider returned HTML rather than a text package')
        raw=response.read(64*1024*1024+1)
        final_url=response.geturl()
    check(len(raw)<=64*1024*1024, 'Source too large')
    text=raw.decode('utf-8-sig')
    check('PROJECT GUTENBERG' in text[:12000].upper(), 'Unexpected source response; inspect it before import')
    # Prepare in a temporary sibling; failed validation leaves no canonical source.
    dest.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=dest.parent) as tmp:
        t=Path(tmp);(t/'download.txt').write_bytes(raw);record=prepare(t/'download.txt',t/'acquisition')
        manifest={'schema_version':1,'provider':'gutenberg','ebook_id':ebook_id,'requested_url':url,'resolved_url':final_url,
                  'retrieved_at':datetime.now(timezone.utc).isoformat(),'raw_sha256':digest(raw),
                  'source_edition_verified':False,'rights_checked':False}
        write_json(t/'acquisition/provenance.json',manifest)
        (t/'acquisition').replace(dest)
    return {'work':f'gutenberg-{ebook_id}','blocks':len(record['blocks']),'raw_sha256':digest(raw),'next':'Verify source edition and rights, then propose the source tree.'}
