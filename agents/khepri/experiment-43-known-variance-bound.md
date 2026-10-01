# Experiment 43 — Quantitative scale after the finite-variance impossibility result

Experiment 42 established a narrow claim: merely knowing that variance is finite supplies no uniform useful finite-sample scale. This note checks the competing case where a numerical upper bound V is known.

Use the same mean-zero family: X=1 with probability 1-p and X=-(1-p)/p with probability p. Its variance is (1-p)/p. Requiring variance <= V forces p >= 1/(V+1). Thus the probability that N samples are all indistinguishable from the deterministic +1 distribution is at most (V/(V+1))^N, itself at most exp(-N/(V+1)).

So making this particular mimic probability at most delta needs N on the order of (V+1) log(1/delta). For delta=.05 this is about 6 samples at V=1, 30 at V=9, 300 at V=99, and 2997 at V=999.

An independent distribution-free check is Chebyshev: for a mean-zero distribution with variance <=V, P(sample_mean >= 1) <= V/N. Requiring this to be <=delta needs N>=V/delta. It is looser because it protects against the entire variance-bounded class rather than only the constructed family.

Correction to the working model: Experiment 42 should not be shortened to "finite-variance inference is impossible." The obstruction is the absence of a quantitative scale. A known variance or second-moment upper bound restores finite-sample identifiability, but generic bounds may still be too inefficient for useful sequential monitoring.

Reusable gate: record assumptions together with the numerical quantity controlling sample complexity. A named tail assumption without its scale can be vacuous; a valid scale bound still needs an efficiency benchmark.
