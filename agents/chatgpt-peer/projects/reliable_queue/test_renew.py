from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("sqlite_queue.py")
s=importlib.util.spec_from_file_location("sq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 q=m.SQLiteQueue(Path(d)/"q.db"); tid=q.add("long")
 t=q.claim(now=0,visibility_timeout=5)
 assert q.renew(tid,t["lease_token"],visibility_timeout=5,now=4)==9
 assert q.claim(now=6) is None
 q.complete(tid,t["lease_token"],now=8)
print("PASS")
