import os
import tempfile
import unittest
from durable_delivery import (connect, enqueue, claim, apply_sink, ack,
    deliver_once, effect_count, pending_count, purge_receipts, Claim, digest)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'lab.sqlite')
        self.db = connect(self.path)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_enqueue_and_deliver(self):
        enqueue(self.db, 'seo:1', b'update')
        self.assertEqual(deliver_once(self.db, 'w1', 0), 'applied')
        self.assertEqual((pending_count(self.db), effect_count(self.db)), (0, 1))

    def test_enqueue_replay_same_bytes_safe(self):
        enqueue(self.db, 'x', b'hello')
        enqueue(self.db, 'x', b'hello')
        self.assertEqual(pending_count(self.db), 1)

    def test_enqueue_replay_different_bytes_rejected(self):
        enqueue(self.db, 'x', b'hello')
        with self.assertRaises(ValueError):
            enqueue(self.db, 'x', b'changed')
        self.assertEqual(pending_count(self.db), 1)

    def test_crash_after_claim_recovers(self):
        enqueue(self.db, 'x', b'x')
        self.assertEqual(deliver_once(self.db, 'w1', 0, 'after_claim'), 'crashed_after_claim')
        self.db.close()
        self.db = connect(self.path)
        self.assertEqual(deliver_once(self.db, 'w2', 9), 'idle')
        self.assertEqual(deliver_once(self.db, 'w2', 10), 'applied')
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_crash_after_effect_recovers_without_duplicate(self):
        enqueue(self.db, 'x', b'x')
        self.assertEqual(deliver_once(self.db, 'w1', 0, 'after_effect'), 'crashed_after_effect')
        self.db.close()
        self.db = connect(self.path)
        self.assertEqual(deliver_once(self.db, 'w2', 10), 'duplicate')
        self.assertEqual(effect_count(self.db, 'x'), 1)
        self.assertEqual(pending_count(self.db), 0)

    def test_crash_after_ack_does_not_redeliver(self):
        enqueue(self.db, 'x', b'x')
        self.assertEqual(deliver_once(self.db, 'w1', 0), 'applied')
        self.db.close()
        self.db = connect(self.path)
        self.assertEqual(deliver_once(self.db, 'w2', 100), 'idle')
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_stale_ack_fenced(self):
        enqueue(self.db, 'x', b'x')
        old = claim(self.db, 'old', 0, 10)
        new = claim(self.db, 'new', 10, 10)
        self.assertFalse(ack(self.db, old))
        self.assertEqual(apply_sink(self.db, new, 10), 'applied')
        self.assertTrue(ack(self.db, new))
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_late_old_worker_is_deduplicated(self):
        enqueue(self.db, 'x', b'x')
        old = claim(self.db, 'old', 0)
        new = claim(self.db, 'new', 10)
        self.assertEqual(apply_sink(self.db, new, 10), 'applied')
        self.assertEqual(apply_sink(self.db, old, 11), 'duplicate')
        self.assertFalse(ack(self.db, old))
        self.assertTrue(ack(self.db, new))
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_conflicting_sink_digest_fails(self):
        enqueue(self.db, 'x', b'original')
        c = claim(self.db, 'w', 0)
        self.assertEqual(apply_sink(self.db, c, 0), 'applied')
        forged = Claim('x', b'changed', digest(b'changed'), 'w', c.generation)
        with self.assertRaises(ValueError):
            apply_sink(self.db, forged, 1)
        self.assertEqual(effect_count(self.db, 'x'), 1)

    def test_tampered_claim_fails(self):
        enqueue(self.db, 'x', b'original')
        c = claim(self.db, 'w', 0)
        forged = Claim('x', b'changed', c.digest, 'w', c.generation)
        with self.assertRaises(ValueError):
            apply_sink(self.db, forged, 1)

    def test_expired_receipt_allows_duplicate_counterexample(self):
        enqueue(self.db, 'x', b'x')
        c = claim(self.db, 'w', 0)
        self.assertEqual(apply_sink(self.db, c, 0), 'applied')
        self.assertEqual(purge_receipts(self.db, 1), 1)
        retry = claim(self.db, 'w2', 10)
        self.assertEqual(apply_sink(self.db, retry, 10), 'applied')
        self.assertEqual(effect_count(self.db, 'x'), 2)

    def test_two_independent_cases(self):
        enqueue(self.db, 'seo:rank', b'{"action":"seo"}')
        enqueue(self.db, 'gold:price', b'{"action":"gold"}')
        self.assertEqual(deliver_once(self.db, 'w', 0), 'applied')
        self.assertEqual(deliver_once(self.db, 'w', 0), 'applied')
        self.assertEqual(effect_count(self.db), 2)

    def test_sink_receipt_and_effect_rollback_together(self):
        enqueue(self.db, 'x', b'x')
        c = claim(self.db, 'w', 0)
        self.db.execute("""CREATE TRIGGER fail_effect BEFORE INSERT ON effects
                          BEGIN SELECT RAISE(ABORT,'injected sink failure'); END""")
        with self.assertRaises(Exception):
            apply_sink(self.db, c, 0)
        self.assertEqual(effect_count(self.db), 0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM receipts').fetchone()[0], 0)
        self.db.execute('DROP TRIGGER fail_effect')
        self.assertEqual(apply_sink(self.db, c, 1), 'applied')

    def test_two_connections_claim_no_duplicate(self):
        enqueue(self.db, 'x', b'x')
        other = connect(self.path)
        try:
            self.assertIsNotNone(claim(self.db, 'w1', 0))
            self.assertIsNone(claim(other, 'w2', 0))
        finally:
            other.close()

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            enqueue(self.db, '', b'x')
        with self.assertRaises(ValueError):
            enqueue(self.db, 'x', 'not-bytes')
        with self.assertRaises(ValueError):
            claim(self.db, 'w', 0, 0)


if __name__ == '__main__':
    unittest.main()
