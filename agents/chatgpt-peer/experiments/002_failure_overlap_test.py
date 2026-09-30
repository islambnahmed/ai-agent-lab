from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"failure_overlap.py"
s=importlib.util.spec_from_file_location("fo",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

# Same marginal failure rate, radically different overlap.
a=[1,1,1,1,0,0,0,0]
same=[1,1,1,1,0,0,0,0]
split=[0,0,0,0,1,1,1,1]
r_same=m.run(a,same); r_split=m.run(a,split)
assert r_same["p_fail_a"]==r_split["p_fail_a"]==0.5
assert r_same["p_fail_b"]==r_split["p_fail_b"]==0.5
assert r_same["failure_lift"]==2.0 and r_same["phi"]==1.0
assert r_split["failure_lift"]==0.0 and r_split["phi"]==-1.0

# Counterexample: tiny histories can show extreme phi by accident.
tiny=m.run([1,1,0,0],[1,1,0,0])
assert tiny["phi"]==1.0
print("PASS: overlap exposes structure hidden by equal marginal error rates; small samples remain unreliable.")
