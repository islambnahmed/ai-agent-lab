from pathlib import Path
import tempfile
from queue import Queue

with tempfile.TemporaryDirectory() as d:
    p=Path(d)/"q.json"
    q=Queue(p)
    tid=q.add({"job":"alpha"},max_attempts=2)
    t=q.claim(now=10); assert t["id"]==tid and t["attempts"]==1
    q.fail(tid,"boom",retry_delay=5,now=10)
    assert q.claim(now=14) is None
    t=q.claim(now=15); assert t["attempts"]==2
    q.fail(tid,"boom again",now=15)
    assert q.snapshot()["tasks"][0]["status"]=="dead"

    # Persistence across a new Queue instance.
    q2=Queue(p)
    assert q2.snapshot()["tasks"][0]["status"]=="dead"

    tid2=q2.add({"job":"beta"})
    t2=q2.claim(now=20); q2.complete(tid2)
    assert q2.snapshot()["tasks"][1]["status"]=="done"
print("PASS")
