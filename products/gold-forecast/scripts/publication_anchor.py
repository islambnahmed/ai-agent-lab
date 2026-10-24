"""Conservative GitHub-server publication audit for Gold Lab receipts.

A GitHub Actions *push* run created_at provides a server-side upper bound on
when a matching receipt existed in a specific immutable Git commit. It does
NOT prove provider close times, price authenticity, or forecast skill.

Usage: python publication_anchor.py <local-receipt.json>
Only public islambnahmed/ai-agent-lab URLs are accessed; no credentials.
"""
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

REPO = 'islambnahmed/ai-agent-lab'
API = f'https://api.github.com/repos/{REPO}'
RECEIPT = re.compile(r'^\d{4}-\d{2}-\d{2}-h(?:1|7|30)\.json$')
ROOT = 'products/gold-forecast/reports/prospective/'


def api_json(path):
    if not path.startswith('/') or '://' in path or '..' in path:
        raise ValueError('Unapproved API path')
    req = urllib.request.Request(API + path, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'GoldLab-Publication-Audit/1.0'})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def parse_utc(s):
    if not isinstance(s, str) or not s.endswith('Z'):
        raise ValueError('UTC Z timestamp required')
    result = dt.datetime.fromisoformat(s[:-1] + '+00:00')
    if result.tzinfo is None:
        raise ValueError('Timestamp must be timezone-aware')
    return result


def assess(receipt, anchor_time):
    """Return strict eligibility, never an inferred close-time guarantee."""
    issued = parse_utc(receipt['issuedAt'])
    observed = parse_utc(anchor_time)
    if issued > observed:
        return 'invalid_issued_after_server_anchor'
    target = receipt.get('targetDate')
    if target is None:
        return 'anchored_target_date_unknown'
    if not isinstance(target, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', target):
        return 'invalid_target_date'
    try:
        date = dt.date.fromisoformat(target)
    except ValueError:
        return 'invalid_target_date'
    if date <= observed.date():
        return 'not_proven_before_target_day'
    return 'anchored_before_target_day_only'


def audit(local_path, get=api_json):
    local_path = Path(local_path)
    if not RECEIPT.fullmatch(local_path.name):
        raise ValueError('Only named Gold Lab prospective receipts are allowed')
    raw = local_path.read_bytes()
    receipt = json.loads(raw)
    if not isinstance(receipt, dict) or not isinstance(receipt.get('id'), str):
        raise ValueError('Invalid receipt structure')
    repo_path = ROOT + local_path.name
    path_arg = urllib.parse.quote(repo_path, safe='/')
    matches = []
    # Bound API use. If history is truncated, fail closed rather than claim first.
    for page in range(1, 11):
        commits = get(f'/commits?path={urllib.parse.quote(repo_path)}&per_page=100&page={page}')
        if not isinstance(commits, list):
            raise ValueError('Invalid commit API response')
        matches.extend(commits)
        if len(commits) < 100:
            break
    else:
        raise ValueError('Commit history too long to establish earliest anchor')
    candidates = []
    for item in matches:
        sha = item.get('sha', '')
        if not re.fullmatch(r'[0-9a-f]{40}', sha):
            continue
        obj = get(f'/contents/{path_arg}?ref={sha}')
        if obj.get('encoding') != 'base64':
            continue
        published = base64.b64decode(obj.get('content', ''), validate=False)
        if published != raw:
            continue
        runs = get(f'/actions/runs?head_sha={sha}&per_page=100')
        if not isinstance(runs, dict) or runs.get('total_count', 0) > 100:
            raise ValueError('Workflow run evidence is incomplete')
        for run in runs.get('workflow_runs', []):
            if run.get('head_sha') == sha and run.get('event') == 'push':
                created = run.get('created_at')
                parse_utc(created)
                candidates.append({'observedAt': created, 'commit': sha,
                                   'runId': run.get('id')})
    if not candidates:
        return {'receiptId': receipt['id'], 'status': 'unanchored',
                'reason': 'No matching receipt bytes in a commit with a GitHub push run'}
    first = min(candidates, key=lambda x: parse_utc(x['observedAt']))
    return {'receiptId': receipt['id'], 'localSha256': hashlib.sha256(raw).hexdigest(),
            'status': assess(receipt, first['observedAt']), **first,
            'limitation': 'GitHub Actions creation is server-side evidence of commit existence; '
                          'not a verified market close timestamp or a proof of predictive skill'}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python publication_anchor.py <receipt.json>')
    try:
        print(json.dumps(audit(sys.argv[1]), indent=2))
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({'status': 'unverified', 'error': str(error)}))
        raise SystemExit(1)
