import os
import random
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp440"))
from durable_delivery import (connect, enqueue, claim, ack, apply_sink, digest,
                              effect_count, Claim, pending_count)
from verified_delivery import dispatch, ack_verified, Rejected


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.out_path = os.path.join(self.temp.name,'out.sqlite')
        self.sink_path = os.path.join(self.temp.name,'sink.sqlite')
        self.out = connect(self.out_path)
        self.sink = connect(self.sink_path)

    def tearDown(self):
        self.out.close()
        self.sink.close()
        self.temp.cleanup()

    def test_baseline_premature_ack_loses_effect(self):
        enqueue(self.out, 'seo:lost', b'update')
        c = claim(self.out, 'w', 0)
        self.assertTrue(ack(self.out, c))
        self.assertEqual(effect_count(self.sink), 0)
        self.assertEqual(pending_count(self.out), 0)

    def test_baseline_unbacked_sink_effect(self):
        fake = Claim('gold:unbacked', b'price', digest(b'price'), 'fake', 1)
        self.assertEqual(apply_sink(self.sink, fake, 0), 'applied')
        self.assertEqual(effect_count(self.sink), 1)

    def test_verified_ack_requires_receipt(self):
        enqueue(self.out, 'seo:1', b'update')
        c = claim(self.out, 'w', 0)
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,c,0)
        self.assertEqual(pending_count(self.out),1)
        self.assertEqual(dispatch(self.out,self.sink,c,0),'applied')
        self.assertTrue(ack_verified(self.out,self.sink,c,0))
        self.assertEqual((pending_count(self.out),effect_count(self.sink)),(0,1))

    def test_unbacked_and_modified_claims_rejected(self):
        fake = Claim('x',b'x',digest(b'x'),'w',1)
        with self.assertRaises(Rejected): dispatch(self.out,self.sink,fake,0)
        enqueue(self.out,'x',b'original')
        c=claim(self.out,'w',0)
        for forged in [Claim('x',b'other',digest(b'other'),'w',c.generation),
                       Claim('x',c.payload,c.digest,'other',c.generation),
                       Claim('x',c.payload,c.digest,'w',c.generation+1)]:
            with self.assertRaises(Rejected): dispatch(self.out,self.sink,forged,0)
        self.assertEqual(effect_count(self.sink),0)

    def test_expired_claim_rejected_even_without_new_owner(self):
        enqueue(self.out,'x',b'x')
        c=claim(self.out,'w',0,10)
        with self.assertRaises(Rejected): dispatch(self.out,self.sink,c,10)
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,c,10)

    def test_stale_worker_rejected_after_reclaim(self):
        enqueue(self.out,'x',b'x')
        old=claim(self.out,'w1',0,10)
        new=claim(self.out,'w2',10,10)
        with self.assertRaises(Rejected): dispatch(self.out,self.sink,old,11)
        self.assertEqual(dispatch(self.out,self.sink,new,11),'applied')
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,old,11)
        self.assertTrue(ack_verified(self.out,self.sink,new,11))
        self.assertEqual(effect_count(self.sink),1)

    def test_recovery_after_effect_before_ack_separate_databases(self):
        for family in ['seo','gold']:
            enqueue(self.out,family,b'payload-'+family.encode())
        for family in ['seo','gold']:
            c=claim(self.out,'w',0)
            self.assertEqual(dispatch(self.out,self.sink,c,0),'applied')
            self.out.close(); self.sink.close()
            self.out=connect(self.out_path); self.sink=connect(self.sink_path)
            new=claim(self.out,'recover',10)
            self.assertEqual(dispatch(self.out,self.sink,new,10),'duplicate')
            self.assertTrue(ack_verified(self.out,self.sink,new,10))
        self.assertEqual(effect_count(self.sink),2)
        self.assertEqual(pending_count(self.out),0)

    def test_receipt_loss_fails_closed(self):
        enqueue(self.out,'x',b'x')
        c=claim(self.out,'w',0)
        dispatch(self.out,self.sink,c,0)
        self.sink.execute('DELETE FROM receipts WHERE id=?',('x',))
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,c,0)
        self.assertEqual(pending_count(self.out),1)

    def test_receipt_without_effect_not_sufficient(self):
        enqueue(self.out,'x',b'x')
        c=claim(self.out,'w',0)
        self.sink.execute('INSERT INTO receipts(id,digest,created_at) VALUES (?,?,?)',
                          ('x',c.digest,0))
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,c,0)
        self.assertEqual(pending_count(self.out),1)

    def test_sink_effect_without_receipt_not_sufficient(self):
        enqueue(self.out,'x',b'x')
        c=claim(self.out,'w',0)
        self.sink.execute('INSERT INTO effects(op_id,digest,payload) VALUES (?,?,?)',
                          ('x',c.digest,c.payload))
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,c,0)
        self.assertEqual(pending_count(self.out),1)

    def test_rollback_on_sink_failure(self):
        enqueue(self.out,'x',b'x')
        c=claim(self.out,'w',0)
        self.sink.execute("""CREATE TRIGGER fail_effect BEFORE INSERT ON effects
                     BEGIN SELECT RAISE(ABORT,'fail'); END""")
        with self.assertRaises(Exception): dispatch(self.out,self.sink,c,0)
        with self.assertRaises(Rejected): ack_verified(self.out,self.sink,c,0)
        self.sink.execute('DROP TRIGGER fail_effect')
        self.assertEqual(dispatch(self.out,self.sink,c,0),'applied')
        self.assertTrue(ack_verified(self.out,self.sink,c,0))

    def test_randomized_state_machine(self):
        for family in ['seo','gold']:
            for seed in range(100):
                op=f'{family}:{seed}'
                payload=f'{family}-payload-{seed}'.encode()
                enqueue(self.out,op,payload)
                rng=random.Random(seed+('seo'==family)*10000)
                now=seed*100
                current=claim(self.out,'w0',now,10)
                for step in range(40):
                    action=rng.randrange(7)
                    if action==0:
                        try: ack_verified(self.out,self.sink,current,now)
                        except Rejected: pass
                    elif action==1:
                        try: dispatch(self.out,self.sink,current,now)
                        except Rejected: pass
                    elif action==2:
                        forged=Claim(op,b'forged',digest(b'forged'),current.owner,current.generation)
                        with self.assertRaises(Rejected): dispatch(self.out,self.sink,forged,now)
                    elif action==3:
                        fake=Claim('unbacked:'+op,payload,digest(payload),'w',1)
                        with self.assertRaises(Rejected): dispatch(self.out,self.sink,fake,now)
                    elif action==4:
                        now+=10
                        next_claim=claim(self.out,'w'+str(step+1),now,10)
                        if next_claim: current=next_claim
                    elif action==5:
                        self.out.close(); self.sink.close()
                        self.out=connect(self.out_path); self.sink=connect(self.sink_path)
                    status=self.out.execute('SELECT status FROM outbox WHERE id=?',(op,)).fetchone()[0]
                    count=effect_count(self.sink,op)
                    self.assertLessEqual(count,1)
                    if status=='done': self.assertEqual(count,1)
                for extra in range(3):
                    if self.out.execute('SELECT status FROM outbox WHERE id=?',(op,)).fetchone()[0]=='done': break
                    now+=10
                    c=claim(self.out,'recovery',now,10)
                    self.assertIsNotNone(c)
                    dispatch(self.out,self.sink,c,now)
                    ack_verified(self.out,self.sink,c,now)
                self.assertEqual(effect_count(self.sink,op),1)
                self.assertEqual(self.out.execute('SELECT status FROM outbox WHERE id=?',(op,)).fetchone()[0],'done')


if __name__=='__main__': unittest.main()
