from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("sqlite_queue.py")
s=importlib.util.spec_from_file_location("sq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 q=m.SQLiteQueue(Path(d)/"q.db")
 a=q.add("email",dedupe_key="email:42",available_at=50)
 b=q.add("duplicate",dedupe_key="email:42",available_at=0)
 assert a==b and q.claim(now=49) is None
 t=q.claim(now=50); assert t["payload"]=="email"
 q.fail(t["id"],t["lease_token"],"x",now=50)
 t=q.claim(now=50); q.fail(t["id"],t["lease_token"],"x",now=50)
 t=q.claim(now=50); q.fail(t["id"],t["lease_token"],"x",now=50)
 assert q.snapshot()[0]["status"]=="dead"
 assert q.requeue_dead(a,available_at=60)
 assert q.claim(now=59) is None
 assert q.claim(now=60)["id"]==a
 c=q.add("cancel me")
 assert q.cancel(c)
 assert not q.cancel(c)
print("PASS")
