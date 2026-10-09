"""Fail-closed settlement calendar guard for Worker A's 2026-10-09 forecast.

The frozen forecast report specified SEVEN WEEKDAYS. StatMuse publishes
weekend XAU/USD rows, so seven provider rows is a different horizon.
This verifies local hashes and dates, NOT publisher price vintages.
"""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def parse_utc(s):
    t=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.tzinfo is None or t.utcoffset()!=dt.timedelta(0):
        raise ValueError('Explicit UTC timestamp required')
    return t.astimezone(dt.timezone.utc)

def expected_weekdays(last_date,horizon):
    if type(horizon) is not int or not 1<=horizon<=60:
        raise ValueError('Invalid horizon')
    day=dt.date.fromisoformat(last_date)
    result=[]
    while len(result)<horizon:
        day+=dt.timedelta(days=1)
        if day.weekday()<5:
            result.append(day.isoformat())
    return result

def audit_issue(ledger_bytes,manifest_bytes):
    if not ledger_bytes.endswith(b'\n'):
        raise ValueError('Unterminated ledger')
    events=[json.loads(s) for s in ledger_bytes.splitlines() if s]
    if len(events)!=1 or events[0].get('type')!='issue':
        raise ValueError('Expected one pending issue')
    ev=events[0]
    if ev.get('prev_hash')!='0'*64:
        raise ValueError('Invalid genesis link')
    if ev.get('event_hash')!=digest(canonical({k:v for k,v in ev.items() if k!='event_hash'})):
        raise ValueError('Ledger event hash mismatch')
    payload={k:v for k,v in ev.items() if k not in ('id','prev_hash','event_hash')}
    if ev.get('id')!=digest(canonical(payload)):
        raise ValueError('Issue ID mismatch')
    if ev.get('source_snapshot_sha256')!=digest(manifest_bytes):
        raise ValueError('Source manifest hash mismatch')
    manifest=json.loads(manifest_bytes)
    if manifest.get('type')!='manual_transcription_manifest_not_raw_source_snapshot':
        raise ValueError('Unexpected manifest type')
    if manifest.get('instrument')!='XAU/USD indicative daily closing price USD per troy ounce':
        raise ValueError('Unexpected instrument')
    if manifest.get('source')!='StatMuse Money':
        raise ValueError('Unexpected source')
    if ev.get('horizon_sessions')!=7 or ev.get('last_date')!='2026-10-08':
        raise ValueError('Not the preregistered forecast')
    issued=parse_utc(ev['issued_at'])
    captured=parse_utc(manifest['captured_at_utc'])
    if captured>issued or issued.date()<=dt.date.fromisoformat(ev['last_date']):
        raise ValueError('Invalid issuance chronology')
    obs=manifest['observations']
    if len(obs)!=2 or obs[-1]['date']!=ev['last_date'] or obs[-1]['close']!=ev['last_price']:
        raise ValueError('Anchor mismatch')
    if ev['predictions']['naive']!=ev['last_price']:
        raise ValueError('Baseline mismatch')
    first=dt.date.fromisoformat(obs[0]['date'])
    last=dt.date.fromisoformat(obs[-1]['date'])
    if first>=last or first.weekday()>=5 or last.weekday()>=5:
        raise ValueError('Invalid anchor dates')
    steps=sum((first+dt.timedelta(days=i)).weekday()<5 for i in range((last-first).days+1))-1
    candidate=round(obs[-1]['close']*math.exp(7/steps*math.log(obs[-1]['close']/obs[0]['close'])),2)
    if ev['predictions']['candidate']!=candidate:
        raise ValueError('Candidate mismatch')
    dates=expected_weekdays(ev['last_date'],7)
    return {'issue_id':ev['id'],'issued_at':ev['issued_at'],
            'expected_dates':dates,'target_date':dates[-1],
            'predictions':ev['predictions'],
            'provenance':'manual transcription; not independently authenticated'}

def validate_future(audit,rows,settled_at):
    if not isinstance(rows,list) or len(rows)!=7:
        raise ValueError('Require seven future weekday observations')
    if [r.get('date') for r in rows]!=audit['expected_dates']:
        raise ValueError('Nonconsecutive or cherry-picked settlement dates')
    settled=parse_utc(settled_at)
    issued=parse_utc(audit['issued_at'])
    for row in rows:
        price=row.get('price')
        if type(price) not in (int,float) or not math.isfinite(price) or price<=0:
            raise ValueError('Invalid price')
        seen=parse_utc(row['first_seen_at'])
        day=dt.date.fromisoformat(row['date'])
        earliest=dt.datetime.combine(day+dt.timedelta(days=1),dt.time(),tzinfo=dt.timezone.utc)
        if seen<earliest:
            raise ValueError('Daily close attested before next UTC day')
        if seen<issued or seen>settled:
            raise ValueError('Impossible observation chronology')
    actual=rows[-1]['price']
    return {'calendar_valid':True,'target_date':audit['target_date'],
            'absolute_errors':{k:round(abs(v-actual),2) for k,v in audit['predictions'].items()},
            'caveat':'Calendar and hashes only; price vintage and first_seen_at are not authenticated.'}

if __name__=='__main__':
    if len(sys.argv) not in (3,4):
        raise SystemExit('Usage: guard.py LEDGER.jsonl MANIFEST.json [FUTURE.json]')
    result=audit_issue(Path(sys.argv[1]).read_bytes(),Path(sys.argv[2]).read_bytes())
    if len(sys.argv)==4:
        result['provisional_scoring']=validate_future(result,json.loads(Path(sys.argv[3]).read_text()),dt.datetime.now(dt.timezone.utc).isoformat())
    print(json.dumps(result,indent=2))
