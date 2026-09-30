from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"complementarity.py"
s=importlib.util.spec_from_file_location("c",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
a=[1,1,1,1,0,0,0,0]
duplicate=[1,1,1,1,0,0,0,0]
complement=[0,0,0,0,1,1,1,1]
assert m.run(a,duplicate)["complementarity_gain"]==0
assert m.run(a,complement)["complementarity_gain"]==0.5
# Oracle union is an upper bound unless a selector can know which method to trust per case.
assert m.run(a,complement)["oracle_union"]==1.0
print("PASS")
