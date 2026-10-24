"""Reproducible local tests, including multi-process races and crash rollback."""
import multiprocessing as mp
import os
import random
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from approval_sqlite import ApprovalDB


def worker_redeem(dbpath, approval, path, payload, gate, output):
    gate.wait()
    output.put(ApprovalDB(dbpath).redeem(approval, path, payload))


def worker_crash_before_commit(dbpath):
    con = sqlite3.connect(dbpath, isolation_level=None)
    con.execute('BEGIN IMMEDIATE')
    con.execute("UPDATE approvals SET consumed=1 WHERE approval_id='crash'")
    con.execute("UPDATE heads SET revision=revision+1,content=x'424144' WHERE path='crash-path'")
    os._exit(77)


class TestApprovalDB(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name)/'store.sqlite')
        self.db = ApprovalDB(self.path)

    def test_new_path(self):
        self.assertEqual(self.db.issue('a','seo/new',b'fresh'),0)
        self.assertEqual(self.db.redeem('a','seo/new',b'fresh'),'ok')
        self.assertEqual(self.db.snapshot('seo/new'),(1,1,b'fresh'))

    def test_existing_path(self):
        self.db.external_write('gold/spot',b'old')
        self.assertEqual(self.db.issue('a','gold/spot',b'new'),1)
        self.assertEqual(self.db.redeem('a','gold/spot',b'new'),'ok')
        self.assertEqual(self.db.snapshot('gold/spot'),(2,1,b'new'))

    def test_stale_peer_write(self):
        self.db.external_write('seo/a',b'v1')
        self.db.issue('a','seo/a',b'v3')
        self.db.external_write('seo/a',b'v2')
        self.assertEqual(self.db.redeem('a','seo/a',b'v3'),'stale')
        self.assertEqual(self.db.snapshot('seo/a'),(2,1,b'v2'))
        self.assertEqual(self.db.redeem('a','seo/a',b'v3'),'invalid_or_consumed')

    def test_aba(self):
        self.db.external_write('gold/a',b'v1')
        self.db.issue('a','gold/a',b'v2')
        self.db.external_write('gold/a',b'other')
        self.db.external_write('gold/a',b'v1')
        self.assertEqual(self.db.redeem('a','gold/a',b'v2'),'stale')
        self.assertEqual(self.db.snapshot('gold/a'),(3,1,b'v1'))

    def test_delete_recreate_revision(self):
        self.db.external_write('seo/a',b'old')
        self.db.issue('a','seo/a',b'approved')
        self.db.external_delete('seo/a')
        self.db.external_write('seo/a',b'new')
        self.assertEqual(self.db.snapshot('seo/a'),(3,1,b'new'))
        self.assertEqual(self.db.redeem('a','seo/a',b'approved'),'stale')

    def test_absent_delete_create_race(self):
        self.db.issue('a','gold/missing',b'approved')
        self.db.external_write('gold/missing',b'peer')
        self.db.external_delete('gold/missing')
        self.assertEqual(self.db.redeem('a','gold/missing',b'approved'),'stale')
        self.assertEqual(self.db.snapshot('gold/missing'),(2,0,None))

    def test_unrelated_path(self):
        self.db.issue('a','seo/a',b'approved')
        self.db.external_write('seo/b',b'peer')
        self.assertEqual(self.db.redeem('a','seo/a',b'approved'),'ok')

    def test_payload_and_path_binding(self):
        self.db.issue('a','seo/a',b'approved')
        self.assertEqual(self.db.redeem('a','seo/a',b'evil'),'plan_mismatch')
        self.assertEqual(self.db.redeem('a','seo/b',b'approved'),'plan_mismatch')
        self.assertEqual(self.db.redeem('a','seo/a',b'approved'),'ok')

    def test_single_use(self):
        self.db.issue('a','seo/a',b'ok')
        self.assertEqual(self.db.redeem('a','seo/a',b'ok'),'ok')
        self.assertEqual(self.db.redeem('a','seo/a',b'ok'),'invalid_or_consumed')

    def test_duplicate_id(self):
        self.db.issue('a','seo/a',b'ok')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.issue('a','seo/b',b'other')

    def test_malformed_payload(self):
        with self.assertRaises(TypeError):
            self.db.issue('a','seo/a','string-not-bytes')

    def test_two_receipts_same_version_only_one_wins(self):
        self.db.external_write('seo/a',b'old')
        self.db.issue('a','seo/a',b'one')
        self.db.issue('b','seo/a',b'two')
        ctx=mp.get_context('spawn')
        gate=ctx.Event(); output=ctx.Queue()
        p1=ctx.Process(target=worker_redeem,args=(self.path,'a','seo/a',b'one',gate,output))
        p2=ctx.Process(target=worker_redeem,args=(self.path,'b','seo/a',b'two',gate,output))
        p1.start();p2.start();gate.set()
        p1.join(15);p2.join(15)
        self.assertEqual((p1.exitcode,p2.exitcode),(0,0))
        self.assertEqual(sorted([output.get(timeout=2),output.get(timeout=2)]),['ok','stale'])
        self.assertEqual(self.db.snapshot('seo/a')[0],2)

    def test_same_receipt_multiprocess_only_once(self):
        self.db.issue('a','gold/a',b'ok')
        ctx=mp.get_context('spawn'); gate=ctx.Event(); output=ctx.Queue()
        procs=[ctx.Process(target=worker_redeem,args=(self.path,'a','gold/a',b'ok',gate,output)) for _ in range(3)]
        for p in procs:p.start()
        gate.set()
        for p in procs:p.join(15)
        self.assertEqual([p.exitcode for p in procs],[0]*3)
        statuses=sorted(output.get(timeout=2) for _ in procs)
        self.assertEqual(statuses,['invalid_or_consumed','invalid_or_consumed','ok'])

    def test_crash_before_commit_rolls_back(self):
        self.db.external_write('crash-path',b'old')
        self.db.issue('crash','crash-path',b'approved')
        ctx=mp.get_context('spawn')
        p=ctx.Process(target=worker_crash_before_commit,args=(self.path,))
        p.start();p.join(15)
        self.assertEqual(p.exitcode,77)
        self.assertEqual(self.db.snapshot('crash-path'),(1,1,b'old'))
        self.assertEqual(self.db.redeem('crash','crash-path',b'approved'),'ok')

    def test_row_version_reset_counterexample(self):
        # A naive version stored only in the deletable resource row is not monotonic.
        con=sqlite3.connect(':memory:')
        con.execute('CREATE TABLE naive(path TEXT PRIMARY KEY,version INT,content BLOB)')
        con.execute('INSERT INTO naive VALUES (?,?,?)',('seo/a',1,b'old'))
        approved=con.execute('SELECT version FROM naive WHERE path=?',('seo/a',)).fetchone()[0]
        con.execute('DELETE FROM naive WHERE path=?',('seo/a',))
        con.execute('INSERT INTO naive VALUES (?,?,?)',('seo/a',1,b'peer'))
        current=con.execute('SELECT version FROM naive WHERE path=?',('seo/a',)).fetchone()[0]
        self.assertEqual(approved,current) # stale approval falsely appears current
        con.close()

    def test_unprotected_direct_sql_write_counterexample(self):
        vulnerable=ApprovalDB(str(Path(self.tmp.name)/'unprotected.sqlite'),enforce_triggers=False)
        vulnerable.external_write('gold/a',b'original')
        vulnerable.issue('a','gold/a',b'approved')
        con=sqlite3.connect(vulnerable.db_path)
        try:
            con.execute("UPDATE heads SET content=? WHERE path=?", (b'peer','gold/a'))
            con.commit()
        finally: con.close()
        self.assertEqual(vulnerable.snapshot('gold/a'),(1,1,b'peer'))
        self.assertEqual(vulnerable.redeem('a','gold/a',b'approved'),'ok')
        # Direct SQL bypasses the API and its version increment if triggers are absent.

    def test_trigger_detects_unversioned_sql_write(self):
        self.db.external_write('gold/a',b'original')
        self.db.issue('a','gold/a',b'approved')
        con=sqlite3.connect(self.path)
        try:
            con.execute("UPDATE heads SET content=? WHERE path=?", (b'peer','gold/a'))
            con.commit()
        finally: con.close()
        self.assertEqual(self.db.snapshot('gold/a'),(2,1,b'peer'))
        self.assertEqual(self.db.redeem('a','gold/a',b'approved'),'stale')

    def test_trigger_blocks_physical_delete_and_revision_regression(self):
        self.db.external_write('seo/a',b'original')
        con=sqlite3.connect(self.path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("DELETE FROM heads WHERE path='seo/a'")
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("UPDATE heads SET revision=revision-1 WHERE path='seo/a'")
            con.rollback()
        finally: con.close()
        self.assertEqual(self.db.snapshot('seo/a'),(1,1,b'original'))

    def test_seeded_reference_model_transfer(self):
        # Independent, pure-Python sequential model across two task domains.
        rng=random.Random(421)
        state={}; receipts={}; seq=0
        paths=[f'{d}/{i}' for d in ('seo','gold') for i in range(5)]
        for _ in range(1200):
            path=rng.choice(paths)
            action=rng.choices(('write','delete','issue','redeem'),(3,2,3,4))[0]
            rev,present,content=state.get(path,(0,0,None))
            if action=='write':
                payload=f'v{rng.randrange(1000)}'.encode()
                self.db.external_write(path,payload)
                state[path]=(rev+1,1,payload)
            elif action=='delete':
                self.db.external_delete(path)
                state[path]=(rev+1,0,None)
            elif action=='issue':
                seq+=1; rid=f'r{seq}'
                payload=f'approved-{seq}'.encode()
                self.assertEqual(self.db.issue(rid,path,payload),rev)
                receipts[rid]=[path,rev,payload,False]
            elif receipts:
                rid=rng.choice(tuple(receipts))
                target,expected,payload,consumed=receipts[rid]
                result=self.db.redeem(rid,target,payload)
                if consumed: expected_result='invalid_or_consumed'
                else:
                    receipts[rid][3]=True
                    target_rev=state.get(target,(0,0,None))[0]
                    if target_rev!=expected: expected_result='stale'
                    else:
                        expected_result='ok'
                        state[target]=(target_rev+1,1,payload)
                self.assertEqual(result,expected_result)
            for candidate in paths:
                self.assertEqual(self.db.snapshot(candidate),state.get(candidate,(0,0,None)))

    def test_naive_check_then_write_lost_update(self):
        self.db.external_write('seo/a',b'old')
        gate=threading.Barrier(2)
        seen=[]
        def naive(payload):
            rev=self.db.snapshot('seo/a')[0]
            gate.wait(timeout=3)
            # This deliberately ignores the previously checked revision.
            self.db.external_write('seo/a',payload)
            seen.append(rev)
        a=threading.Thread(target=naive,args=(b'A',)); b=threading.Thread(target=naive,args=(b'B',))
        a.start();b.start();a.join(5);b.join(5)
        self.assertEqual(seen,[1,1])
        self.assertEqual(self.db.snapshot('seo/a')[0],3)
        # Both naive workers accepted a write based on revision 1.

if __name__=='__main__':unittest.main()
