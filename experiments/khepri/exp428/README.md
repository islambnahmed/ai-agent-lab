# Khepri exp428 — correlated-witness provenance-domain quorum

Date: 2026-10-24. Research-only synthetic experiment in the authorized AI Agent Lab. Extends exp427's independent-witness quorum. Standard-library Python, no credentials or external systems.

## Question

Does counting witness identities as independent votes remain robust when several witnesses depend on the same upstream measurement pipeline? Counterexample: three receipts from upstream X, one from Y, one from Z. If X is corrupted, a 3-of-5 **witness** quorum accepts fabricated observations despite only one independent source being compromised.

## Tested alternative

Precommit a witness-to-upstream-domain map. Give each declared domain **at most one vote** per candidate/opportunity; if members of a domain disagree, that domain abstains. Require a strict majority of *domains* to report identical raw measurement pairs for every candidate/opportunity. No majority => fail closed. The pre-outcome policy hash binds the domain map and quorum threshold. Scoring and sequential evaluation reuse exp427/exp426 unchanged.

This protects against one *declared* corrupt domain out of three, even if that domain controls most witnesses. It is not a method to authenticate domain labels or discover hidden shared dependencies.

## Evidence

`python -m unittest -v test_provenance_gate.py`: **13/13 pass**, including 27 exhaustive one-slot domain vote configurations, malformed inputs, policy tampering, true-improvement preservation, finance two-candidate transfer, and two counterexamples.

`python benchmark.py > results.json`: **2 domains × 200 seeded trials × 5 conditions = 2,000 condition-trials**; SEO has 80 opportunities/1 candidate, finance has 60 opportunities/2 candidates. Honest streams contain shuffled balanced positive/negative pairs. This is a *deterministic adversarial stress test*, **not** an estimate of population false-positive rates.

| Condition | SEO old/new positive crossings | Finance old/new positive crossings | New rejected trials per domain |
| --- | --- | --- | --- |
| All witnesses honest | 3 / 3 | 0 / 0 | 0 |
| One upstream domain X corrupted (3/5 witnesses) | **200 / 3** | **200 / 0** | 0 |
| Two upstream domains X and Y corrupted | **200 / 200** | **200 / 200** | 0 |
| Corrupt X, honest Z missing | **200 / 0** | **200 / 0** | **200** |
| X falsely declared as 3 separate domains *before* policy commitment | **200 / 200** | **200 / 200** | 0 |

The three SEO crossings in the honest and one-corrupt-domain scenarios are identical: the new guard correctly recovers the honest data stream but **does not** eliminate sequential statistical false crossings. This prevents claiming zero false positives from the experiment.

## Counterexamples, trust boundary, and operational trade-off

- If two out of three upstream domains collude, the strict-majority domain rule accepts fabricated results. A quorum is not a proof of truth.
- If the policy authority mistakenly certifies three shared X witnesses as independent X1/X2/X3, the new guard also accepts fabricated results. Hashing a false provenance map only commits to the false map; independent provenance auditing is still needed.
- When one honest domain is unavailable and another is corrupted, the system fails closed (200/200 rejections in each domain); availability suffers.
- If every nominally separate domain shares an unrecorded faulty measurement vendor, the domain map cannot reveal the common-mode fault.
- All witnesses and provenance identifiers are externally authenticated **assumptions**, not implemented features. The code never signs or authenticates receipts. Statistical conditional-null assumptions also remain external.

## Reproduction

Run from this directory with Python 3.10+:

```bash
python -m unittest -v test_provenance_gate.py
python benchmark.py > results.json
```

`quorum_gate.py` and `baseline_manifest_gate.py` are unchanged copies from exp427, included so the experiment is standalone. No network calls or third-party packages.

## Transferable lesson

Witness count is not an independence guarantee. Model failure domains explicitly, require independent-domain votes, and **audit the independence claim itself**; otherwise duplicate or correlated witnesses create false confidence. This is a local research prototype, not a production authentication system.
