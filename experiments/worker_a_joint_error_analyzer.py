"""Analyze joint binary error vectors for a 3-auditor majority scheme.

Input is a text/CSV-like file containing one joint error vector per line.
Accepted vectors: 000..111. Lines may contain extra comma-separated fields;
the first field is used. Header/comment/blank lines are ignored.

Reports the observed majority-wrong rate plus two deliberately distinct
uncertainty summaries:
1) a two-sided 95% interval for estimation; and
2) an exact one-sided 95% upper confidence bound for reliability claims.

The reliability upper bound is computed analytically for zero failures, so
the claim does not change merely because scipy is or is not installed.

This intentionally avoids inferring ensemble reliability from pairwise
correlations: majority failure is a higher-order event.
"""

from collections import Counter
from math import sqrt
import argparse

VALID = {f"{i:03b}" for i in range(8)}
HEADER_TOKENS = {"vector", "joint_vector", "error_vector", "joint_error_vector"}
Z95 = 1.959963984540054


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
                continue
            # Reliability analysis must fail closed: silently dropping a
            # malformed row can make the observed failure rate look safer.
            # Only explicit comments/blanks and a small set of documented
            # header names are ignorable.
            if token.lower() in HEADER_TOKENS:
                continue
            raise ValueError(f"invalid joint vector {token!r}: expected 000..111")
    if not out:
        raise ValueError("no valid joint vectors (000..111) found")
    return out


def wilson(k, n, z=Z95):
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * sqrt((p*(1-p)/n) + z*z/(4*n*n)) / den
    return max(0.0, center-half), min(1.0, center+half)


def two_sided_interval(k, n, alpha=0.05):
    """95% estimation interval; exact CP when scipy exists, Wilson otherwise."""
    try:
        from scipy.stats import beta
        lo = 0.0 if k == 0 else beta.ppf(alpha/2, k, n-k+1)
        hi = 1.0 if k == n else beta.ppf(1-alpha/2, k+1, n-k)
        return lo, hi, "Clopper-Pearson two-sided 95%"
    except ImportError:
        lo, hi = wilson(k, n)
        return lo, hi, "Wilson two-sided 95% (scipy unavailable)"


def reliability_upper_bound(k, n, alpha=0.05):
    """Exact one-sided 95% upper bound for k=0; CP upper bound otherwise."""
    if k == 0:
        # P(K=0 | p)=alpha -> p_upper=1-alpha**(1/n).
        return 1 - alpha ** (1/n), "exact one-sided 95% upper bound"
    try:
        from scipy.stats import beta
        hi = 1.0 if k == n else beta.ppf(1-alpha, k+1, n-k)
        return hi, "Clopper-Pearson one-sided 95% upper bound"
    except ImportError:
        # Without scipy, do not silently substitute a different reliability
        # claim. Wilson remains an estimation interval, not an exact CP bound.
        return None, "exact nonzero-failure upper bound requires scipy"


def analyze(vectors):
    counts = Counter(vectors)
    n = len(vectors)
    majority = sum(c for v, c in counts.items() if v.count("1") >= 2)
    lo, hi, interval_label = two_sided_interval(majority, n)
    upper, upper_label = reliability_upper_bound(majority, n)
    return counts, n, majority, majority/n, lo, hi, interval_label, upper, upper_label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    counts, n, k, rate, lo, hi, ilabel, upper, ulabel = analyze(parse_vectors(args.path))
    print(f"n={n}")
    print("joint_counts=" + " ".join(f"{v}:{counts[v]}" for v in sorted(VALID)))
    print(f"majority_wrong={k}/{n} ({rate:.6%})")
    print(f"estimation_interval ({ilabel}): [{lo:.6%}, {hi:.6%}]")
    if upper is None:
        print(f"reliability_upper_bound: unavailable ({ulabel})")
    else:
        print(f"reliability_upper_bound ({ulabel}): {upper:.6%}")
    if k == 0:
        print("note: zero observed majority failures does not imply zero risk")


if __name__ == "__main__":
    main()
