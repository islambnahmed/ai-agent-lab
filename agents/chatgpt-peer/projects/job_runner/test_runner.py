from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("runner.py")
s=importlib.util.spec_from_file_location("jr",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 r=m.JobRunner(Path(d)/"jobs.db")
 r.register("add",lambda a,b:a+b)
 tid=r.submit("add",{"a":2,"b":5})
 out=r.work_once(now=0)
 assert out["task_id"]==tid and out["result"]==7
 bad=r.submit("missing",{})
 out2=r.work_once(now=1)
 assert out2["status"]=="failed"
print("PASS")
