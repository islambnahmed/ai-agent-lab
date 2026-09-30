from pathlib import Path
import tempfile,importlib.util

def load(name):
 p=Path(__file__).with_name(name+".py");s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
qmod=load("queue"); imod=load("idempotency"); w=load("worker")
with tempfile.TemporaryDirectory() as d:
 q=qmod.Queue(Path(d)/"q.json"); j=imod.EffectJournal(Path(d)/"e.json"); calls=[]
 tid=q.add({"x":3})
 out=w.process_one(q,j,lambda payload,key:(calls.append((payload,key)) or payload["x"]*2),now=0)
 assert out["result"]==6 and len(calls)==1
 assert q.snapshot()["tasks"][0]["status"]=="done"
print("PASS")
