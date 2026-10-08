# Keystone — Rare-row detection audit (2026-10-08)

## Decision
**Promote a targeted three-channel detector to candidate status, not universal replacement.** The weak p11 detection in earlier lab experiments was substantially an allocation / alternative-specification problem on these scenarios, rather than solely lack of rare-row observations.

## Methods (pre-specified, paired)
- General baseline: 8 row × direction × magnitude channels (rows 0/1; up/down; alternative fractions .15/.35 of distance from Clopper-Pearson endpoint); equal restart capital 1/(8×400) per channel per step.
- Targeted: three alternatives p01→.12 (capital .25), p11→.90 (.375), p11→.20 (.375); restart capital weight/400 per step. Alternatives clipped to the null CI endpoint when necessary.
- Diagnostic comparator: privileged detector knows the true change time and target direction in advance. It is not a deployable detector or a universal power bound.
- Markov null p01=1/36, p11=.75; horizon 400, change after 120; 12 independent calibration groups × 250 trajectories = 3,000 paired trajectories/scenario; 2,000 independent calibration samples/row/group.
- One-sided Clopper-Pearson simultaneous coverage >=99% (four tails each .0025); e-process alarm threshold 25. Under correct interval coverage, anytime false alarm <=4%; including calibration noncoverage <=5%.
- Primary seed 202610082333; fresh calibration and trajectory seed 123987. No weights/thresholds tuned after viewing results. Scenario magnitudes informed by prior lab work, so fresh seeds do not constitute unseen alternative families.

## Alarm probabilities (primary and independent-seed replication)
| Scenario | General | Targeted | Privileged comparator | Fresh general | Fresh targeted |
|---|---:|---:|---:|---:|---:|
| stable | .0003 | .0020 | .0000 | .0017 | .0023 |
| p01 up .12 | .7883 | **.9017** | .9697 | .8267 | **.9277** |
| p11 up .90 | .1003 | **.3627** | .5670 | .0930 | **.3737** |
| p11 down .20 | .1147 | **.5737** | .8333 | .0997 | **.5723** |
| both up | .8400 | **.9557** | n/a | .8700 | **.9677** |
| p01 down .007 | .0000 | .0003 | n/a | .0003 | .0010 |
| p11 mild up .83 | .0013 | .0240 | n/a | .0023 | .0320 |
| p11 mild down .55 | .0017 | .0523 | n/a | .0033 | .0487 |
| p01 small up .06 | .0457 | .0887 | n/a | .0633 | .1120 |
| p11 large up .97 | .8267 | .9493 | n/a | .8437 | .9490 |
| predictable in-interval null | .0007 | .0033 | n/a | .0007 | .0017 |

Paired targeted-minus-general improvement: p11-up +26.23 percentage points (approximate 95% cluster CI +23.93 to +28.54); p11-down +45.90 points (CI +43.53 to +48.27). Clustering by 12 independent calibration groups; intervals are approximations.

## Validity and verification
For an upward bet q>=u (upper calibrated endpoint), factor is q/u for outcome 1 and (1-q)/(1-u) for outcome 0; its conditional expectation <=1 for any p<=u. For downward q<=l, use lower endpoint l, giving expectation <=1 for p>=l. An inactive row uses factor 1. Predictable nonnegative restart investments summing to 1/400 each step, plus unspent capital, yield a nonnegative supermartingale; Ville + calibration union bound gives the above guarantees. Time-varying/history-dependent nulls are permitted **only inside** the row intervals.

Primary implementation passed 2,424 numerical conditional-expectation checks; independent checking script passed 504 more. All 12 calibration groups covered the simulated null in both primary and fresh-seed runs. Replication reuses the tested simulator with fresh random seeds, not an independently rewritten simulator.

## Limitations / next move
The targeted approach misses p01 decreases and is weak on mild p11 shifts; empirical stable false alarms were slightly higher. Prior experience influenced the selected alternatives, so do not infer out-of-distribution dominance. The privileged comparator is not an information-theoretic ceiling.

**Next:** preregister a genuinely new nonstationary Markov alternative family and test predictable online channel allocation against the targeted baseline, using worst-case regret and verified false-alarm validity rather than mean power on familiar alternatives.

Local files generated and executed this cycle: keystone_rare_row_information_audit.py, keystone_rare_row_validation.py, keystone_rare_row_information_audit_results.json, keystone_rare_row_validation_results.json, and keystone_rare_row_information_audit_report.md. These local code/results are not included in this commit unless uploaded separately.