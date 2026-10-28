"""Prepare accepted relay tasks; submit only under a committed owner policy."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
from pathlib import Path
import re
import subprocess

import ctp as c
import relay_coordinator as coordinator

POLICY = 'model-submission-policy.json'
TASK_TYPES = {'work_analysis', 'target_guide', 'translation', 'legacy_combined_guide'}
IN_FLIGHT = {'prepared', 'delivering', 'delivered', 'queued', 'submitting',
             'submitted', 'returned', 'importing'}


@contextmanager
def dispatch_lock(root: Path):
    folder = root/'private/relay-coordinator'
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'dispatch.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        yield


def policy(root: Path) -> dict:
    data = c.read_json(root/POLICY)
    c.check(isinstance(data,dict) and set(data)=={
        'schema_version','enabled','policy_id','authorized_by','authorization_note',
        'works','targets','task_types','model','max_submissions_total',
        'max_submissions_per_run','max_in_flight'} and
        data['schema_version']==1 and type(data['enabled']) is bool and
        isinstance(data['policy_id'],str) and
        re.fullmatch(r'[a-z0-9][a-z0-9-]{2,79}',data['policy_id']) and
        isinstance(data['model'],str) and 0<len(data['model'].strip())<=160 and
        not any(ord(ch)<32 for ch in data['model']) and
        all(type(data[key]) is int and data[key]>=0 for key in
            ('max_submissions_total','max_submissions_per_run','max_in_flight')) and
        all(isinstance(data[key],list) and len(data[key])==len(set(data[key]))
            for key in ('works','targets','task_types')) and
        all(isinstance(x,str) and re.fullmatch(r'gutenberg-[0-9]{1,7}',x)
            for x in data['works']) and
        all(isinstance(x,str) and x in {r['id'] for r in c.read_json(root/'project.json')['targets']}
            for x in data['targets']) and
        all(x in TASK_TYPES for x in data['task_types']),
        'Invalid model-submission policy')
    if data['enabled']:
        maintainers=c.read_json(root/'project.json')['maintainers']
        c.check(data['authorized_by'] in maintainers and
                isinstance(data['authorization_note'],str) and
                bool(data['authorization_note'].strip()) and
                data['works'] and data['task_types'] and
                data['max_submissions_total']>0 and
                data['max_submissions_per_run']>0 and
                data['max_in_flight']>0,
                'Enabled model-submission policy needs bounded owner authorization')
        def git(*args):
            return subprocess.run(['git','-C',str(root),*args],
                                  capture_output=True,check=False,text=True)
        fetched=git('fetch','--quiet','origin','main')
        head=git('rev-parse','HEAD');remote=git('rev-parse','origin/main')
        branch=git('branch','--show-current');saved=git('show','HEAD:'+POLICY)
        dirty=git('status','--porcelain','--untracked-files=normal')
        c.check(all(r.returncode==0 for r in (fetched,head,remote,branch,saved,dirty)) and
                head.stdout.strip()==remote.stdout.strip() and
                branch.stdout.strip()=='main' and
                saved.stdout==(root/POLICY).read_text(encoding='utf-8') and
                not dirty.stdout.strip(),
                'Enabled model-submission policy requires a clean, current origin/main')
    return data


def _task_type(row: dict) -> str:
    return (row['task_type'] if row['adapter']=='independent_guide' else
            'translation' if row['adapter']=='translation' else
            'legacy_combined_guide')


def _allowed(row: dict, data: dict) -> bool:
    return (row['work'] in data['works'] and
            (row['target'] is None or row['target'] in data['targets']) and
            _task_type(row) in data['task_types'] and
            row['model_requested']==data['model'])


def _prepare_issue_requests(root: Path, relay: Path, model: str) -> tuple[list, list, list]:
    from translation_jobs import validate_queue as translations
    from guide_requests import validate_guide_queue as guides
    prepared=[];existing=[];held=[]
    specs=[('translation',entry['issue']) for entry in translations(root)['requests']]
    specs += [('legacy_guide',entry['issue']) for entry in guides(root)['requests']]
    for adapter,issue in sorted(specs,key=lambda pair:(pair[1],pair[0])):
        result=root/('translation-results' if adapter=='translation' else 'guide-results')/('issue-'+str(issue)+'.json')
        if result.exists():continue
        rows=[row for row in coordinator.records(root)
              if row['adapter']==adapter and row['issue']==issue]
        if rows:
            (existing if all(row['state'] in coordinator.ACTIVE for row in rows) else held).append(
                {'adapter':adapter,'issue':issue,'attempts':[row['id'] for row in rows]})
            continue
        try:
            row=coordinator.prepare(root,relay,
                translation_issue=issue if adapter=='translation' else None,
                guide_issue=issue if adapter=='legacy_guide' else None,model=model)
            prepared.append({'adapter':adapter,'issue':issue,'attempt':row['id']})
        except (c.ProjectError,OSError,ValueError,KeyError,TypeError) as exc:
            held.append({'adapter':adapter,'issue':issue,'reason':str(exc)})
    return prepared,existing,held


def dispatch(root: Path, relay: Path = coordinator.DEFAULT_RELAY) -> dict:
    """No model calls; delivery to watched relay input requires active policy."""
    root=root.resolve();relay=relay.resolve()
    with dispatch_lock(root):
        data=policy(root)
        guides=coordinator.sync_proposals(root,relay,model=data['model'])
        prepared,existing,held=_prepare_issue_requests(root,relay,data['model'])
        submitted=[];skipped=[]
        if data['enabled']:
            rows=coordinator.records(root)
            authorized=[row for row in rows if isinstance(row.get('authorization'),dict)
                        and row['authorization'].get('policy_id')==data['policy_id']]
            in_flight=sum(row['state'] in IN_FLIGHT and
                          isinstance(row.get('authorization'),dict) for row in rows)
            remaining=min(data['max_submissions_total']-len(authorized),
                          data['max_submissions_per_run'],
                          data['max_in_flight']-in_flight)
            for row in rows:
                if remaining<=0:break
                if row['state']!='prepared' or row['authorization'] is not None:continue
                if not _allowed(row,data):continue
                try:
                    note=('Standing policy '+data['policy_id']+' authorized by '+
                          data['authorized_by']+': '+data['authorization_note'])
                    outcome=coordinator.submit(root,row['id'],note,
                                               policy_id=data['policy_id'])
                    submitted.append({'attempt':row['id'],'state':outcome['state']})
                    remaining-=1
                except (c.ProjectError,OSError,ValueError,KeyError,TypeError) as exc:
                    skipped.append({'attempt':row['id'],'reason':str(exc)})
                    break
        return {'guide_preparation':guides,'issue_prepared':prepared,
                'issue_existing':existing,'held':held,'submitted':submitted,
                'submission_blocked':skipped,'policy_enabled':data['enabled'],
                'model_called_directly':False,
                'relay_submitted':bool(submitted)}
