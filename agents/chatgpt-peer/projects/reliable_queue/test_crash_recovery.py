from pathlib import Path
import tempfile, importlib.util
p=Path(__file__).with_name("queue.py")
s=importlib.util.spec_from_file_location("rq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
    q=m.Queue(Path(d)/"q.json")
    tid=q.add("work",max_attempts=3)
    first=q.claim(now=0,visibility_timeout=10)
    assert first["attempts"]==1
    assert q.claim(now=9) is None
    recovered=q.claim(now=10,visibility_timeout=10)
    assert recovered["id"]==tid and recovered["attempts"]==2
    assert recovered["lease_token"]!=first["lease_token"]
    q.complete(tid,recovered["lease_token"])
    assert q.claim(now=100) is None
print("PASS")
