"""Opt-in local relay coordination. No browser calls, model API, or scheduler.

Only explicit submit authorizes an exact archived ZIP. Relay state is read through
SQLite read-only; every relay queue transition remains the transport's job.
"""
from __future__ import annotations
from contextlib import contextmanager, closing
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
from uuid import uuid4
from zipfile import ZipFile

import ctp as c
from independent_guide_jobs import _members, PACKAGE_FILES, _readme

DEFAULT_RELAY = Path.home()/'Software/chatgpt-relay'
ACTIVE = {'prepared','delivering','delivered','queued','submitting','submitted','returned','importing','imported'}


def now():
    return datetime.now(timezone.utc).isoformat()


def state_dir(root):
    return root/'private/relay-coordinator'


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.'+path.name+'-'+uuid4().hex)
    try:
        with temp.open('x', encoding='utf-8') as out:
            json.dump(value,out,ensure_ascii=False,indent=2); out.write('\n')
            out.flush(); os.fsync(out.fileno())
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def locked(root):
    folder=state_dir(root); folder.mkdir(parents=True,exist_ok=True)
    with (folder/'lock').open('a') as handle:
        try:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise c.ProjectError('Another relay coordinator is running') from exc
        yield folder


def records(root):
    return [c.read_json(p) for p in sorted((state_dir(root)/'attempts').glob('*/attempt.json'))]


def load(root, attempt):
    c.ident(attempt)
    row=c.read_json(state_dir(root)/'attempts'/attempt/'attempt.json')
    c.check(row['id']==attempt,'Attempt identity mismatch')
    return row


def save(root,row):
    row['updated_at']=now()
    atomic_json(state_dir(root)/'attempts'/row['id']/'attempt.json',row)


def archive(root,row):
    return state_dir(root)/'attempts'/row['id']


def inventory(root):
    result={}
    for prefix in ('books','revisions','guide-results','translation-results'):
        folder=root/prefix
        for p in folder.rglob('*'):
            c.check(not p.is_symlink(),'Symbolic link in editorial output tree')
            if p.is_file(): result[p.relative_to(root).as_posix()]=c.digest(p.read_bytes())
    return result


def transport_rows(relay):
    db=relay/'relay.sqlite3'
    if not db.exists(): return []
    c.check(not db.is_symlink(),'Relay database is a symbolic link')
    with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as con:
        con.row_factory=sqlite3.Row
        return [dict(r) for r in con.execute('SELECT id,input_name,sha256,model,output_filename,status,chat_url,review_reason FROM jobs')]


