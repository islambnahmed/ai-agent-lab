import unittest
import random
import tempfile
import os
from retention import TimedReceiptSink, ContiguousWatermarkSink

class RetentionTests(unittest.TestCase):
    def setUp(self):
        self._sinks=[]

    def tearDown(self):
        for sink in self._sinks: sink.close()

    def sink(self, cls, *args, **kwargs):
        s=cls(*args, **kwargs)
        self._sinks.append(s)
        return s

    def test_ttl_late_retry_duplicates(self):
        s = self.sink(TimedReceiptSink, ttl=10)
        self.assertEqual(s.deliver("seo",1,{"lead":7},0),"applied")
        self.assertEqual(s.deliver("seo",1,{"lead":7},11),"applied")
        self.assertEqual(s.effect_count(),2)

    def test_ttl_within_window_dedupes(self):
        s = self.sink(TimedReceiptSink, ttl=10)
        self.assertEqual(s.deliver("gold",1,{"price":100},0),"applied")
        self.assertEqual(s.deliver("gold",1,{"price":100},9),"replayed")
        self.assertEqual(s.effect_count(),1)

    def test_permanent_receipt_survives_late_retry(self):
        s = self.sink(TimedReceiptSink, ttl=None)
        s.deliver("seo",1,{"lead":7},0)
        self.assertEqual(s.deliver("seo",1,{"lead":7},10**9),"replayed")
        self.assertEqual(s.effect_count(),1)
        self.assertEqual(s.receipt_count(),1)

    def test_payload_conflict_not_overwritten(self):
        s = self.sink(TimedReceiptSink, ttl=None)
        s.deliver("seo",1,{"lead":7},0)
        with self.assertRaisesRegex(ValueError,"conflicting"):
            s.deliver("seo",1,{"lead":8},1)
        self.assertEqual(s.effect_count(),1)

    def test_ttl_expiry_loses_conflict_detection(self):
        s = self.sink(TimedReceiptSink, ttl=10)
        s.deliver("seo",1,{"lead":7},0)
        self.assertEqual(s.deliver("seo",1,{"lead":8},11),"applied")
        self.assertEqual(s.effect_count(),2)

    def test_contiguous_watermark_prunes(self):
        s = self.sink(ContiguousWatermarkSink)
        a=s.issue("seo",{"a":1}); b=s.issue("seo",{"a":2})
        self.assertEqual((a,b),(1,2))
        s.deliver("seo",a,{"a":1}); s.deliver("seo",b,{"a":2})
        self.assertEqual(s.watermark("seo"),2)
        self.assertEqual(s.receipt_count(),0)
        self.assertEqual(s.deliver("seo",a,{"a":1}),"stale_rejected")
        self.assertEqual(s.effect_count(),2)

    def test_out_of_order_does_not_skip_pending(self):
        s=self.sink(ContiguousWatermarkSink)
        for n in (1,2,3): s.issue("gold",{"n":n})
        s.deliver("gold",3,{"n":3})
        self.assertEqual(s.watermark("gold"),0)
        s.deliver("gold",1,{"n":1})
        self.assertEqual(s.watermark("gold"),1)
        self.assertEqual(s.deliver("gold",3,{"n":3}),"replayed")
        s.deliver("gold",2,{"n":2})
        self.assertEqual(s.watermark("gold"),3)
        self.assertEqual(s.effect_count(),3)
        self.assertEqual(s.receipt_count(),0)

    def test_unregistered_seq_rejected(self):
        s=self.sink(ContiguousWatermarkSink); s.issue("seo",{"a":1})
        with self.assertRaisesRegex(ValueError,"unregistered"):
            s.deliver("seo",2,{"a":2})
        self.assertEqual(s.effect_count(),0)

    def test_unknown_stream_rejected(self):
        s=self.sink(ContiguousWatermarkSink)
        with self.assertRaisesRegex(ValueError,"unknown"):
            s.deliver("untrusted",1,{"x":1})

    def test_digest_mismatch_rejected(self):
        s=self.sink(ContiguousWatermarkSink); seq=s.issue("seo",{"a":1})
        with self.assertRaisesRegex(ValueError,"conflicting"):
            s.deliver("seo",seq,{"a":2})
        self.assertEqual(s.effect_count(),0)

    def test_cancel_explicitly_compacts_without_effect(self):
        s=self.sink(ContiguousWatermarkSink); a=s.issue("seo",{"a":1}); b=s.issue("seo",{"a":2})
        s.deliver("seo",b,{"a":2}); s.cancel("seo",a)
        self.assertEqual(s.watermark("seo"),2)
        self.assertEqual(s.effect_count(),1)

    def test_cancel_after_done_fails(self):
        s=self.sink(ContiguousWatermarkSink); a=s.issue("seo",{"a":1}); s.deliver("seo",a,{"a":1})
        with self.assertRaisesRegex(ValueError,"cannot cancel"):
            s.cancel("seo",a)

    def test_liveness_gap_prevents_compaction(self):
        s=self.sink(ContiguousWatermarkSink)
        for n in range(1,102): s.issue("gold",{"n":n})
        for n in range(2,102): s.deliver("gold",n,{"n":n})
        self.assertEqual(s.watermark("gold"),0)
        self.assertEqual(s.receipt_count(),101)
        s.deliver("gold",1,{"n":1})
        self.assertEqual(s.watermark("gold"),101)
        self.assertEqual(s.receipt_count(),0)

    def test_stream_scope_isolation(self):
        s=self.sink(ContiguousWatermarkSink)
        a=s.issue("seo",{"n":1}); b=s.issue("gold",{"n":1})
        self.assertEqual((a,b),(1,1))
        s.deliver("seo",a,{"n":1})
        self.assertEqual(s.watermark("gold"),0)
        s.deliver("gold",b,{"n":1})
        self.assertEqual(s.effect_count(),2)

    def test_repeated_stale_retry_never_mutates_effects(self):
        s=self.sink(ContiguousWatermarkSink); seq=s.issue("seo",{"x":1}); s.deliver("seo",seq,{"x":1})
        for _ in range(50): self.assertEqual(s.deliver("seo",seq,{"x":1}),"stale_rejected")
        self.assertEqual(s.effect_count(),1)

    def test_pruned_payload_cannot_be_reverified(self):
        s=self.sink(ContiguousWatermarkSink); seq=s.issue("seo",{"x":1}); s.deliver("seo",seq,{"x":1})
        self.assertEqual(s.deliver("seo",seq,{"x":999}),"stale_rejected")
        self.assertEqual(s.effect_count(),1)

    def test_seeded_out_of_order_replay_and_cancellation(self):
        rng=random.Random(430)
        for stream in ("seo", "gold"):
            for trial in range(30):
                s=self.sink(ContiguousWatermarkSink)
                intents=[]
                for n in range(1,21):
                    payload={"stream":stream,"trial":trial,"n":n}
                    seq=s.issue(stream,payload)
                    intents.append((seq,payload))
                order=intents[:]
                rng.shuffle(order)
                cancelled={seq for seq,_ in intents if seq % 7 == 0}
                for seq,payload in order:
                    if seq in cancelled:
                        s.cancel(stream,seq)
                    else:
                        self.assertEqual(s.deliver(stream,seq,payload),"applied")
                        self.assertIn(s.deliver(stream,seq,payload),("replayed","stale_rejected"))
                self.assertEqual(s.watermark(stream),20)
                self.assertEqual(s.receipt_count(),0)
                self.assertEqual(s.effect_count(),20-len(cancelled))
                for seq,payload in intents:
                    self.assertEqual(s.deliver(stream,seq,payload),"stale_rejected")
                self.assertEqual(s.effect_count(),20-len(cancelled))

    def test_restart_preserves_watermark_and_rejects_late_retry(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,"sink.sqlite")
            s=ContiguousWatermarkSink(path)
            seq=s.issue("seo",{"lead":4})
            self.assertEqual(s.deliver("seo",seq,{"lead":4}),"applied")
            s.close()
            restarted=ContiguousWatermarkSink(path)
            self.assertEqual(restarted.watermark("seo"),1)
            self.assertEqual(restarted.deliver("seo",seq,{"lead":4}),"stale_rejected")
            self.assertEqual(restarted.effect_count(),1)
            restarted.close()

    def test_effect_and_done_mark_rollback_together(self):
        s=self.sink(ContiguousWatermarkSink)
        seq=s.issue("gold",{"quote":3})
        s.db.execute("""CREATE TRIGGER reject_done BEFORE UPDATE OF status ON intents
                        WHEN NEW.status='done' BEGIN SELECT RAISE(ABORT,'injected'); END;""")
        with self.assertRaisesRegex(Exception,"injected"):
            s.deliver("gold",seq,{"quote":3})
        self.assertEqual(s.effect_count(),0)
        self.assertEqual(s.watermark("gold"),0)
        s.db.execute("DROP TRIGGER reject_done")
        self.assertEqual(s.deliver("gold",seq,{"quote":3}),"applied")
        self.assertEqual(s.effect_count(),1)

    def test_naive_max_seen_counterexample(self):
        registered={1,2,3}; delivered={3}
        naive_watermark=max(delivered)
        self.assertIn(2,registered)
        self.assertNotIn(2,delivered)
        self.assertLessEqual(2,naive_watermark)

if __name__ == '__main__': unittest.main()
