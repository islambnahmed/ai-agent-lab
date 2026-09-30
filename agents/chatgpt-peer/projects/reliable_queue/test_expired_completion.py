from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("sqlite_queue.py")
s=importlib.util.spec_from_file_location("sq",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 q=m.SQLiteQueue(Path(d)/"q.db"); tid=q.add("slow")
 t=q.claim(now=0,visibility_timeout=5)
 try:
  q.complete(tid,t["lease_token"],now=6)
  raise AssertionError("expired lease completed without recovery claim")
 except ValueError as e:
  assert "expired" in str(e)
 # A later claim performs recovery and gets a fresh token.
 t2=q.claim(now=6,visibility_timeout=5)
 assert t2["id"]==tid and t2["lease_token"]!=t["lease_token"]
 q.complete(tid,t2["lease_token"],now=7)
print("PASS")
