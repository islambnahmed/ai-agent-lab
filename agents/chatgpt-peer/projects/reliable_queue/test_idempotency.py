from pathlib import Path
import tempfile,importlib.util
p=Path(__file__).with_name("idempotency.py")
s=importlib.util.spec_from_file_location("i",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
    calls=[]
    j=m.EffectJournal(Path(d)/"effects.json")
    r,fresh=j.execute_once("order:42",lambda:(calls.append("charged") or {"ok":1}))
    assert fresh and calls==["charged"]
    r2,fresh2=j.execute_once("order:42",lambda:(calls.append("charged-again") or {"ok":2}))
    assert not fresh2 and r2==r and calls==["charged"]
    j2=m.EffectJournal(Path(d)/"effects.json")
    r3,fresh3=j2.execute_once("order:42",lambda:None)
    assert not fresh3 and r3==r
print("PASS")
