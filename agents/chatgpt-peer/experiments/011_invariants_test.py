from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"invariant_guard.py"
s=importlib.util.spec_from_file_location("g",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

checks=[
 ("nonnegative_total",lambda x:x["total"]>=0),
 ("parts_match_total",lambda x:sum(x["parts"])==x["total"]),
]
assert m.run({"parts":[2,3],"total":5},checks)["ok"]
bad=m.run({"parts":[2,3],"total":6},checks)
assert not bad["ok"] and bad["checks"][1]["name"]=="parts_match_total"

# Counterexample: internally consistent but semantically wrong data passes.
wrong_but_consistent={"parts":[200,300],"total":500}
assert m.run(wrong_but_consistent,checks)["ok"]
print("PASS source-level assertions")
