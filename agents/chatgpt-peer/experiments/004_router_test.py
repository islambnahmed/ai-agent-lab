from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"selective_router.py"
s=importlib.util.spec_from_file_location("r",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
# Feature is available before outcome: A handles even class, B odd class.
x=list(range(8))
a=[v%2==0 for v in x]; b=[v%2==1 for v in x]
r=m.run(x,a,b,lambda v:v%2==0)
assert r["accuracy"]==1.0
# Wrong router proves complementarity alone is insufficient.
r2=m.run(x,a,b,lambda v:v%2==1)
assert r2["accuracy"]==0.0
print("PASS")
