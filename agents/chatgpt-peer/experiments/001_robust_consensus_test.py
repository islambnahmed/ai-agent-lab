from pathlib import Path
import importlib.util

p=Path(__file__).parents[1]/"tools"/"robust_consensus.py"
spec=importlib.util.spec_from_file_location("rc",p)
rc=importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)

# Clean data: center preserved.
r=rc.run([9.8,10.0,10.1,10.2,9.9])
assert r["estimate"]==10.0

# One catastrophic sensor/result: should not drag the estimate.
r=rc.run([10.0,10.1,9.9,10.2,1000.0])
assert r["estimate"]==10.05 and r["rejected"]==[1000.0]

# Majority exact agreement exposes MAD=0 edge case.
r=rc.run([5,5,5,5,100])
assert r["estimate"]==5.0 and r["rejected"]==[100.0]

# Counterexample: if the majority is wrong, robust consensus is confidently wrong.
r=rc.run([100,100,100,1,1])
assert r["estimate"]==100.0
print("PASS: useful against minority outliers; does NOT protect against correlated/majority failure.")
