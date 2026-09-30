from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("runner.py")
s=importlib.util.spec_from_file_location("jr",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 db=Path(d)/"j.db"; r1=m.JobRunner(db); r2=m.JobRunner(db)
 tid=r1.submit("slow")
 old=r1.queue.claim(now=0,visibility_timeout=1)
 new=r2.queue.claim(now=1,visibility_timeout=10)
 assert old["lease_token"]!=new["lease_token"]
 try:
  r1.queue.complete(tid,old["lease_token"])
  raise AssertionError("stale completion accepted")
 except ValueError:
  pass
 # New claim remains intact after stale rejection.
 row=[x for x in r2.queue.snapshot() if x["id"]==tid][0]
 assert row["status"]=="running" and row["lease_token"]==new["lease_token"]
print("PASS")
