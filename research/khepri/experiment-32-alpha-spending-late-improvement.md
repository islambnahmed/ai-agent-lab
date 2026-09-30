# Khepri Experiment 32 — Alpha spending and late improvement

## Question
Experiment 31 showed that repeated fresh audits need a global false-positive budget. Does the way that budget is spent matter for detecting genuine improvements that arrive late?

## Method
Monte Carlo, 20,000 runs per condition, 100 sequential audits. Under the null each audit statistic is N(0,1). After a chosen change point t0, the mean shifts by delta*sqrt(50). Two one-sided family-wise-error-controlled schedules were compared:

1. **Uniform horizon:** alpha_t = 0.05/100.
2. **Front-loaded:** alpha_t = 0.05*(6/pi^2)/t^2.

Both spend at most ~0.05 total alpha by the union bound. Seed 42. Change points t0={1,25,50,75}; delta={0.25,0.40}.

## Results
For delta=0.25, detection probability after the real change:
- t0=1: uniform 0.998; front-loaded 0.927
- t0=25: uniform 0.994; front-loaded 0.391
- t0=50: uniform 0.965; front-loaded 0.206
- t0=75: uniform 0.815; front-loaded 0.084

For delta=0.40:
- t0=25: 1.000 vs 0.998
- t0=50: 1.000 vs 0.956
- t0=75: 1.000 vs 0.742

Observed pre-change false-alarm probability stayed <=~0.05 in these simulations. The front-loaded schedule spent almost all of its error budget early, so weak-but-real late improvements became nearly invisible.

## Counterexample / model correction
"Any alpha-spending schedule with total <=0.05 is good enough" is false if the goal includes useful power throughout a long-lived agent experiment. Error control alone does not determine an evaluation policy.

## Transferable lesson
For a bounded audit horizon, reserve meaningful alpha for late cycles (uniform spending is a simple baseline). For an unbounded experiment, do not blindly use a strongly front-loaded summable schedule; explicitly optimize a power-vs-time objective or periodically start a predeclared new evaluation epoch while preserving an overall error-control policy.

## Reproducibility sketch
For each run generate Z[t]~N(0,1); add delta*sqrt(50) for t>=t0; reject at audit t when Z[t] > Phi^-1(1-alpha_t); record any post-change rejection and any pre-change rejection.

This is evidence about evaluation design, not evidence that the agents themselves improved.
