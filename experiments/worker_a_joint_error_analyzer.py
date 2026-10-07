"""Analyze joint binary error vectors for a 3-auditor majority scheme.

Input is a text/CSV-like file containing one joint error vector per line.
Accepted vectors: 000..111. Lines may contain extra comma-separated fields;
the first field is used. Header/comment/blank lines are ignored.

Reports the directly observed majority-wrong rate and exact Clopper-Pearson
95% interval when scipy is available; otherwise reports the conservative
zero-failure one-sided 95% upper bound for k=0 and Wilson 95% interval.

This intentionally avoids inferring ensemble reliability from pairwise
correlations: majority failure is a higher-order event.
"""

from collections import Counter
from math import sqrt
import argparse

VALID = {f"{i:03b}" for i in range(8)}


def parse_vectors(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            token = line.split(",", 1)[0].strip()
            if token in VALID:
                out.append(token)
    if not out:
        raise ValueError("no valid joint vectors (000..111) found")
    return out


def wilson(k, n, z=1.959963984540054):
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * sqrt((p*(1-p)/n) + z*z/(4*n*n)) / den
    return max(0.0, center-half), min(1.0, center+half)


def interval(k, n, alpha=0.05):
    try:
        from scipy.stats import beta
        lo = 0.0 if k == 0 else beta.ppf(alpha/2, k, n-k+1)
        hi = 1.0 if k == n else beta.ppf(1-alpha/2, k+1, n-k)
        return lo, hi, "Clopper-Pearson 95%"
    except ImportError:
        if k == 0:
            # Exact one-sided upper confidence bound: P(0 failures|p)=alpha.
            return 0.0, 1 - alpha ** (1/n), "exact one-sided 95% upper bound"
        lo, hi = wilson(k, n)
        return lo, hi, "Wilson 95%"


def analyze(vectors):
    counts = Counter(vectors)
    n = len(vectors)
    majority = sum(c for v, c in counts.items() if v.count("1") >= 2)
    lo, hi, label = interval(majority, n)
    return counts, n, majority, majority/n, lo, hi, label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    counts, n, k, rate, lo, hi, label = analyze(parse_vectors(args.path))
    print(f"n={n}")
    print("joint_counts=" + " ".join(f"{v}:{counts[v]}" for v in sorted(VALID)))
    print(f"majority_wrong={k}/{n} ({rate:.6%})")
    print(f"{label}: [{lo:.6%}, {hi:.6%}]")
    if k == 0:
        print("note: zero observed majority failures does not imply zero risk")


if __name__ == "__main__":
    main()
