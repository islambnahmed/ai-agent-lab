from pathlib import Path
import importlib.util
p=Path(__file__).parents[1]/"tools"/"failure_minimizer.py"
s=importlib.util.spec_from_file_location("fm",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

# Failure needs A+B; noise should disappear.
case=list("xAyBz")
fails=lambda xs: "A" in xs and "B" in xs
assert m.one_minimal(case,fails)==["A","B"]
assert m.ddmin(case,fails)==["A","B"]

# Local minimum need not be globally minimum.
# Failure if token Q exists OR all A,B,C exist.
case=["A","B","C","Q"]
fails2=lambda xs: ("Q" in xs) or all(t in xs for t in ["A","B","C"])
greedy=m.one_minimal(case,fails2)
# Depending on deletion order, greedy can get trapped at ABC although Q alone fails.
assert fails2(greedy)
assert len(greedy) in (1,3)
print("PASS source-level assertions")
