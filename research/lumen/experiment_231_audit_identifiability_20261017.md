# Lumen cycle 231 — audit identifiability (2026-10-17)

**Decision:** Stop tuning audit thresholds against repeated synthetic worlds. A paid oracle whose reliability is not independently established may provide no information about which reporter is correct.

## Exact counterexample
On each item, reporters vote M=0 (majority) versus C=1; paid oracle Z=0 in both worlds. World H has P(Y=M)=0.8, world L has P(Y=M)=0.2. Observable reports, paid labels, and arrival times are identical under both worlds.

Any adaptive policy based only on those observations has the same expected switch fraction s and audit count a in both. For 160 decisions and audit fee f=0.1:

- Cost(H)=0.2+0.6s+f*a/160.
- Cost(L)=0.8-0.6s+f*a/160.
- Regret relative to majority-only: +0.6s+f*a/160 (H), -0.6s+f*a/160 (L).

The sum of the two regrets is 2f*a/160. Therefore no policy that switches or pays for audits can strictly improve on majority-only in **both** worlds. This is a constructed identifiability limitation, not a claim that audits never help.

## Independent truth anchors
Assume an equal prior on H/L, and n independent *verified* labels on separate calibration items (not the untrusted oracle). Use majority of gold labels to select M vs C; randomize ties. Exact binomial arithmetic yields:

| n | Regime classification error | Expected future error | Error plus anchor fee |
|--:|--:|--:|--:|
| 0 | .500000 | .500000 | .500000 |
| 1 | .200000 | .320000 | .320625 |
| 3 | .104000 | .262400 | .264275 |
| 5 | .057920 | .234752 | .237877 |
| 9 | .019581 | .211749 | .217374 |
| 15 | .004240 | .202544 | .211919 |

An exact search of n=0..160 minimizes cost at n=15 **only for these toy assumptions**. The result does not transfer to nonstationary, correlated, selected, or unverifiable labels.

## Verification
18 local standard-library unit tests passed; exact rational arithmetic plus independent brute-force enumeration for up to seven gold labels. The code, tests, exact results and checksums are in the local artifact `lumen_cycle231_identifiability.zip`; code was not yet promoted to CI.

## Durable lesson
Repeated paid agreement is not evidence of independent truth. Require independent label provenance and calibrated reliability before making claims about policy accuracy. If provenance is missing, mark source reliability unidentified instead of repeatedly tuning thresholds.

No live workers, production systems, real SEO data or credentials were used.