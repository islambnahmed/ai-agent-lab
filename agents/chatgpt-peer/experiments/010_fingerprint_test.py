from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"artifact_fingerprint.py"
s=importlib.util.spec_from_file_location("f",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

# Dict key order should not create fake drift.
a={"x":1,"y":[2,3]}; b={"y":[2,3],"x":1}
assert m.run(a)["sha256"]==m.run(b)["sha256"]

# Real content change must change the fingerprint.
c={"x":1,"y":[2,4]}
assert m.run(a)["sha256"]!=m.run(c)["sha256"]

# List order is semantic here and must change the fingerprint.
assert m.run([1,2])["sha256"]!=m.run([2,1])["sha256"]
print("PASS source-level assertions")
