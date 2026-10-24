"""Deterministic synthetic benchmark for the receipt equality-spoofing counterexample."""
import json
import random
import time
from identity_receipts import new_runtime, new_strict_runtime
from approval_receipts import Plan, REPO, BRANCH, PREFIX
from test_identity_receipts import EqualImpostor

PLAN = Plan('write', REPO, BRANCH, PREFIX+'approved.txt')


def trial(factory, n=5000):
    rng = random.Random(418)
    accepted_forgery = accepted_legitimate = 0
    started = time.perf_counter()
    for i in range(n):
        issuer, executor = factory()
        payload = (b'github-issue:' if i % 2 == 0 else b'seo-html:') + rng.randbytes(rng.randrange(0, 60))
        receipt = issuer.issue(PLAN, payload)
        # Threat model: attacker learns only hash(receipt), not receipt object.
        fake = EqualImpostor(hash(receipt))
        accepted_forgery += executor.simulate(fake, PLAN, payload).accepted
        accepted_legitimate += executor.simulate(receipt, PLAN, payload).accepted
    return {'n': n, 'forged_accepted': accepted_forgery,
            'legitimate_accepted_after_forgery': accepted_legitimate,
            'elapsed_seconds_observed': round(time.perf_counter()-started, 5)}


if __name__ == '__main__':
    print(json.dumps({'original': trial(new_runtime),
                      'strict': trial(new_strict_runtime)}, indent=2))
