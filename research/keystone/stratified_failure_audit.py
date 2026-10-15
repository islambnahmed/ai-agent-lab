"""Exact conditional-independence audit of binary agent failures by task stratum.

CSV columns: task_id,stratum,<agent>,<agent>,... ; 1=failed, 0=succeeded.
Strata must be pre-registered, not chosen after inspecting outcomes.
Within each stratum, the conditional null assumes exchangeable task rows.
"""
import argparse
import csv
import json
from collections import defaultdict
from fractions import Fraction
from itertools import combinations
from math import comb


def read_tasks(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        names = reader.fieldnames
        if not names or len(names) < 4 or names[:2] != ["task_id", "stratum"] or len(set(names)) != len(names):
            raise ValueError("expected unique task_id,stratum,>=2 agent columns")
        agents = names[2:]
        if any(not name.strip() or name != name.strip() for name in agents):
            raise ValueError("agent names must be nonempty and trimmed")
        seen = set()
        groups = defaultdict(list)
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"malformed row {line}")
            task, stratum = row["task_id"].strip(), row["stratum"].strip()
            if not task or task in seen or not stratum:
                raise ValueError(f"empty/duplicate task ID or empty stratum at row {line}")
            if any(row[name] not in ("0", "1") for name in agents):
                raise ValueError(f"non-binary outcome at row {line}")
            seen.add(task)
            groups[stratum].append(tuple(int(row[name]) for name in agents))
    if not seen:
        raise ValueError("no tasks")
    return agents, dict(groups)


def exact_conditional_p(tables):
    """Probability-ordered exact two-sided p for total joint failures.

    Each (a,b,c,d) table is conditioned on its row/column margins.
    Returns Fraction, expected joint count as Fraction, and per-stratum deltas.
    """
    distribution = {0: Fraction(1)}
    observed = 0
    expected = Fraction(0)
    deltas = []
    for a, b, c, d in tables:
        if any(type(v) is not int or v < 0 for v in (a, b, c, d)):
            raise ValueError("cells must be nonnegative integers")
        n = a + b + c + d
        if not n:
            raise ValueError("empty stratum")
        row, col = a + b, a + c
        lo, hi = max(0, row + col - n), min(row, col)
        denom = comb(n, row)
        probs = {x: Fraction(comb(col, x) * comb(n - col, row - x), denom)
                 for x in range(lo, hi + 1)}
        next_distribution = defaultdict(Fraction)
        for total, p0 in distribution.items():
            for x, p1 in probs.items():
                next_distribution[total + x] += p0 * p1
        distribution = dict(next_distribution)
        observed += a
        e = Fraction(row * col, n)
        expected += e
        deltas.append(Fraction(a) - e)
    p_observed = distribution[observed]
    p_value = sum((p for p in distribution.values() if p <= p_observed), Fraction(0))
    assert sum(distribution.values()) == 1
    return p_value, expected, deltas


def audit(agents, groups, alpha=Fraction(1, 20)):
    alpha = Fraction(str(alpha))
    if not 0 < alpha < 1 or len(agents) < 2 or len(set(agents)) != len(agents):
        raise ValueError("invalid agents or alpha")
    if not groups or any(not rows for rows in groups.values()):
        raise ValueError("empty strata")
    width = len(agents)
    if any(len(row) != width or any(type(v) is not int or v not in (0, 1) for v in row)
           for rows in groups.values() for row in rows):
        raise ValueError("invalid outcome matrix")
    results = []
    for i, j in combinations(range(width), 2):
        tables = []
        for rows in groups.values():
            a = sum(row[i] == 1 and row[j] == 1 for row in rows)
            b = sum(row[i] == 1 and row[j] == 0 for row in rows)
            c = sum(row[i] == 0 and row[j] == 1 for row in rows)
            d = len(rows) - a - b - c
            tables.append((a, b, c, d))
        p, expected, deltas = exact_conditional_p(tables)
        # A pooled statistic can cancel when dependence reverses between strata.
        # Test each pre-registered stratum as a separate exact hypothesis,
        # Bonferroni-adjust within a pair, then Holm-adjust across pairs.
        # This controls family-wise false positives without requiring the
        # stratum-specific tests to be independent.
        stratum_results = []
        for name, table in zip(groups, tables):
            single_p, single_expected, _ = exact_conditional_p([table])
            stratum_results.append({
                "stratum": name,
                "observed_joint_failures": table[0],
                "null_expected_joint_failures": float(single_expected),
                "exact_fisher_two_sided_p": float(single_p),
                "direction": "positive" if table[0] > single_expected else
                             "negative" if table[0] < single_expected else "zero",
                "_p": single_p,
            })
        any_stratum_p = min(Fraction(1), len(tables) * min(x["_p"] for x in stratum_results))
        for item in stratum_results:
            del item["_p"]
        results.append({"agents": [agents[i], agents[j]],
                        "observed_joint_failures": sum(t[0] for t in tables),
                        "null_expected_joint_failures": float(expected),
                        "exact_conditional_p": float(p),
                        "any_stratum_bonferroni_p": float(any_stratum_p),
                        "stratum_tests": stratum_results,
                        "stratum_deltas": [float(d) for d in deltas],
                        "opposite_stratum_directions": any(d > 0 for d in deltas) and any(d < 0 for d in deltas),
                        "_p": p, "_any_p": any_stratum_p})
    adjusted = Fraction(0)
    for rank, idx in enumerate(sorted(range(len(results)), key=lambda t: results[t]["_p"])):
        adjusted = max(adjusted, (len(results) - rank) * results[idx]["_p"])
        results[idx]["holm_adjusted_p"] = float(min(Fraction(1), adjusted))
        results[idx]["reject_conditional_independence"] = adjusted < alpha
    adjusted_any = Fraction(0)
    for rank, idx in enumerate(sorted(range(len(results)), key=lambda t: results[t]["_any_p"])):
        adjusted_any = max(adjusted_any, (len(results) - rank) * results[idx]["_any_p"])
        results[idx]["holm_adjusted_any_stratum_p"] = float(min(Fraction(1), adjusted_any))
        results[idx]["reject_any_stratum_independence"] = adjusted_any < alpha
    for result in results:
        del result["_p"]
        del result["_any_p"]
    return {"task_count": sum(map(len, groups.values())),
            "stratum_sizes": {key: len(rows) for key, rows in groups.items()},
            "pairs": results,
            "warnings": [
                "Pre-register strata; outcome-dependent grouping invalidates p-values.",
                "Null requires exchangeability of rows within each stratum, conditional on margins.",
                "Pooled exact test can miss opposite-direction dependence across strata; inspect any-stratum test.",
                "Any-stratum test uses Bonferroni over pre-registered strata and Holm over agent pairs; it may be conservative.",
                "Non-rejection does not prove independence or future reliability.",
                "Task clustering, selection bias, and time drift are not handled."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()
    agents, groups = read_tasks(args.csv_path)
    print(json.dumps(audit(agents, groups, args.alpha), indent=2))


if __name__ == "__main__":
    main()
