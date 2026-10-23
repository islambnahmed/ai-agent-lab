# Khepri experiment 393 — false corroboration from shared upstreams

## Question
Can two agreeing price feeds be treated as independent evidence if they are mirrors of the same upstream provider? Does upstream de-duplication alone improve safety?

Reviewed `products/gold-forecast/data.mjs`: its crossCheck function already warns that agreement between indicative spot feeds does not prove historical accuracy or upstream independence. This experiment does **not** establish a bug in the production pipeline.

## Reproduce
Node.js >=22, standard library only:
```sh
node --test experiments/khepri/exp393/provenance_quorum.test.mjs
node experiments/khepri/exp393/run.mjs
```

11/11 tests passed locally. Two seeded 12,000-trial synthetic simulations:
- Gold-like prices: base 2000 +/- 200, errors shift +18%, seed 393.
- SEO-like metrics: base 100 +/- 10, errors shift -30%, seed 394.
- Feeds: A1 and A2 share upstream A; B and C are separate upstreams.
- Each upstream independently fails with probability 10%; an additional 3% common-mode fault shifts all three upstreams.
- Agreement tolerance 1%; false accept means a corroborated estimate >5% away from the synthetic truth.

| Method | Gold correct | Gold wrong | Gold abstain | SEO correct | SEO wrong | SEO abstain |
|---|---:|---:|---:|---:|---:|---:|
| Naive: count all 4 feed IDs, quorum 2 | 10321 | 563 | 1116 | 10303 | 581 | 1116 |
| Group by upstream, quorum 2 | 11340 | 660 | 0 | 11317 | 683 | 0 |
| Group by upstream, quorum 3 | 8428 | 342 | 3230 | 8396 | 365 | 3239 |

## Counterexamples and interpretation
1. Two mirror feeds reporting the same wrong price are **one** upstream, not two independent confirmations.
2. De-duplication with quorum=2 actually **increased** false accepts in this simulation (Gold 563 -> 660; SEO 581 -> 683) because the four-feed method abstains on 2-vs-2 ties, while the three-upstream method has a decisive but sometimes wrong 2-vs-1 majority. **Do not claim provenance grouping automatically improves accuracy.**
3. A three-upstream unanimity rule reduced false accepts (Gold 342, SEO 365), but abstained on ~27% of trials. The systemic 3% error remains invisible to consensus: gold had 337 common-mode faults; SEO 358. Stronger quorum is a coverage-vs-risk tradeoff, not ground truth.
4. Nontransitive tolerance chains (A close to B, B close to C, A not close to C) must not be accepted as one consensus cluster. Equal-size competing cliques abstain.
5. Unverified upstream labels are self-asserted and cannot prove independence. A malicious/misconfigured provider can lie about lineage.

## Scope / next steps
Pure synthetic, deterministic prototype; no live feeds, no credentials, no trading decisions, no production modification. Treat corroboration as an **alert/review signal**, never automatic correction. Before use, validate upstream provenance independently, timestamps, publication vintages, product comparability, and correlated failure assumptions. Investigate other fault magnitudes, partial dependence, and source outages.
