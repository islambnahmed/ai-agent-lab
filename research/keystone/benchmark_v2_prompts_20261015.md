# Keystone paired-agent benchmark v2 — prompt-only registration

Status: DESIGN ONLY. No agent attempts, scores, or statistical conclusions are recorded here.

**Registration contract:** Version `keystone-v2-20261015`, rubric `v2.0`, exactly 30 immutable tasks: 10 `coding-trace`, 10 `reasoning-schedule`, 10 `verification-modular`. All participants receive the same task IDs and exact prompts, independently, with no access to another worker's answer. No external packages. Do not read evaluator keys before submitting; the public prompts do not contain keys. Since the lab shares other materials, **blinding is not verified**.

**Outcome protocol:** Record each agent's task ID, rubric version, UTC submission time, original answer, and an authorized evidence link. An independent scorer must record pass/fail/unknown and link to evidence. Missing attempts, evidence, or incompatible versions remain `unknown` (never silently converted to pass/fail). Only analyze matched verified pass/fail rows, and report missingness separately; do not claim population reliability from these convenience-sampled tasks. Do not run the stratified independence audit without checking exchangeability and sampling assumptions.

**Coding-trace rubric:** Under Python 3.11+, report the exact single stdout line, including spaces, punctuation and list formatting. No explanation required; correctness requires exact match.

**Reasoning-schedule rubric:** Two identical workers, each runs at most one job at once; jobs indivisible, no preemption, all ready at time zero. Return the minimum integer makespan, one partition of the listed jobs between workers, and a valid optimality proof. Missing proof is a fail.

**Verification-modular rubric:** Each claim is only about integers `n` in the inclusive interval [-25,25]. State true or false. For true, give a convincing argument covering all 51 values (exhaustive reproducible code with correct range is accepted); for false, give one explicit counterexample in range with arithmetic. Bare true/false fails.

## C01 · coding-trace

```python
a = [1, 2]
b = a
b += [3]
print(a is b, a)
```

## C02 · coding-trace

```python
rows = [[1], [2]]
copy = rows[:]
copy[0].append(9)
print(rows, copy)
```

## C03 · coding-trace

```python
d = {True: "yes", 1: "one", 0: "zero"}
print(len(d), d[True], d[1])
```

## C04 · coding-trace

```python
fs = [lambda: i for i in range(3)]
print([f() for f in fs])
```

## C05 · coding-trace

```python
x = [0, 1, 2, 3, 4]
print(x[::-2], x[-2:0:-1])
```

## C06 · coding-trace

```python
def f(v, cache=[]):
    cache.append(v)
    return len(cache)
print(f(3), f(4), f(5, []), f(6))
```

## C07 · coding-trace

```python
x = {}
print(x.setdefault("a", []).append(1), x["a"])
```

## C08 · coding-trace

```python
it = iter([2, 4, 6])
print(sum(it), list(it))
```

## C09 · coding-trace

```python
def f():
    try:
        return "try"
    finally:
        return "finally"
print(f())
```

## C10 · coding-trace

```python
a = [1, 2, 3]
print([i * i for i in a if i % 2], "i" in globals())
```

## R01 · reasoning-schedule

Find the minimum makespan for jobs `[8,7,6,5,4,3]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R02 · reasoning-schedule

Find the minimum makespan for jobs `[9,8,7,6,5,4]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R03 · reasoning-schedule

Find the minimum makespan for jobs `[11,9,8,7,6,3]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R04 · reasoning-schedule

Find the minimum makespan for jobs `[13,12,11,7,5,2]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R05 · reasoning-schedule

Find the minimum makespan for jobs `[10,10,9,8,6,5]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R06 · reasoning-schedule

Find the minimum makespan for jobs `[17,13,12,9,5,4]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R07 · reasoning-schedule

Find the minimum makespan for jobs `[14,13,10,8,7,6]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R08 · reasoning-schedule

Find the minimum makespan for jobs `[19,16,11,10,9,7]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R09 · reasoning-schedule

Find the minimum makespan for jobs `[15,14,13,12,9,4]`. Give a valid assignment and a proof that no smaller makespan is possible.

## R10 · reasoning-schedule

Find the minimum makespan for jobs `[20,18,15,11,9,8]`. Give a valid assignment and a proof that no smaller makespan is possible.

## V01 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **n² ≡ n (mod 2)**. Justify your conclusion according to the rubric.

## V02 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **n² ≡ n (mod 3)**. Justify your conclusion according to the rubric.

## V03 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if 6 divides n, then 24 divides n²**. Justify your conclusion according to the rubric.

## V04 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if 4 divides n², then 2 divides n**. Justify your conclusion according to the rubric.

## V05 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if 8 divides n², then 8 divides n**. Justify your conclusion according to the rubric.

## V06 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if 4 divides n², then 8 divides n²**. Justify your conclusion according to the rubric.

## V07 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if n is odd, then n² ≡ 1 (mod 8)**. Justify your conclusion according to the rubric.

## V08 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if 3 divides n², then 9 divides n**. Justify your conclusion according to the rubric.

## V09 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **if 5 divides n, then 25 divides n²**. Justify your conclusion according to the rubric.

## V10 · verification-modular

Evaluate the claim for every integer `n` in `[-25,25]`: **n³ ≡ n (mod 6)**. Justify your conclusion according to the rubric.

