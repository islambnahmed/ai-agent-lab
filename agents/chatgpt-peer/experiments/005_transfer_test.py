from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"router_audit.py"
s=importlib.util.spec_from_file_location("a",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

# Stable mechanism: parity routing transfers.
dev=(list(range(8)),[x%2==0 for x in range(8)],[x%2==1 for x in range(8)])
tr=(list(range(8,16)),[x%2==0 for x in range(8,16)],[x%2==1 for x in range(8,16)])
assert m.run(dev,tr,lambda x:x%2==0)["transfer_accuracy"]==1.0

# Spurious mechanism: dev rule flips on transfer distribution.
dev2=([0,1,2,3],[1,1,0,0],[0,0,1,1])
tr2=([4,5,6,7],[0,0,1,1],[1,1,0,0])
r=m.run(dev2,tr2,lambda x:x<2 or (4<=x<6))
# Deliberately bad fixed feature rule on transfer.
r_bad=m.run(dev2,tr2,lambda x:x<2)
assert r_bad["development_accuracy"]==1.0 and r_bad["transfer_accuracy"]==0.5
print("PASS")
