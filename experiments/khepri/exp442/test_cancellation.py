import os
import random
import tempfile
import unittest
from cancellation import (connect, apply_guarded, cancel_guarded, effect_count,
                          check_schedules, enumerate_interleavings, evaluate)

class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'sink.sqlite')
        self.db = connect(self.path)
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_baseline_counterexample(self):
        result = check_schedules(False)
        self.assertGreater(result['violations'], 0)
        self.assertIn(['verify','cancel','effect'], result['counterexamples'])

    def test_all_guarded_schedules_safe(self):
        result = check_schedules(True)
        self.assertEqual(result['schedules'], 6)
        self.assertEqual(result['violations'], 0)

    def test_cancel_before_apply(self):
        self.assertEqual(cancel_guarded(self.db, 'seo:1'), 'cancelled')
        self.assertEqual(apply_guarded(self.db, 'seo:1', b'payload'), 'fenced')
        self.assertEqual(effect_count(self.db, 'seo:1'), 0)

    def test_apply_before_cancel(self):
        self.assertEqual(apply_guarded(self.db, 'gold:1', b'payload'), 'applied')
        self.assertEqual(cancel_guarded(self.db, 'gold:1'), 'too_late')
        self.assertEqual(effect_count(self.db, 'gold:1'), 1)

    def test_cancel_retry_survives_restart(self):
        self.assertEqual(cancel_guarded(self.db, 'x'), 'cancelled')
        self.db.close(); self.db = connect(self.path)
        self.assertEqual(cancel_guarded(self.db, 'x'), 'cancelled')
        self.assertEqual(apply_guarded(self.db, 'x', b'x'), 'fenced')

    def test_effect_retry_survives_restart(self):
        self.assertEqual(apply_guarded(self.db, 'x', b'x'), 'applied')
        self.db.close(); self.db = connect(self.path)
        self.assertEqual(apply_guarded(self.db, 'x', b'x'), 'duplicate')
        self.assertEqual(cancel_guarded(self.db, 'x'), 'too_late')
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_payload_conflict(self):
        apply_guarded(self.db, 'x', b'a')
        with self.assertRaises(ValueError): apply_guarded(self.db, 'x', b'b')
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_fence_garbage_collection_breaks_safety(self):
        self.assertEqual(cancel_guarded(self.db, 'x'), 'cancelled')
        # Intentionally simulate unsafe tombstone expiry; never do this in service.
        self.db.execute('DELETE FROM fences WHERE id=?', ('x',))
        self.assertEqual(apply_guarded(self.db, 'x', b'x'), 'applied')
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_two_connections(self):
        other = connect(self.path)
        try:
            self.assertEqual(cancel_guarded(self.db, 'x'), 'cancelled')
            self.assertEqual(apply_guarded(other, 'x', b'x'), 'fenced')
        finally: other.close()

    def test_randomized_cross_domain(self):
        for family in ('seo', 'gold'):
            for seed in range(500):
                op = f'{family}:{seed}'
                rng = random.Random(seed + (family == 'gold') * 100000)
                actions = ['apply', 'cancel', 'retry_apply', 'retry_cancel']
                rng.shuffle(actions)
                saw_success = False
                for action in actions:
                    if action.endswith('apply') or action == 'apply':
                        apply_guarded(self.db, op, op.encode())
                    else:
                        if cancel_guarded(self.db, op) == 'cancelled':
                            saw_success = True
                    if rng.randrange(4) == 0:
                        self.db.close(); self.db = connect(self.path)
                self.assertLessEqual(effect_count(self.db, op), 1)
                if saw_success:
                    self.assertEqual(effect_count(self.db, op), 0)

if __name__ == '__main__': unittest.main()
