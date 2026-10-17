"""Mechanical queue acquisition; source bytes stay out of public Git pending checks."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from legacy_v1 import check, read_json, write_json, ProjectError
from intake import validate_queue
from source_import import fetch_gutenberg, validate_blocks


def acquire_queued(root: Path, output: Path) -> dict:
    config = read_json(root/'project.json')
    queue = read_json(root/'queue.json')
    validate_queue(queue, config)
    check(not output.exists(), 'Use a fresh acquisition output directory')
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'acquired': [], 'skipped': [], 'failed': []}
    for work in queue['works']:
        wid = work['id']
        local = root/'books'/wid/'acquisition'
        receipt = root/'books'/wid/'acquisition-receipt.json'
        try:
            if local.exists():
                validate_blocks(local)
                report['skipped'].append(wid)
                continue
            if receipt.exists():
                saved = read_json(receipt)
                validate_receipt(saved, wid, config['repository'])
                # Leave ten days to retrieve the artifact before its retention ends.
                if datetime.fromisoformat(saved['retained_until']) > datetime.now(timezone.utc) + timedelta(days=10):
                    report['skipped'].append(wid)
                    continue
            fetch_gutenberg(output, work['source']['id'])
            report['acquired'].append(wid)
        except (ProjectError, OSError, ValueError, URLError) as exc:
            report['failed'].append({'work': wid, 'error': str(exc)})
    write_json(output/'report.json', report)
    return report


def validate_receipt(receipt: dict, wid: str, repository: str) -> None:
    import re
    check(receipt.get('schema_version') == 1 and receipt.get('work') == wid, 'Invalid acquisition receipt')
    check(receipt.get('status') == 'awaiting verification', 'Invalid acquisition status')
    check(receipt.get('source_edition_verified') is False and receipt.get('rights_checked') is False,
          'An acquisition receipt cannot approve edition or rights')
    check(bool(re.fullmatch(r'[0-9a-f]{64}', receipt.get('raw_sha256', ''))), 'Invalid source hash')
    for key in ('run_id', 'artifact_id'):
        check(type(receipt.get(key)) is int and receipt[key] > 0, 'Invalid Actions identifier')
    check(receipt['artifact_url'] == f"https://github.com/{repository}/actions/runs/{receipt['run_id']}/artifacts/{receipt['artifact_id']}", 'Invalid artifact URL')
    check(datetime.fromisoformat(receipt['retained_until']).tzinfo is not None, 'Retention timestamp needs a timezone')


def register_acquisitions(root: Path, output: Path, run_id: int, artifact_id: int) -> dict:
    config = read_json(root/'project.json')
    queue = read_json(root/'queue.json')
    validate_queue(queue, config)
    allowed = {w['id']: w for w in queue['works']}
    report = read_json(output/'report.json')
    pending = []
    for wid in report['acquired']:
        check(wid in allowed, 'Acquisition is not in the authorized queue')
        base = output/'books'/wid/'acquisition'
        blocks = validate_blocks(base)
        provenance = read_json(base/'provenance.json')
        check(provenance['ebook_id'] == allowed[wid]['source']['id'] and provenance['raw_sha256'] == blocks['raw_sha256'], 'Acquisition identity/hash mismatch')
        receipt = dict(provenance, work=wid, status='awaiting verification', run_id=run_id, artifact_id=artifact_id,
                       artifact_url=f'https://github.com/{config["repository"]}/actions/runs/{run_id}/artifacts/{artifact_id}',
                       retained_until=(datetime.now(timezone.utc) + timedelta(days=90)).isoformat())
        validate_receipt(receipt, wid, config['repository'])
        pending.append((root/'books'/wid/'acquisition-receipt.json', receipt))
    for path, receipt in pending:
        write_json(path, receipt)
    return {'registered': len(pending), 'failed': report['failed']}
