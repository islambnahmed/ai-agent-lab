from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("sqlite_queue.py")
s=importlib.util.spec_from_file_location("sq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 pth=Path(d)/"q.db"; q1=m.SQLiteQueue(pth); q2=m.SQLiteQueue(pth)
 ids=[q1.add({"n":i}) for i in range(2)]
 a=q1.claim(now=0,visibility_timeout=10); b=q2.claim(now=0,visibility_timeout=10)
 assert a["id"]!=b["id"]
 q1.complete(a["id"],a["lease_token"]); q2.complete(b["id"],b["lease_token"])
 assert [x["status"] for x in q1.snapshot()]==["done","done"]
print("PASS")