def info(request):
    members=_members(request,PACKAGE_FILES)
    def parsed(name):
        return json.loads(members[name].decode('utf-8'),object_pairs_hook=c.pairs,parse_constant=c.invalid_constant)
    job,manifest=parsed('input/job.json'),parsed('input/manifest.json')
    c.check(c.object_hash(job)==manifest.get('job_sha256'),'Job hash mismatch')
    if job.get('task_type') in ('work_analysis','target_guide'):
        adapter='independent_guide'
        for key in ('task_type','work','target','attempt','requested_model','source_fingerprint','prompt_sha256'):
            c.check(manifest.get(key)==job.get(key),'Guide manifest differs from its pinned job')
        c.check(members['README.md'].decode('utf-8')==_readme(manifest),'Guide README changed')
        model,output=manifest['requested_model'],manifest['output_filename']
        work,target=manifest['work'],manifest['target']
    else:
        c.check(manifest.get('kind') in ('guide','translation') and type(manifest.get('issue')) is int,
                'Only accepted legacy Issue jobs and independent guides are supported')
        adapter='legacy_guide' if manifest['kind']=='guide' else 'translation'
        text=members['README.md'].decode('utf-8')
        match=re.match(r'---\nmodel: ([^\n]+)\noutput_filename: ([^\n]+)\n---\n',text)
        c.check(match is not None,'Legacy request needs explicit relay model and filename metadata')
        model,output=match.groups()
        from translation_jobs import relay_readme,GUIDE_README,TRANSLATION_README,TRANSLATION_README_V2
        body=(GUIDE_README if adapter=='legacy_guide' else
              TRANSLATION_README_V2 if job.get('request',{}).get('schema_version')==2 else
              TRANSLATION_README)
        c.check(text==relay_readme(body,request,model),'Legacy relay instructions differ from exporter')
        work,target=manifest['work'],manifest['target']
    c.ident(work)
    if target is not None:c.ident(target)
    c.check(isinstance(model,str) and model.strip() and not any(ord(ch)<32 for ch in model),'Invalid requested model')
    c.check(isinstance(output,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.zip',output),'Unsafe expected output filename')
    return {'adapter':adapter,'job_sha256':manifest['job_sha256'],'work':work,'target':target,
            'issue':manifest.get('issue'),'task_type':job.get('task_type'),
            'model_requested':model,'output_filename':output},job


def validate_current(root,row,job):
    from acquire_queue import validate_record
    wd=root/'books'/row['work']
    rights=c.read_json(wd/'rights.json')
    c.check(rights.get('work')==row['work'] and rights.get('status')=='acquired' and rights.get('eligible') is True,'Source is not admitted')
    validate_record(wd,rights['ebook_id'])
    if row['adapter']=='legacy_guide':
        from guide_requests import guide_entry,prepare_guide_issue
        expected,_=prepare_guide_issue(root,guide_entry(root,row['issue']))
    elif row['adapter']=='translation':
        from translation_jobs import request_entry,prepare_job
        expected,_=prepare_job(root,request_entry(root,row['issue']))
    else:
        from independent_guide_jobs import prepare
        expected,_=prepare(root,row['task_type'],row['work'],row['target'],
                           model=row['model_requested'],attempt=job['attempt'])
    c.check(c.object_hash(expected)==row['job_sha256'],'Job inputs became stale; prepare a deliberate new attempt')


def _adopt(root,request,relay,retry_of=None):
    metadata,job=info(request)
    validate_current(root,metadata,job)
    key=metadata['adapter']+':'+metadata['job_sha256']
    for existing in records(root):
        if existing['task_key']==key:
            if existing['state'] in ACTIVE:
                c.check(existing['model_requested']==metadata['model_requested'],'Task already prepared with a different requested model')
                return existing
            c.check(retry_of is not None,'Prior attempt needs review; explicit retry is required')
    if retry_of is not None:
        prior=load(root,retry_of)
        c.check(prior['task_key']==key and prior['state'] in {'needs_review','stale'},'Retry must identify a stopped attempt for this job')
    attempt='attempt-'+uuid4().hex
    folder=state_dir(root)/'attempts'/attempt; folder.mkdir(parents=True)
    dest=folder/request.name
    c.check(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.zip',request.name),'Unsafe input filename')
    c.check(all(x['input_name']!=request.name and x['output_filename']!=metadata['output_filename'] for x in records(root)),
            'Input or output name already used by a coordinator attempt')
    raw=request.read_bytes();dest.write_bytes(raw)
    row={'schema_version':1,'id':attempt,'task_key':key,**metadata,'input_name':request.name,
         'request_sha256':c.digest(raw),'relay':str(relay.resolve()),'state':'prepared',
         'created_at':now(),'authorization':None,'retry_of':retry_of}
    save(root,row); return row


def adopt(root,request,relay=DEFAULT_RELAY):
    root=root.resolve()
    with locked(root): return _adopt(root,request.resolve(),relay)


def prepare(root,relay=DEFAULT_RELAY,guide_issue=None,translation_issue=None,task_type=None,
            work=None,target=None,model='6 Extra High',retry_of=None):
    root=root.resolve()
    with locked(root):
        c.check(sum(x is not None for x in (guide_issue,translation_issue,task_type))==1,'Choose exactly one task')
        if task_type is None:c.check(work is None and target is None,'Issue tasks use their accepted work and target')
        filename='ctp-'+('guide-issue-'+str(guide_issue) if guide_issue is not None else
                         'translation-issue-'+str(translation_issue) if translation_issue is not None else
                         str(task_type)+'-'+str(work))+'-'+uuid4().hex[:12]+'.zip'
        with tempfile.TemporaryDirectory(dir=state_dir(root)) as temp:
            path=Path(temp)/filename
            if guide_issue is not None:
                from guide_requests import export_guide_issue
                export_guide_issue(root,guide_issue,path,model)
            elif translation_issue is not None:
                from translation_jobs import export_translation
                export_translation(root,translation_issue,path,model)
            else:
                c.check(work is not None,'Independent guide needs --work')
                from independent_guide_jobs import export
                export(root,task_type,work,target,path,model=model)
            return _adopt(root,path,relay,retry_of)


def request_path(root,row):
    path=archive(root,row)/row['input_name']
    c.check(path.is_file() and not path.is_symlink() and c.digest(path.read_bytes())==row['request_sha256'],
            'Archived request is missing or changed')
    return path


def canonical_model(value):
    return value.replace('6 Sol ','6 ',1) if isinstance(value,str) and value.startswith('6 Sol ') else value


def matching_transport(row,rows):
    matches=[r for r in rows if r['input_name']==row['input_name']]
    c.check(len(matches)<=1,'Duplicate relay input name')
    if not matches:return None
    found=matches[0]
    c.check(found['sha256']==row['request_sha256'],'Relay input hash differs')
    c.check(found['output_filename']==row['output_filename'] and
            canonical_model(found['model'])==canonical_model(row['model_requested']),
            'Relay model or result filename differs')
    return found


def _deliver(root,row):
    path=request_path(root,row);relay=Path(row['relay'])
    c.check((relay/'input').is_dir() and (relay/'output').is_dir(),'Relay input/output directories are unavailable')
    metadata,job=info(path);validate_current(root,row,job)
    final=relay/'input'/row['input_name']
    found=matching_transport(row,transport_rows(relay))
    if found is not None:
        row['state']='returned' if found['status']=='complete' else found['status'];row['relay_id']=found['id'];save(root,row);return row
    if final.exists():
        c.check(not final.is_symlink() and c.digest(final.read_bytes())==row['request_sha256'],'Existing relay input differs')
        row['state']='delivered';save(root,row);return row
    c.check(row['state']=='prepared','Uncertain earlier delivery: inspect relay before retrying')
    row['state']='delivering';save(root,row) # durable before publishing watched ZIP
    temp=relay/'input'/('.'+row['input_name']+'.'+row['id']+'.partial')
    try:
        with temp.open('xb') as out:
            out.write(path.read_bytes());out.flush();os.fsync(out.fileno())
        os.link(temp,final) # atomically publish, never overwrite
    finally:
        temp.unlink(missing_ok=True)
    row['state']='delivered';row['delivered_at']=now();save(root,row)
    return row


def submit(root,attempt,authorization):
    root=root.resolve()
    c.check(isinstance(authorization,str) and authorization.strip(),'Explicit owner authorization note is required')
    with locked(root):
        row=load(root,attempt)
        c.check(row['state'] in {'prepared','delivering','delivered','queued','submitting','submitted'},'Attempt cannot be submitted in this state')
        if row['authorization'] is None:
            row['authorization']={'note':authorization,'request_sha256':row['request_sha256'],
                                  'relay':row['relay'],'recorded_at':now()}
            save(root,row)
        return _deliver(root,row)


def _atomic_bytes(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name('.'+path.name+'-'+uuid4().hex)
    try:
        with temp.open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
        os.replace(temp,path)
    finally:temp.unlink(missing_ok=True)


def rollback(root,folder,changes):
    for name,hashes in reversed(list(changes.items())):
        path=root/name
        current=c.digest(path.read_bytes()) if path.exists() else None
        c.check(current in (hashes['before'],hashes['after']), 'Concurrent editorial edit during recovery: '+name)
        if hashes['before'] is None:path.unlink(missing_ok=True)
        else:_atomic_bytes(path,(folder/'before'/name).read_bytes())


def install(root,row,stage,before):
    after=inventory(stage)
    c.check(set(before)<=set(after),'Importer removed historical files')
    changes={name:{'before':before.get(name),'after':sha} for name,sha in after.items() if before.get(name)!=sha}
    allowed=['books/'+row['work']+'/reference/']
    if row['target'] is not None:
        allowed.extend(['books/'+row['work']+'/editions/'+row['target']+'/',
                        'revisions/'+row['work']+'/'+row['target']+'/'])
    if row['issue'] is not None:
        receipt='guide-results/' if row['adapter']=='legacy_guide' else 'translation-results/'
        allowed.append(receipt+'issue-'+str(row['issue'])+'.json')
    c.check(all(any(name.startswith(prefix) if prefix.endswith('/') else name==prefix for prefix in allowed) for name in changes),
            'Importer changed files outside its task scope')
    c.check(inventory(root)==before,'Editorial files changed while staging import')
    tx=archive(root,row)/'transaction'
    c.check(not tx.exists(),'Interrupted import transaction needs recovery')
    tx.mkdir()
    for name in changes:
        if changes[name]['before'] is not None:
            dest=tx/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dest)
    atomic_json(tx/'journal.json',changes)
    row['state']='importing';save(root,row)
    try:
        for name in changes:_atomic_bytes(root/name,(stage/name).read_bytes())
    except BaseException:
        rollback(root,tx,changes)
        row['state']='needs_review';row['reason']='Import installation failed; prior files restored';save(root,row)
        raise
    row['outputs']=changes;row['state']='imported';row['imported_at']=now();save(root,row)


def _import(root,row,response):
    before=inventory(root)
    path=request_path(root,row)
    raw=response.read_bytes()
    c.check(c.digest(raw)==row['response_sha256'],'Returned result changed')
    with tempfile.TemporaryDirectory(dir=state_dir(root)) as temp:
        stage=Path(temp)
        for name in ('books','examples','revisions','prompts','docs'):
            if (root/name).exists():shutil.copytree(root/name,stage/name)
        for name in ('project.json','queue.json','guide-requests.json','translation-requests.json','catalog.json'):
            if (root/name).exists():shutil.copy2(root/name,stage/name)
        for name in ('guide-results','translation-results'):
            if (root/name).exists():shutil.copytree(root/name,stage/name)
        retained=stage/'response.zip';retained.write_bytes(raw)
        if row['adapter']=='independent_guide':
            from independent_guide_jobs import import_result
            outcome=import_result(stage,path,retained)
        elif row['adapter']=='legacy_guide':
            from translation_jobs import import_guide
            outcome=import_guide(stage,retained)
        else:
            from translation_jobs import import_translation
            outcome=import_translation(stage,retained)
        def portable(value):
            if isinstance(value,str) and value.startswith(str(stage)+'/'):return str(root)+value[len(str(stage)):]
            if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
            if isinstance(value,list):return [portable(v) for v in value]
            return value
        row['import_result']=portable(outcome);row['git_context_at_import']=c.git_context(root)
        install(root,row,stage,before)


def reconcile(root,import_ready=False):
    root=root.resolve()
    with locked(root):
        for row in records(root):
            if row['state'] in {'prepared','imported','needs_review','stale'}:continue
            try:
                if row['state']=='importing':
                    tx=archive(root,row)/'transaction'
                    rollback(root,tx,c.read_json(tx/'journal.json'))
                    row['state']='needs_review';row['reason']='Interrupted import restored; inspect before retrying'
                    save(root,row);continue
                request_path(root,row)
                found=matching_transport(row,transport_rows(Path(row['relay'])))
                if found is None:
                    path=Path(row['relay'])/'input'/row['input_name']
                    if path.is_file():
                        c.check(not path.is_symlink() and c.digest(path.read_bytes())==row['request_sha256'],'Watched relay input differs')
                        row['state']='delivered'
                    else:
                        row['state']='needs_review';row['reason']='Delivery missing with no transport record; never resend automatically'
                else:
                    row['relay_id']=found['id'];row['chat_url']=found['chat_url']
                    row['transport_status']=found['status']
                    if found['status']=='needs_review':
                        row['state']='needs_review';row['reason']=found['review_reason']
                    elif found['status']=='complete':
                        response=Path(row['relay'])/'output'/row['output_filename']
                        c.check(response.is_file() and not response.is_symlink(),'Relay says complete but result file is missing')
                        c.check(response.stat().st_size<=32*1024*1024,'Result ZIP too large')
                        captured=archive(root,row)/'response.zip'
                        raw=response.read_bytes();sha=c.digest(raw)
                        if captured.exists():c.check(c.digest(captured.read_bytes())==sha,'Relay result changed after capture')
                        else:captured.write_bytes(raw)
                        row['response_sha256']=sha;row['state']='returned';save(root,row)
                        if import_ready:_import(root,row,captured)
                    else:row['state']=found['status']
                save(root,row)
            except (c.ProjectError,OSError,ValueError,KeyError,TypeError,sqlite3.Error) as exc:
                row['state']='needs_review';row['reason']=str(exc);save(root,row)
        return status(root)


def resume(root,attempt):
    """Explicitly retry observation/import after review, without resubmission."""
    root=root.resolve()
    with locked(root):
        row=load(root,attempt)
        c.check(row['state']=='needs_review' and row['authorization'] is not None,'Only an authorized reviewed attempt can resume')
        path=request_path(root,row);_,job=info(path);validate_current(root,row,job)
        tx=archive(root,row)/'transaction'
        if tx.exists():
            changes=c.read_json(tx/'journal.json')
            for name,hashes in changes.items():
                path=root/name;current=c.digest(path.read_bytes()) if path.exists() else None
                c.check(current==hashes['before'],'Review must restore the pre-import state before resuming')
            os.rename(tx,tx.with_name('transaction-recovered-'+uuid4().hex))
        row.setdefault('review_history',[]).append({'reason':row.pop('reason',None),'resumed_at':now()})
        row['state']='delivered';save(root,row)
        return row


def status(root):
    from guide_task_planner import discover
    try:planning=discover(root)
    except (c.ProjectError,ValueError,KeyError,TypeError,OSError) as exc:
        planning={'read_only':True,'proposed':[],'error':str(exc)}
    return {'attempts':records(root),'planning':planning,'model_invoked_directly':False,
            'scheduler_installed':False,'publication_automatic':False}


def sync_proposals(root, relay=DEFAULT_RELAY, model='6 Extra High'):
    """Prepare exact ZIPs for eligible accepted guide requests, never submit them.

    Existing attempt job hashes provide the durable, idempotent task identity.
    Stopped attempts stay stopped until an owner selects a deliberate retry.
    """
    from guide_task_planner import discover
    root=root.resolve()
    planning=discover(root)
    prepared=[]; existing=[]; held=[]
    for proposal in planning['proposed']:
        before={row['id'] for row in records(root)}
        try:
            row=prepare(root,relay,task_type=proposal['type'],work=proposal['work'],
                        target=proposal.get('target'),model=model)
        except (c.ProjectError,OSError,ValueError,KeyError,TypeError) as exc:
            held.append({'proposal':proposal,'reason':str(exc)})
            continue
        summary={'proposal':proposal,'attempt':row['id'],'state':row['state']}
        (existing if row['id'] in before else prepared).append(summary)
    return {'prepared':prepared,'existing':existing,'held':held,
            'model_called':False,'relay_submitted':False,
            'publication_automatic':False}


def publish(root,attempt,approve=False,push=False):
    """Optional exact-file Git publication with separate explicit approval."""
    root=root.resolve()
    c.check(approve,'Public Git distribution requires --approve-git-distribution')
    def git(*args):
        try:
            return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.PIPE).strip()
        except subprocess.CalledProcessError as exc:
            raise c.ProjectError('Git publication failed; inspect the branch and remote before retrying. No force push was attempted.') from exc
    with locked(root):
        row=load(root,attempt)
        c.check(row['state']=='imported','Only an imported result can be published')
        if row.get('commit'):
            c.check(not push or git('rev-parse','HEAD')==row['commit'],'HEAD moved since the approved import commit; inspect before pushing')
            if push:git('push','origin','HEAD')
            return row
        c.check(not git('diff','--cached','--name-only'),'Index has unrelated staged changes')
        expected=row['outputs']
        dirty=set(git('ls-files','--modified','--others','--exclude-standard').splitlines())
        c.check(dirty==set(expected),'Worktree has other changes or imported outputs changed')
        for name,hashes in expected.items():c.check(c.digest((root/name).read_bytes())==hashes['after'],'Imported output changed: '+name)
        c.validate_project(root)
        git('add','--',*expected)
        git('commit','-m','Import draft relay '+row['adapter']+' '+row['work'])
        row['commit']=git('rev-parse','HEAD');row['git_distribution_approved_at']=now();save(root,row)
        if push:git('push','origin','HEAD')
        return row
