"""Maintainer-authorized whole-work guide requests for offline ChatGPT ZIP exchange.

The literary glossary remains free-form Markdown. Only the Issue/ZIP envelope
has a strict machine-readable schema; it never invokes a model.
"""
from __future__ import annotations

from pathlib import Path
import json
import re

from legacy_v1 import check, read_json, write_json, digest, object_hash, ProjectError
from translation_jobs import (
    HASH, prepare_guide, render_prompt, zip_files, GUIDE_README, relay_readme
)

GUIDE_MARKER = '<!-- ctp:guide-request:v1 -->'
PROMPT_FILE = 'prompts/whole-work-guide.md'


def guide_prompt(root: Path) -> str:
    path=root/PROMPT_FILE
    check(path.is_file(), 'Missing whole-work guide prompt')
    text=path.read_text(encoding='utf-8')
    check(bool(text.strip()) and len(text)<=100000, 'Invalid guide prompt length')
    return text


def validate_guide_request(root: Path, request: dict, pinned_prompt: str | None = None) -> None:
    check(isinstance(request,dict) and
          set(request)=={'schema_version','work','target','source_fingerprint','prompt_sha256'} and
          type(request['schema_version']) is int and request['schema_version']==1,
          'Unknown whole-work guide request schema')
    work=request['work'];target=request['target']
    check(isinstance(work,str) and re.fullmatch(r'gutenberg-[0-9]{1,7}',work),
          'Invalid requested source')
    check(isinstance(target,str), 'Invalid target language')
    check(isinstance(request['source_fingerprint'],str) and
          HASH.fullmatch(request['source_fingerprint']), 'Invalid source fingerprint')
    check(isinstance(request['prompt_sha256'],str) and
          HASH.fullmatch(request['prompt_sha256']), 'Invalid guide prompt fingerprint')
    template=pinned_prompt if pinned_prompt is not None else guide_prompt(root)
    check(isinstance(template,str) and
          digest(template.encode('utf-8'))==request['prompt_sha256'],
          'Guide prompt changed since Issue creation')
    # Reuses the existing work/rights/target validation and source fingerprint.
    job,_=prepare_guide(root,work,target,guide_template=template)
    check(job['source_fingerprint']==request['source_fingerprint'],
          'Guide request refers to a different source revision')
    from translation_jobs import ALLOWED, VARIABLE
    check(set(VARIABLE.findall(template))<=ALLOWED and
          '{{' not in VARIABLE.sub('',template), 'Unsupported guide prompt template')
    # Reject missing substitutions or malformed placeholders, not prose formatting.
    variables=_variables(root,work,target)
    render_prompt(template,variables)


def _variables(root: Path, work: str, target: str) -> dict:
    from translation_jobs import _ctp
    c=_ctp()
    metadata,tree=c.validate_work(root/'books'/work)
    config=read_json(root/'project.json')
    language=next(row['label'] for row in config['targets'] if row['id']==target)
    return {'target_language':language,'target_language_code':target,
            'source_language':metadata['language'],
            'work_title':tree.get('label',work)}


def parse_guide_issue(root: Path, issue: dict) -> dict | None:
    if issue.get('pull_request') or issue.get('state')!='open':
        return None
    body=issue.get('body') or ''
    if GUIDE_MARKER not in body:
        return None
    config=read_json(root/'project.json')
    check(issue.get('user',{}).get('login') in config['maintainers'],
          'Guide request author is not an authorized maintainer')
    check(type(issue.get('number')) is int and issue['number']>0, 'Invalid Issue number')
    check(isinstance(body,str) and len(body)<=65000 and
          body.count(GUIDE_MARKER)==1, 'Duplicate or oversized guide Issue marker')
    section=body.split(GUIDE_MARKER,1)[1]
    fence=re.escape(chr(96)*3)
    match=re.fullmatch(r'\s*'+fence+r'json\s*\n([\s\S]+?)\n'+fence+r'\s*',section)
    check(match is not None,'Expected exactly one final JSON guide request block')
    from legacy_v1 import pairs, invalid_constant
    request=json.loads(match.group(1),object_pairs_hook=pairs,parse_constant=invalid_constant)
    validate_guide_request(root,request)
    return request


