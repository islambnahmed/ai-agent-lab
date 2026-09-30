from pathlib import Path
import tempfile, importlib.util
p=Path(__file__).with_name("queue.py")
s=importlib.util.spec_from_file_location("rq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

with tempfile.TemporaryDirectory() as d:
    q=m.Queue(Path(d)/"q.json")
    tid=q.add({"job":"charge"},max_attempts=3)
    old=q.claim(now=0,visibility_timeout=5)
    new=q.claim(now=5,visibility_timeout=5)
    assert old["id"]==new["id"] and old["lease_token"]!=new["lease_token"]

    try:
        q.complete(tid,old["lease_token"])
        raise AssertionError("stale worker was allowed to complete")
    except ValueError as e:
        assert "stale" in str(e)

    q.renew(tid,new["lease_token"],visibility_timeout=10,now=6)
    assert q.claim(now=10) is None
    q.complete(tid,new["lease_token"])
    assert q.snapshot()["tasks"][0]["status"]=="done"
print("PASS")
