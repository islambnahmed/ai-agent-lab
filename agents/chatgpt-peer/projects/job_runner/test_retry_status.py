from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("runner.py")
s=importlib.util.spec_from_file_location("jr",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 r=m.JobRunner(Path(d)/"j.db"); calls={"n":0}
 def flaky():
  calls["n"]+=1
  if calls["n"]<2: raise RuntimeError("temporary")
  return "ok"
 r.register("flaky",flaky)
 tid=r.submit("flaky",max_attempts=2)
 r.work_once(now=0)
 x=r.result(tid); assert x["status"]=="retrying" and x["queue_status"]=="pending"
 r.work_once(now=1)
 x=r.result(tid); assert x["status"]=="done" and x["result"]=="ok" and x["attempts"]==2
 tid2=r.submit("never",max_attempts=1)
 r.work_once(now=2)
 y=r.result(tid2); assert y["status"]=="dead" and y["queue_status"]=="dead"
print("PASS")
