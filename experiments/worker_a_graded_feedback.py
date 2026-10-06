"""Worker A: cheap graded feedback can turn exponential blind search into linear recovery.

Environment:
- hidden d-bit target
- one evaluation accepts a candidate and returns its Hamming similarity score (0..d)

Learner:
1) evaluate all-zero baseline;
2) flip each bit individually and evaluate again;
3) score delta reveals that hidden bit exactly.

Total environment evaluations: d + 1.  No ideal existential/partition oracle is used.
The environment does reveal log2(d+1) bits per score, so this is a structured-feedback
result, not a claim that arbitrary black-box search becomes easy.
"""

def score(candidate: int, target: int, d: int) -> int:
    mask = (1 << d) - 1
    return d - ((candidate ^ target) & mask).bit_count()

def recover(target: int, d: int):
    baseline = score(0, target, d)
    recovered = 0
    evaluations = 1
    for i in range(d):
        s = score(1 << i, target, d)
        evaluations += 1
        # Flipping bit i improves score iff target bit i is 1.
        if s > baseline:
            recovered |= 1 << i
    return recovered, evaluations

def exhaustive_check(max_d: int = 12):
    rows = []
    for d in range(1, max_d + 1):
        failures = 0
        max_evals = 0
        for target in range(1 << d):
            got, evals = recover(target, d)
            failures += got != target
            max_evals = max(max_evals, evals)
        rows.append({
            "d": d,
            "targets": 1 << d,
            "failures": failures,
            "evals_per_target": max_evals,
            "blind_expected_evals": ((1 << d) + 1) / 2,
        })
    return rows

if __name__ == "__main__":
    for row in exhaustive_check():
        print(row)
