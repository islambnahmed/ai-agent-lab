"""Worker A: exact cost baseline for finding one hidden witness among 2**d states.

Compares:
1) ordinary membership queries without replacement;
2) an ideal partition query (one bit: which half contains the witness).

The point is to count underlying environment evaluations, not only visible questions.
No external dependencies.
"""

def membership_expected(n: int) -> float:
    # Hidden witness uniformly distributed; random/permutation search without replacement.
    return (n + 1) / 2

def membership_success(n: int, budget: int) -> float:
    return min(budget, n) / n

def ideal_partition_questions(d: int) -> int:
    # Binary search if the environment supplies an exact partition bit directly.
    return d

def exhaustive_partition_eval_upper_bound(d: int) -> int:
    # If each partition answer is implemented by scanning candidate states naively,
    # the first scan can dominate; this conservative bound shows the hidden cost.
    return (1 << d) - 1

def rows(ds=(4, 6, 8, 10, 12)):
    out = []
    for d in ds:
        n = 1 << d
        budget = 4 * d
        out.append({
            "d": d,
            "states": n,
            "membership_expected_evals": membership_expected(n),
            "success_with_4d_evals": membership_success(n, budget),
            "ideal_partition_questions": ideal_partition_questions(d),
            "naive_partition_eval_upper_bound": exhaustive_partition_eval_upper_bound(d),
        })
    return out

if __name__ == "__main__":
    for r in rows():
        print(r)
