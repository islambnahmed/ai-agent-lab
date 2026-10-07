# Keystone: prequential online change detector

## Question
Can an online-learned alternative avoid the leakage failure from scoring an observation after updating on that same observation?

## Protocol
- Bernoulli regime: p=0.9 until t=100, then p=0.1; horizon 200.
- 10,000 independent seeded runs (seed 9).
- Long model estimated only from observations 0..49 and then frozen.
- Fast model initialized from the same estimate; EWMA alpha=0.1.
- At each t, score log predictive likelihood ratio fast vs long **before** updating fast with x_t (prequential/out-of-sample ordering).
- Evidence statistic: S_t=max(0,S_{t-1}+log p_fast(x_t)-log p_long(x_t)).
- Alarm threshold h=6.

## Result
- False alarms before change: 2.08%.
- Detection after change: 97.92% of all runs (runs with earlier false alarm excluded from post-change detection by first-alarm accounting).
- Mean post-change detection delay among valid detections: 7.37 observations.
- Median delay: 7 observations.

Threshold sweep: h=5 => 3.34% false alarms, 6.65 mean delay; h=7 => 1.35%, 8.08; h=8 => 0.98%, 8.76.

## Interpretation
The previous 100% false-alarm failure was primarily an evaluation/update-order leakage bug, not evidence that online alternatives are intrinsically unusable. Prequential scoring restores sane false-alarm behavior. However, it is materially slower than the earlier oracle sequential detector (~3.7 observations) that knew the alternative distribution. The remaining research problem is therefore the price of learning the alternative online, not merely change detection itself.

## Next test
Compare prequential EWMA against window and mixture/Bayesian alternatives under matched false-alarm budgets across unknown change magnitudes, and report predictive regret in addition to detection delay.
