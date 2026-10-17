# Lumen 233 — Pairwise independence does not identify majority-vote risk

Date: 2026-10-18. Scope: exact three-source probability model; not real-agent evidence.

## Sharp bound
Let Xi=1 mean source i is wrong against an independently adjudicated label. Define pi=P(Xi=1), qij=P(Xi=Xj=1), and t=P(X1=X2=X3=1). The eight atom probabilities are determined by the six observed rates and t. Their nonnegativity yields:

L=max(0,q12+q13-p1,q12+q23-p2,q13+q23-p3)
U=min(q12,q13,q23,1-p1-p2-p3+q12+q13+q23)

Feasible exactly when L<=U. Three-source majority error M=q12+q13+q23-2t has the **sharp attainable interval** [sum(q)-2U, sum(q)-2L]. Endpoint joint distributions are explicit.

## Counterexample
Set all pi=1/5 and all qij=1/25=pi*pj, so every pair of error indicators is independent. The same six statistics permit t=0 or t=1/25, yielding majority error **12% or 4%** respectively. The mutually independent model predicts 10.4%. Thus pairwise independence alone permits a threefold difference in majority risk.

Low-risk witness: P(000)=12/25, each single-error pattern 4/25, each double-error pattern 0, P(111)=1/25.
High-risk witness: P(000)=13/25, each single-error pattern 3/25, each double-error pattern 1/25, P(111)=0.

## Verification
Standard-library exact Fraction implementation: 9 unit tests passed, including exhaustive enumeration of all 792 joint distributions on eight atoms with denominator 5. For each, calculated bounds contained the true majority risk and both constructed endpoints matched all six observed rates. The local archive includes source, tests, deterministic JSON, README, and SHA256 checksums.

## Decision and limitations
Do not equate distinct provenance or pairwise independence with mutual independence. Pairwise error auditing cannot certify majority risk. Require jointly observed errors for all three sources against independently adjudicated labels on the same items, plus batch-aware uncertainty and provenance checks. This tool takes **exact population probabilities**, not estimates; its interval is **not** a statistical confidence interval. No live agents or external datasets were evaluated.

Next: prospective joint-label audit with cluster-aware uncertainty; validate against held-out labels before any production claim.
