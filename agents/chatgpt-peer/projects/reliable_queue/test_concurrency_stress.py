from pathlib import Path
import tempfile,importlib.util,multiprocessing as mp

p=Path(__file__).with_name("sqlite_queue.py")
s=importlib.util.spec_from_file_location("sq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def worker(db_path,out):
    q=m.SQLiteQueue(db_path)
    claimed=[]
    while True:
        t=q.claim(visibility_timeout=30)
        if t is None:break
        claimed.append(t["id"])
        q.complete(t["id"],t["lease_token"])
    out.put(claimed)

if __name__=="__main__":
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/"q.db"; q=m.SQLiteQueue(db)
        ids={q.add({"n":i}) for i in range(200)}
        out=mp.Queue(); ps=[mp.Process(target=worker,args=(db,out)) for _ in range(8)]
        for x in ps:x.start()
        for x in ps:x.join(20)
        assert all(not x.is_alive() and x.exitcode==0 for x in ps)
        claims=[]
        for _ in ps:claims.extend(out.get(timeout=2))
        assert len(claims)==200
        assert len(set(claims))==200
        assert set(claims)==ids
        assert all(t["status"]=="done" for t in q.snapshot())
    print("PASS")
