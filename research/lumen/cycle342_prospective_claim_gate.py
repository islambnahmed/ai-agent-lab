"""Fail-closed screening of externally supplied Gold Lab prospective evidence.

This is NOT a provider downloader, GitHub anchor verifier, or settlement engine.
An eligible result means supplied fields are internally consistent, not independently
authenticated. Source proof must be independently checked before reporting skill.
"""
from __future__ import annotations
import datetime as dt
import math
from typing import Any

def instant(s: str) -> dt.datetime:
    if not isinstance(s,str) or not s.endswith('Z'):
        raise ValueError('UTC Z timestamp required')
    try: t=dt.datetime.fromisoformat(s[:-1]+'+00:00')
    except (TypeError,ValueError) as e: raise ValueError('invalid UTC timestamp') from e
    if t.utcoffset()!=dt.timedelta(0): raise ValueError('UTC required')
    return t

def date(s: str) -> dt.date:
    if not isinstance(s,str) or len(s)!=10: raise ValueError('YYYY-MM-DD required')
    try: d=dt.date.fromisoformat(s)
    except ValueError as e: raise ValueError('invalid date') from e
    if d.isoformat()!=s: raise ValueError('YYYY-MM-DD required')
    return d

def finite_positive(x: Any) -> bool:
    # JSON permits arbitrary-size integers; math.isfinite(10**400) raises
    # OverflowError. Untrusted evidence must fail closed, never crash screening.
    if type(x) not in (int, float) or x <= 0:
        return False
    try:
        return math.isfinite(x)
    except OverflowError:
        return False

def screen(receipt: dict, evidence: dict) -> dict:
    """Screen supplied evidence without network access; fail closed on missing proof."""
    failures=[]
    as_of=dt.datetime.now(dt.timezone.utc)
    if not isinstance(receipt,dict) or not isinstance(evidence,dict):
        return {'status':'insufficient_evidence','reasons':['receipt/evidence objects required']}
    try:
        issued=instant(receipt['issuedAt'])
        if issued>as_of: raise ValueError('receipt issue timestamp is in the future')
        origin=date(receipt['originDate'])
        if issued.date() <= origin:
            failures.append('receipt issued before completed origin UTC day')
        horizon=receipt['horizon']
        if type(horizon) is not int or horizon not in (1,7,30): raise ValueError('invalid horizon')
        if not all(finite_positive(receipt[k]) for k in ('point','baseline','originClose')):raise ValueError('invalid receipt prices')
        if receipt['baseline']!=receipt['originClose']: failures.append('baseline not equal to originClose')
        if receipt.get('targetDate') is not None: failures.append('requires observed-cadence targetDate=null in this audit')
        if receipt.get('calendar')!='observations': failures.append('this audit only covers observations cadence')
        if not isinstance(receipt.get('source'), str) or not receipt['source'].strip():
            raise ValueError('nonempty source provider required')
    except (KeyError,TypeError,ValueError) as e:
        return {'status':'invalid_receipt','reasons':[str(e)]}
    if evidence.get('receipt_in_anchored_commit_verified') is not True:
        failures.append('no independently verified anchored receipt bytes')
    try:
        anchor=instant(evidence['anchorObservedAt'])
        if anchor>as_of: failures.append('external anchor timestamp is in the future')
        if anchor<=issued: failures.append('anchor not after receipt issue timestamp')
    except (KeyError,ValueError):
        anchor=None;failures.append('missing verified external anchor timestamp')
    if evidence.get('provider')!=receipt.get('source'):
        failures.append('outcome provider does not match receipt provider')
    if evidence.get('unit')!='USD per troy ounce' or evidence.get('grain')!='daily':
        failures.append('outcome unit/grain contract unverified')
    if evidence.get('original_vintage_verified') is not True:
        failures.append('original source vintage/prefix not independently verified')
    if evidence.get('complete_provider_sequence_independently_verified') is not True:
        failures.append('future observed-close sequence completeness not independently verified')
    sequence=evidence.get('futureObservedCloses')
    if not isinstance(sequence,list) or len(sequence)!=horizon:
        failures.append('exact future provider observation sequence unavailable')
        target=None
    else:
        try:
            days=[date(r['date']) for r in sequence]
            if days[0]<=origin or any(a>=b for a,b in zip(days,days[1:])):
                failures.append('future provider observation dates invalid or unordered')
            if any(not finite_positive(r['price']) for r in sequence):
                failures.append('invalid future provider price')
            target=sequence[-1]
        except (KeyError,TypeError,ValueError):
            target=None;failures.append('invalid provider observation sequence')
    if target is not None:
        try:
            published=instant(evidence['targetFirstAvailableAt'])
            if published>as_of: failures.append('target first availability timestamp is in the future')
            if anchor is None or published<=anchor:
                failures.append('target first availability not proven after external receipt anchor')
            if published.date() <= date(target['date']):
                failures.append('claimed completed UTC-day close was available before UTC day ended')
        except (KeyError,ValueError):
            failures.append('no independently verified target first-availability timestamp')
    else:
        failures.append('target publication chronology cannot be checked')
    if evidence.get('provider_timestamp_independently_verified') is not True:
        failures.append('target first-availability provenance not independently verified')
    if failures:
        return {'status':'insufficient_evidence','reasons':failures,
                'structural_model_equals_baseline':receipt['point']==receipt['baseline']}
    actual=target['price']
    model_abs_error=abs(receipt['point']-actual)
    baseline_abs_error=abs(receipt['baseline']-actual)
    return {'status':'eligible_for_scoring','targetDate':target['date'],
            'actual':actual,'modelAbsError':model_abs_error,'baselineAbsError':baseline_abs_error,
            'improvementVsPersistence':baseline_abs_error-model_abs_error,
            'structural_model_equals_baseline':receipt['point']==receipt['baseline'],
            'caution':'Screened supplied evidence only; not independent source authentication or trading edge.'}

def main():
    """CLI screens user-supplied JSON; it does not fetch or authenticate evidence."""
    import argparse, json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',required=True,help='Committed receipt JSON')
    parser.add_argument('--evidence',required=True,help='Independently audited evidence JSON')
    args=parser.parse_args()
    try:
        with open(args.receipt,encoding='utf-8') as f: receipt=json.load(f)
        with open(args.evidence,encoding='utf-8') as f: evidence=json.load(f)
        result=screen(receipt,evidence)
    except (OSError,ValueError) as e:
        result={'status':'invalid_input','reasons':[str(e)]}
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='eligible_for_scoring' else 2

if __name__=='__main__':
    raise SystemExit(main())
