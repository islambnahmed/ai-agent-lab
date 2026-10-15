"""Audit binary agent failures on identical, pre-registered tasks.

CSV: task_id,<agent1>,<agent2>,... with 1=failure, 0=success.
Tests and intervals assume independent identically distributed task rows.
They cannot prove independence or future reliability.
"""
import argparse
import csv
import json
import math
from itertools import combinations


def _logchoose(n, k):
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_two_sided(a, b, c, d):
    """Fisher exact two-sided p-value, probability-ordering definition."""
    if any(type(v) is not int or v < 0 for v in (a, b, c, d)):
        raise ValueError("contingency cells must be nonnegative integers")
    n = a + b + c + d
    if not n:
        raise ValueError("empty table")
    row, col = a + b, a + c
    low, high = max(0, row + col - n), min(row, col)
    denom = _logchoose(n, row)

    def logprob(x):
        return _logchoose(col, x) + _logchoose(n - col, row - x) - denom

    observed = logprob(a)
    eligible = [logprob(x) for x in range(low, high + 1)
                if logprob(x) <= observed + 1e-9]
    peak = max(eligible)
    return min(1.0, math.exp(peak) * sum(math.exp(v - peak) for v in eligible))


def wilson_interval(k, n, z=1.959963984540054):
    if type(k) is not int or type(n) is not int or n <= 0 or not 0 <= k <= n:
        raise ValueError("invalid count")
    p = k / n
    denom = 1 + z*z/n
    mid = (p + z*z/(2*n)) / denom
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return [max(0.0, mid-half), min(1.0, mid+half)]


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if not fields or len(fields) < 3 or fields[0] != "task_id" or len(set(fields)) != len(fields):
            raise ValueError("expected unique headers: task_id and >=2 agents")
        agents = fields[1:]
        if any(not a.strip() for a in agents):
            raise ValueError("agent names cannot be blank")
        ids, rows = set(), []
        for line, row in enumerate(reader, start=2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"malformed CSV row {line}")
            task_id = row["task_id"].strip()
            if not task_id or task_id in ids:
                raise ValueError(f"empty/duplicate task_id on row {line}")
            ids.add(task_id)
            if any(row[a] not in ("0", "1") for a in agents):
                raise ValueError(f"non-binary failure value on row {line}")
            rows.append(tuple(int(row[a]) for a in agents))
    if not rows:
        raise ValueError("at least one task is required")
    return agents, rows


def audit(agents, rows, alpha=0.05):
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    n, k = len(rows), len(agents)
    if n == 0 or k < 2 or len(set(agents)) != k or any(
        len(row) != k or any(type(v) is not int or v not in (0, 1) for v in row)
        for row in rows
    ):
        raise ValueError("invalid binary task matrix or agent names")
    failures = [sum(row[i] for row in rows) for i in range(k)]
    pairs = []
    for i, j in combinations(range(k), 2):
        a = sum(row[i] == 1 and row[j] == 1 for row in rows)
        b, c = failures[i] - a, failures[j] - a
        d = n - a - b - c
        pairs.append({
            "agents": [agents[i], agents[j]],
            "both_failed": a,
            "observed_joint_rate": a/n,
            "independence_joint_rate": failures[i]*failures[j]/(n*n),
            "fisher_two_sided_p": fisher_two_sided(a, b, c, d),
        })
    running = 0.0
    for rank, index in enumerate(sorted(range(len(pairs)), key=lambda t: pairs[t]["fisher_two_sided_p"])):
        running = max(running, (len(pairs)-rank)*pairs[index]["fisher_two_sided_p"])
        pairs[index]["holm_adjusted_p"] = min(1.0, running)
        pairs[index]["reject_pairwise_independence"] = running < alpha
    all_fail = sum(all(row) for row in rows)
    return {
        "task_count": n,
        "agent_failure_rates": dict(zip(agents, (count/n for count in failures))),
        "all_failed": {
            "count": all_fail,
            "observed_rate": all_fail/n,
            "wilson_95pct_interval_iid_tasks_only": wilson_interval(all_fail, n),
            "full_independence_plugin_rate_not_validated": math.prod(count/n for count in failures),
        },
        "pairs": pairs,
        "alpha_familywise": alpha,
        "warnings": [
            "A non-significant Fisher test does not establish pairwise independence.",
            "Even true pairwise independence does not imply mutual independence.",
            "Inference assumes IID representative tasks; no temporal or clustered-task correction.",
            "Observational audit only, not a prospective reliability guarantee.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()
    agents, rows = load_csv(args.csv_path)
    print(json.dumps(audit(agents, rows, args.alpha), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
