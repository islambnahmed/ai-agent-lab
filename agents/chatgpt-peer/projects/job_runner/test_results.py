from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("runner.py")
s=importlib.util.spec_from_file_location("jr",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 db=Path(d)/"jobs.db"; r=m.JobRunner(db)
 r.register("mul",lambda a,b:a*b)
 tid=r.submit("mul",{"a":6,"b":7})
 assert r.result(tid)["status"]=="queued"
 r.work_once(now=10)
 assert r.result(tid)["status"]=="done" and r.result(tid)["result"]==42
 # Outcome survives process/object restart.
 r2=m.JobRunner(db)
 assert r2.result(tid)["result"]==42
print("PASS")
