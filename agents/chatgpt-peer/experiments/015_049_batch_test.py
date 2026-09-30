from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"decision_primitives.py"
s=importlib.util.spec_from_file_location("d",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert m.robust_scale([1,1,1,100])["median"]==1
assert abs(m.bounded_retry(8,10)-0.75)<1e-12
v=m.value_of_information([[10,0],[0,10]],1)
assert v["current"]==5 and v["perfect_info"]==10 and v["upper_bound_net_gain"]==4
assert m.regret(7,10)==3
assert m.saturation([1,.1,0,0,0])
print("PASS source-level assertions")
