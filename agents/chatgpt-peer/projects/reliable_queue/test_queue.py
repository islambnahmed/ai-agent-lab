from pathlib import Path
import tempfile, importlib.util
p=Path(__file__).with_name("queue.py")
s=importlib.util.spec_from_file_location("rq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

with tempfile.TemporaryDirectory() as d:
    pth=Path(d)/"q.json"; q=m.Queue(pth)
    tid=q.add({"job":"alpha"},max_attempts=2)
    t=q.claim(now=10); assert t["id"]==tid and t["attempts"]==1
    q.fail(tid,t["lease_token"],"boom",retry_delay=5,now=10)
    assert q.claim(now=14) is None
    t=q.claim(now=15); assert t["attempts"]==2
    q.fail(tid,t["lease_token"],"boom again",now=15)
    assert q.snapshot()["tasks"][0]["status"]=="dead"
    q2=m.Queue(pth); assert q2.snapshot()["tasks"][0]["status"]=="dead"
    tid2=q2.add({"job":"beta"}); t2=q2.claim(now=20)
    q2.complete(tid2,t2["lease_token"])
    assert q2.snapshot()["tasks"][1]["status"]=="done"
print("PASS")
