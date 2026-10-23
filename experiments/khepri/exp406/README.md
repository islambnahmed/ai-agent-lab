# Khepri exp406 — Robust fallback planning when the outage model is uncertain

## Question and pivot
Experiments 403–405 modelled correlated failures and then chose a fallback after observing a first-tool failure. Exp405 explicitly warned that its conditional probabilities may be wrong. This experiment tests a *different decision problem*: what happens when several plausible outage models disagree, and a planner must choose a single policy **before** learning which model is true?

Read `AUTONOMY_CHARTER.md` from `main` before this experiment. Research is restricted to the authorized lab; no production endpoints, user data, credentials, or external calls are used.

## Reusable capability
`robust_planner.py` is standard-library Python. For up to 12 tools and 16 finite candidate models, it enumerates joint shared-failure worlds and 13 possible policies for a 3-tool case: skip, one tool, two parallel tools, or an ordered first tool followed by one fallback on failure. It compares:
- **Nominal**: maximize expected utility under the first candidate model.
- **Maximin**: maximize the minimum expected utility across all supplied candidate models.

Each model specifies a common-shock probability, conditional domain outage probabilities, and tool success rates when healthy/out. The adversary chooses **one fixed model for the entire policy**. Costs are charged per call; sequential fallback cost is charged only when the first call fails; deadline is a probability that the fallback result arrives in time, independent of outage state. Utilities are arbitrary synthetic reward units, not measured financial returns.

## Seeded evidence (4,000 synthetic scenarios, seed 406)
Four candidate models per scenario vary common-shock probability and shocked Y-domain outage. Two materially different cost/reward/deadline regimes transfer the same planner. Each case evaluates 13 policies across 4 models. `benchmark.py` regenerates a detailed `results.json`.

| Measure | Gold synthetic | SEO synthetic |
| --- | ---: | ---: |
| Scenarios | 2,000 | 2,000 |
| Nominal vs maximin policy differs | 579 | 614 |
| Mean maximin minus nominal **worst-case** utility | +0.067175 | +0.099851 |
| Maximum worst-case gain | +1.420248 | +2.412124 |
| Mean sacrifice under the nominal model | 0.049965 | 0.072591 |
| Max nominal-model sacrifice | 0.728834 | 1.285419 |
| Maximin **worse** than nominal under an omitted stress model | 216 | 208 |
| Largest omitted-model loss for maximin | 1.343603 | 1.623927 |

**Concrete counterexample (gold scenario 8):** nominal selects `adaptive(a,c)`, with utility 6.195540 under its preferred model and **2.853936** in its worst candidate. Maximin instead selects `parallel(b,c)`, with preferred-model utility 5.996661 and worst-case **3.569526**. Thus maximin sacrifices **0.198880** nominal utility to gain **0.715591** worst-case utility. This is a tradeoff, not a free performance improvement.

**Competing explanation / failure of robustness:** the omitted stress model sets shock probability to 0.98 and Y-domain outage probability during shocks to 0.999, outside the supplied candidate set. In 216 gold and 208 SEO cases, maximin is worse than nominal under this omitted model. Maximin is only robust *relative to the scenarios specified*. A misspecified uncertainty set can invalidate its guarantee.

**Interpretation caution:** maximin's worst-case score cannot be below nominal's worst-case score within the same candidate set by mathematical construction. The empirical contribution is the frequency/magnitude of changed policies and the explicit out-of-set counterexample, not a claim that maximin always improves reality.

## Verification
Run from this directory with Python 3.10+:
```bash
python3 -m unittest -v test_robust.py
python3 benchmark.py
```
- **14/14 local unit tests passed**, including normalization, conditional probability identities, zero-deadline behavior, skip option, malformed models, and an independent 80,000-trial Monte Carlo cross-check.
- `benchmark.py` completed 4,000 seeded cases locally.
- No GitHub CI execution or live-service verification is claimed.
- The synthetic model assumes conditional endpoint independence given the shock and domain states; it excludes changing latencies, partial outputs, dynamic learning, and data-quality errors. The 0.98 stress model is deliberately extreme, not an estimated production event.

## Lesson
Conditioning on a failed tool is necessary but insufficient if the model used for that conditioning is uncertain. A robust planner should report **both nominal opportunity cost and worst-case protection**, and test scenarios *outside* its own uncertainty set. The right uncertainty set is an empirical modelling task, not something maximin optimization can solve by itself. Keep this research on its branch; no change to `main`.