def intake_guide(root: Path, issues: list[dict]) -> dict:
    path=root/'guide-requests.json'
    queue=read_json(path) if path.exists() else {'schema_version':1,'requests':[]}
    check(queue.get('schema_version')==1 and isinstance(queue.get('requests'),list),
          'Invalid guide request queue')
    before=object_hash(queue)
    seen={entry['issue'] for entry in queue['requests']}
    accepted,rejected=[],[]
    for issue in sorted(issues,key=lambda row:row.get('number',0)):
        try:
            if issue.get('number') in seen: continue
            request=parse_guide_issue(root,issue)
            if request is None: continue
            queue['requests'].append({
                'issue':issue['number'],'author':issue['user']['login'],
                'body_sha256':digest(issue['body'].encode('utf-8')),
                'request':request,'prompt_text':guide_prompt(root)
            })
            seen.add(issue['number']);accepted.append(issue['number'])
        except (ProjectError,KeyError,TypeError,ValueError,AttributeError) as exc:
            rejected.append({'issue':issue.get('number'),'reason':str(exc)})
    changed=object_hash(queue)!=before
    if changed:write_json(path,queue)
    return {'changed':changed,'accepted':accepted,'rejected':rejected,
            'requests':len(queue['requests']),'ai_called':False}


def validate_guide_queue(root: Path) -> dict:
    path=root/'guide-requests.json'
    data=read_json(path) if path.exists() else {'schema_version':1,'requests':[]}
    check(data.get('schema_version')==1 and isinstance(data.get('requests'),list),
          'Invalid guide request queue')
    seen=set()
    config=read_json(root/'project.json')
    for entry in data['requests']:
        issue=entry['issue']
        check(type(issue) is int and issue>0 and issue not in seen,
              'Duplicate guide Issue')
        seen.add(issue)
        check(entry['author'] in config['maintainers'], 'Untrusted guide author')
        check(isinstance(entry['body_sha256'],str) and
              HASH.fullmatch(entry['body_sha256']), 'Invalid guide Issue evidence')
        validate_guide_request(root,entry['request'],entry['prompt_text'])
    return data


def guide_entry(root: Path, issue: int) -> dict:
    for entry in validate_guide_queue(root)['requests']:
        if entry['issue']==issue: return entry
    raise ProjectError('Unknown whole-work guide request Issue')


def prepare_guide_issue(root: Path, entry: dict) -> tuple[dict,dict]:
    request=entry['request']
    validate_guide_request(root,request,entry['prompt_text'])
    job,manifest=prepare_guide(root,request['work'],request['target'],
                               guide_template=entry['prompt_text'])
    job['issue']=entry['issue']
    job['guide_instructions']=render_prompt(
        entry['prompt_text'],_variables(root,request['work'],request['target']))
    job['request']=request
    manifest['issue']=entry['issue']
    manifest['job_sha256']=digest(json.dumps(
        job,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    return job,manifest


def export_guide_issue(root: Path, issue: int, output: Path, model: str = '6 Extra High') -> dict:
    entry=guide_entry(root,issue)
    job,manifest=prepare_guide_issue(root,entry)
    zip_files(output,{'README.md':relay_readme(GUIDE_README,output,model),
                      'input/job.json':job,'input/manifest.json':manifest})
    return {'issue':issue,'package':str(output),'nodes':len(job['source_nodes']),
            'job_sha256':manifest['job_sha256'],'ai_called':False}


def pending_guides(root: Path) -> dict:
    rows=[]
    for entry in validate_guide_queue(root)['requests']:
        issue=entry['issue']
        if not (root/'guide-results'/('issue-'+str(issue)+'.json')).exists():
            rows.append({'issue':issue,'work':entry['request']['work'],
                         'target':entry['request']['target']})
    return {'requests':rows,'ai_called':False}


def validate_guide_results(root: Path) -> None:
    issues={r['issue']:r['request'] for r in validate_guide_queue(root)['requests']}
    for path in (root/'guide-results').glob('issue-*.json'):
        item=read_json(path)
        issue=item.get('issue')
        check(type(issue) is int and issue in issues and
              path.name=='issue-'+str(issue)+'.json','Orphan guide import')
        for key in ('response_sha256','job_sha256'):
            check(isinstance(item.get(key),str) and HASH.fullmatch(item[key]),
                  'Invalid guide result hash')
        check(item.get('work')==issues[issue]['work'] and
              item.get('target')==issues[issue]['target'],
              'Guide result work/target mismatch')
        files=item.get('files')
        check(isinstance(files,dict) and set(files)=={'work_guide','target_guide'},
              'Invalid guide result files')
        for field,value in files.items():
            check(isinstance(value,str), 'Invalid guide file path')
            pathname=Path(value)
            check(not pathname.is_absolute() and '..' not in pathname.parts and
                  pathname.suffix=='.md' and HASH.fullmatch(pathname.stem),
                  'Guide content must be a relative hash-named Markdown path')
            actual=(root/pathname).read_bytes()
            check(digest(actual)==pathname.stem,'Historical guide was altered')
        record=item.get('run_record')
        check(isinstance(record,str) and not Path(record).is_absolute() and
              '..' not in Path(record).parts and (root/record).is_file(),
              'Guide result provenance record missing')
