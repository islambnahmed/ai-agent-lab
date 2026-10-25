"""Deterministic two-file SQLite fault matrix; no external operations."""
import json
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp440"))
from durable_delivery import connect, enqueue, claim, Claim, digest, effect_count, pending_count
from verified_delivery import dispatch, ack_verified, Rejected


def run(per_family=200):
    with tempfile.TemporaryDirectory() as t:
        opath=os.path.join(t,'out.db'); spath=os.path.join(t,'sink.db')
        out=connect(opath); sink=connect(spath)
        applied=duplicates=blocked=0
        ops=[f'{family}:{i}' for family in ('seo','gold') for i in range(per_family)]
        for op in ops:
            enqueue(out,op,('action:'+op).encode())
        for idx,op in enumerate(ops):
            c=claim(out,'before-crash',0,10)
            assert c is not None
            assert dispatch(out,sink,c,0)=='applied'
            applied+=1
            # Crash after effect but before ACK; restart periodically.
            if idx % 50 == 49:
                out.close(); sink.close()
                out=connect(opath); sink=connect(spath)
            for fake in (Claim('unbacked:'+op,c.payload,c.digest,c.owner,c.generation),
                         Claim(c.op_id,b'wrong',digest(b'wrong'),c.owner,c.generation)):
                try: dispatch(out,sink,fake,0)
                except Rejected: blocked+=1
                else: raise AssertionError('unbacked or altered claim accepted')
        for op in ops:
            c=claim(out,'after-crash',10,10)
            assert c is not None
            assert dispatch(out,sink,c,10)=='duplicate'
            duplicates+=1
            assert ack_verified(out,sink,c,10)
        result={'per_family':per_family,'operations':len(ops),
                'applied_once':applied,'suppressed_retries':duplicates,
                'rejected_forged_dispatches':blocked,
                'effects':effect_count(sink),'pending':pending_count(out),
                'duplicate_effects':effect_count(sink)-len(ops),
                'distinct_db_files':os.path.abspath(opath)!=os.path.abspath(spath)}
        out.close(); sink.close()
        return result


if __name__=='__main__': print(json.dumps(run(),indent=2,sort_keys=True))
