from pathlib import Path
import importlib.util,json
p=Path(__file__).parents[1]/"tools"/"roundtrip_probe.py"
s=importlib.util.spec_from_file_location("r",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

v={"name":"ناريمان","items":[1,2,3],"active":True}
r=m.run(v,lambda x:json.dumps(x,ensure_ascii=False),json.loads)
assert r["preserved"]

# Lossy transform: drops active field.
r2=m.run(v,lambda x:json.dumps({"name":x["name"],"items":x["items"]},ensure_ascii=False),json.loads)
assert not r2["preserved"]
print("PASS source-level assertions")
