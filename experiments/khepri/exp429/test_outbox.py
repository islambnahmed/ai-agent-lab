import multiprocessing
import os
import tempfile
import unittest
from pathlib import Path
from outbox import (Outbox, IdempotentSink, NonIdempotentSink, SplitCommitSink,
                    SimulatedCrash, event_key)


def worker_apply(path, key, kind, payload, ready, go, output):
    sink = IdempotentSink(path)
    ready.put(1)
    go.wait()
    try:
        output.put(sink.apply(key, kind, payload))
    except Exception as exc:
        output.put(type(exc).__name__)


def worker_die_after_sink(outbox_path, sink_path):
    box = Outbox(outbox_path)
    sink = IdempotentSink(sink_path)
    try:
        box.deliver('seo','job-1',sink,crash_at='after_sink')
    except SimulatedCrash:
        os._exit(23)
    os._exit(24)


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.box = Outbox(self.root/'outbox.sqlite')
        self.sink = IdempotentSink(self.root/'sink.sqlite')
        self.payload = {'lead':'synthetic-1','score':4}
        self.box.enqueue('seo', 'job-1', 'lead', self.payload)

    def test_clean_delivery(self):
        self.assertEqual(self.box.deliver('seo','job-1',self.sink),'applied')
        self.assertEqual(self.sink.count(),1)
        self.assertEqual(self.box.status('seo','job-1'),('done',1))

    def test_before_sink_crash_retries_once(self):
        with self.assertRaises(SimulatedCrash):
            self.box.deliver('seo','job-1',self.sink,crash_at='before_sink')
        self.assertEqual(self.sink.count(),0)
        self.box.deliver('seo','job-1',self.sink)
        self.assertEqual(self.sink.count(),1)

    def test_after_sink_crash_retries_without_duplicate(self):
        with self.assertRaises(SimulatedCrash):
            self.box.deliver('seo','job-1',self.sink,crash_at='after_sink')
        self.assertEqual(self.box.status('seo','job-1'),('pending',1))
        self.assertEqual(self.box.deliver('seo','job-1',self.sink),'replayed')
        self.assertEqual(self.sink.count(),1)

    def test_after_ack_crash_is_already_done(self):
        with self.assertRaises(SimulatedCrash):
            self.box.deliver('seo','job-1',self.sink,crash_at='after_ack')
        self.assertEqual(self.box.deliver('seo','job-1',self.sink),'already_done')
        self.assertEqual(self.sink.count(),1)

    def test_outbox_restart_preserves_pending(self):
        with self.assertRaises(SimulatedCrash):
            self.box.deliver('seo','job-1',self.sink,crash_at='after_sink')
        reopened = Outbox(self.root/'outbox.sqlite')
        reopened.deliver('seo','job-1',IdempotentSink(self.root/'sink.sqlite'))
        self.assertEqual(self.sink.count(),1)

    def test_nonidempotent_sink_duplicates_after_crash(self):
        unsafe = NonIdempotentSink(self.root/'unsafe.sqlite')
        with self.assertRaises(SimulatedCrash):
            self.box.deliver('seo','job-1',unsafe,crash_at='after_sink')
        self.box.deliver('seo','job-1',unsafe)
        self.assertEqual(unsafe.count(),2)

    def test_conflicting_outbox_reuse_rejected(self):
        self.assertFalse(self.box.enqueue('seo','job-1','lead',self.payload))
        with self.assertRaises(ValueError):
            self.box.enqueue('seo','job-1','lead',{'lead':'different'})

    def test_conflicting_sink_reuse_rejected(self):
        key = event_key('seo','job-1')
        self.sink.apply(key,'lead',self.payload)
        with self.assertRaises(ValueError):
            self.sink.apply(key,'lead',{'lead':'different'})
        self.assertEqual(self.sink.count(),1)

    def test_scope_prevents_key_collision(self):
        self.box.enqueue('gold','job-1','quote',{'value':1})
        self.box.deliver('seo','job-1',self.sink)
        self.box.deliver('gold','job-1',self.sink)
        self.assertEqual(self.sink.count(),2)

    def test_unambiguous_scope_encoding(self):
        self.assertNotEqual(event_key('a:b','c'),event_key('a','b:c'))
        with self.assertRaises(ValueError):
            event_key('','c')

    def test_atomic_sink_two_processes(self):
        key = event_key('seo','race')
        ctx = multiprocessing.get_context('spawn')
        ready, out, go = ctx.Queue(),ctx.Queue(),ctx.Event()
        ps = [ctx.Process(target=worker_apply,args=(self.sink.path,key,'lead',self.payload,ready,go,out)) for _ in range(2)]
        for p in ps: p.start()
        for _ in ps: ready.get(timeout=10)
        go.set()
        results=[out.get(timeout=10) for _ in ps]
        for p in ps:
            p.join(timeout=10)
            self.assertEqual(p.exitcode,0)
        self.assertCountEqual(results,['applied','replayed'])
        self.assertEqual(self.sink.count_for(key),1)

    def test_real_process_exit_after_sink_commit(self):
        ctx = multiprocessing.get_context('spawn')
        p = ctx.Process(target=worker_die_after_sink,args=(self.box.path,self.sink.path))
        p.start()
        p.join(timeout=10)
        self.assertEqual(p.exitcode,23)
        self.assertEqual(self.box.status('seo','job-1'),('pending',1))
        self.assertEqual(self.sink.count(),1)
        self.assertEqual(self.box.deliver('seo','job-1',self.sink),'replayed')
        self.assertEqual(self.sink.count(),1)

    def test_sink_transaction_crash_rolls_back_effect_and_receipt(self):
        key=event_key('seo','tx-crash')
        with self.assertRaises(SimulatedCrash):
            self.sink.apply(key,'lead',self.payload,crash_at='inside_sink_tx')
        self.assertEqual(self.sink.count_for(key),0)
        self.assertEqual(self.sink.apply(key,'lead',self.payload),'applied')
        self.assertEqual(self.sink.count_for(key),1)

    def test_non_atomic_receipt_counterexample(self):
        broken = SplitCommitSink(self.root/'broken.sqlite')
        key = event_key('seo','job-1')
        with self.assertRaises(SimulatedCrash):
            broken.apply(key,'lead',self.payload,crash_after_effect=True)
        broken.apply(key,'lead',self.payload)
        self.assertEqual(broken.count_for(key),2)

    def test_ack_before_sink_can_lose_effect(self):
        # Counterexample to an alternative ordering: local ack first, then crash.
        from outbox import connect
        key = event_key('seo','job-1')
        with connect(self.box.path) as con:
            con.execute("UPDATE jobs SET state='done' WHERE key=?",(key,))
        self.assertEqual(self.box.deliver('seo','job-1',self.sink),'already_done')
        self.assertEqual(self.sink.count(),0)

    def test_same_key_same_payload_semantic_collision_unobservable(self):
        # Two distinct intents incorrectly assigned the same key+payload coalesce.
        key = event_key('seo','same-id')
        self.assertEqual(self.sink.apply(key,'lead',self.payload),'applied')
        self.assertEqual(self.sink.apply(key,'lead',self.payload),'replayed')
        self.assertEqual(self.sink.count_for(key),1)


if __name__ == '__main__':
    unittest.main()
