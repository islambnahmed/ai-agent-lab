"""Deterministic paired SQLite experiments; synthetic cases, not attack prevalence."""
import json
import tempfile
from collections import Counter
from pathlib import Path
from approval_sqlite import ApprovalDB

CASES=('clean','peer_write','aba','delete_recreate','unrelated','absent_create')


def run(repeats=40):
    totals=Counter()
    by_domain={}
    with tempfile.TemporaryDirectory() as tmp:
        baseline=ApprovalDB(Path(tmp)/'naive.sqlite')
        guarded=ApprovalDB(Path(tmp)/'guarded.sqlite')
        for domain in ('seo','gold'):
            counts=Counter()
            for case in CASES:
                for i in range(repeats):
                    path=f'{domain}/{case}/{i}'
                    peer=f'{domain}/unrelated/{case}/{i}'
                    approval_id=f'{domain}-{case}-{i}'
                    if case!='absent_create':
                        baseline.external_write(path,b'original')
                        guarded.external_write(path,b'original')
                    guarded.issue(approval_id,path,b'approved')
                    touched=False
                    for db in (baseline,guarded):
                        if case=='peer_write':
                            db.external_write(path,b'peer'); touched=True
                        elif case=='aba':
                            db.external_write(path,b'peer')
                            db.external_write(path,b'original'); touched=True
                        elif case=='delete_recreate':
                            db.external_delete(path)
                            db.external_write(path,b'peer'); touched=True
                        elif case=='unrelated':
                            db.external_write(peer,b'peer')
                        elif case=='absent_create':
                            db.external_write(path,b'peer'); touched=True
                    # Naive plan+payload approval: always overwrites, no state condition.
                    baseline.external_write(path,b'approved')
                    result=guarded.redeem(approval_id,path,b'approved')
                    counts[f'{case}_{result}']+=1
                    if touched:
                        counts['baseline_stale_overwrites']+=1
                        if result=='ok': counts['guarded_stale_overwrites']+=1
                    else:
                        if result!='ok': raise AssertionError((case,result))
                    if touched and result!='stale': raise AssertionError((case,result))
                    if touched and guarded.snapshot(path)[2]==b'approved':
                        raise AssertionError('guarded overwrote peer state')
            by_domain[domain]=dict(sorted(counts.items()))
            totals.update(counts)
    return {'model':'SQLite local paired deterministic scenarios', 'cases_per_domain':repeats*len(CASES),
            'scenarios':list(CASES), 'by_domain':by_domain, 'totals':dict(sorted(totals.items())),
            'caveat':'All events deliberately constructed. Not real-world frequency, throughput or security guarantee.'}

if __name__=='__main__':
    results=run()
    Path(__file__).with_name('results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results['totals'],indent=2))
