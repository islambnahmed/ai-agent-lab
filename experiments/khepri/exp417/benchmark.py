"""Reproducible synthetic comparison of three authorization boundaries."""
import json
import random
from approval_receipts import (BRANCH, PREFIX, REPO, Plan, new_runtime,
                               scope_only, path_only_approval)

BASE = Plan('write', REPO, BRANCH, PREFIX + 'approved.txt')

def run(n=10000, seed=417):
    rng = random.Random(seed)
    totals = {'cases':0,'scope_only_false_accepts':0,
              'path_only_false_accepts':0,'receipt_false_accepts':0,
              'receipt_legitimate_accepts':0,'receipt_replays_accepted':0,
              'scope_only_outside_denied':0,'receipt_outside_denied':0}
    domain_counts = {}
    for i in range(n):
        domain = 'github_issue' if i % 2 == 0 else 'seo_html'
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        # An attacker supplies an in-scope action or a changed body. This
        # models a planner contaminated by untrusted observations, not an LLM.
        mode = i % 4
        original = ('issue:' if domain == 'github_issue' else '<title>') + str(i)
        approved_payload = original.encode('utf8')
        if mode == 0:
            requested = Plan('write', REPO, BRANCH, PREFIX + 'attacker.txt')
            submitted = approved_payload
        elif mode == 1:
            requested = BASE
            submitted = approved_payload + b'\nOVERRIDE'
        elif mode == 2:
            requested = Plan('write', REPO, BRANCH, PREFIX + 'other_' + str(i) + '.txt')
            submitted = approved_payload + b'!'
        else:
            requested = BASE
            submitted = rng.randbytes(rng.randrange(1,30)) + b'!'
            if submitted == approved_payload:
                submitted += b'!'
        issuer, executor = new_runtime()
        receipt = issuer.issue(BASE, approved_payload)
        totals['cases'] += 1
        totals['scope_only_false_accepts'] += int(scope_only(requested, submitted))
        totals['path_only_false_accepts'] += int(path_only_approval(BASE, requested, submitted))
        totals['receipt_false_accepts'] += int(executor.simulate(receipt, requested, submitted).accepted)
        # Separate valid approval, plus replay attempt.
        valid_receipt = issuer.issue(BASE, approved_payload)
        totals['receipt_legitimate_accepts'] += int(executor.simulate(valid_receipt, BASE, approved_payload).accepted)
        totals['receipt_replays_accepted'] += int(executor.simulate(valid_receipt, BASE, approved_payload).accepted)
        # Out-of-scope control.
        if i < 100:
            outside = Plan('write', REPO, 'main', PREFIX+'bad.txt')
            totals['scope_only_outside_denied'] += int(not scope_only(outside, b'bad'))
            r2 = issuer.issue(BASE, approved_payload)
            totals['receipt_outside_denied'] += int(not executor.simulate(r2, outside, b'bad').accepted)
    return {'seed':seed, 'domains':domain_counts, 'results':totals,
            'notes': 'All 10,000 attacks deliberately differ from approved plan and/or payload. No real API writes.'}

if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))
