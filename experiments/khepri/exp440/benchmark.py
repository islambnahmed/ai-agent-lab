"""Deterministic fault matrix: two different synthetic task families."""
import os
import tempfile
from durable_delivery import (connect, enqueue, deliver_once, effect_count,
                              pending_count, purge_receipts)


def run(n=200):
    results = {}
    for family in ('seo', 'gold'):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, 'bench.sqlite')
            db = connect(path)
            try:
                for i in range(n):
                    enqueue(db, f'{family}:{i:04d}', f'{family}:payload:{i}'.encode())
                # Crash all attempts after sink effect. Acknowledge only on retry.
                for i in range(n):
                    outcome = deliver_once(db, 'w1', 0, 'after_effect')
                    assert outcome == 'crashed_after_effect'
                db.close()
                db = connect(path)
                for i in range(n):
                    outcome = deliver_once(db, 'w2', 10)
                    assert outcome == 'duplicate'
                assert effect_count(db) == n and pending_count(db) == 0
                results[family] = {'operations': n, 'injected_crashes': n,
                                   'replayed_receipts': n, 'effects': effect_count(db),
                                   'duplicate_effects': effect_count(db) - n}
                # Separate, intentionally unsafe receipt-retention experiment.
                # Each new operation has its own stable id and payload.
                for i in range(n):
                    enqueue(db, f'{family}:ttl:{i:04d}', f'{family}:ttl:{i}'.encode())
                for i in range(n):
                    assert deliver_once(db, 'w3', 20, 'after_effect') == 'crashed_after_effect'
                removed = purge_receipts(db, 21)  # purge old receipts incl. first run
                assert removed == 2*n
                for i in range(n):
                    assert deliver_once(db, 'w4', 30) == 'applied'
                results[family]['ttl_receipts_purged'] = removed
                results[family]['ttl_duplicate_effects'] = effect_count(db) - 2*n
                assert results[family]['ttl_duplicate_effects'] == n
            finally:
                db.close()
    return results


if __name__ == '__main__':
    print(run())
