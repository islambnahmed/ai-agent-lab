# Keystone: heterogeneous pairwise risk — averaging destroys critical information (2026-10-11)

## Result (exact, reproducible)

Let three binary failure indicators have marginals p=(ε,1/2,1/2) and pairwise intersections q12=q13=ε/2, q23=1/4. These moments are pairwise-independent but **do not imply mutual independence**.

For any three events with marginals a,b,c and pair intersections ab,ac,bc, the exact feasible range of t=P(111) is

- lower = max(0, ab+ac-a, ab+bc-b, ac+bc-c)
- upper = min(ab, ac, bc, 1-a-b-c+ab+ac+bc).

Every t in this interval is achievable: the eight atoms are t, ab-t, ac-t, bc-t, a-ab-ac+t, b-ab-bc+t, c-ac-bc+t, and 1-a-b-c+ab+ac+bc-t.

In the example, the exact upper is ε/2. Averaging p and q over labels yields p_bar=(1+ε)/3, q_bar=(1/4+ε)/3. Symmetrization shows the exchangeable bound computed from these averages is a **valid outer bound**, but as ε→0 its upper tends to 1/12, whereas the exact heterogeneous upper tends to 0. Hence the overestimate factor diverges: averaging can be arbitrarily misleading.

At ε=1/10000: exact upper = 1/20000 = 0.00005; averaged exchangeable upper = 10004/120000 ≈ 0.0833667; factor = 1667.333...

## Verification

Local reproducible Python artifact: heterogeneous_joint_bounds.py (Fraction exact triple formula + SciPy HiGHS 2^n-atom LP oracle for n≤10); test_heterogeneous_joint_bounds.py. 5 test methods passed (120 randomized analytic-versus-LP triple comparisons; 48 randomized n=4..7 feasible laws; explicit infeasible and malformed cases). All LP witnesses were checked against original marginals and every pairwise intersection. No claim of production readiness; floating-point LP may need stronger numerics near degeneracy.

## Operational lesson

Do not replace heterogeneous per-agent failure rates and pairwise intersections with two averages before issuing a sharp joint-failure estimate. Retain individual moments; use exact three-event formulas when applicable, or a full-atom LP for small n. Even pairwise independence is insufficient to justify a product of failure rates.

This is a mathematical benchmark, not an empirical estimate of any deployed AI agents.
