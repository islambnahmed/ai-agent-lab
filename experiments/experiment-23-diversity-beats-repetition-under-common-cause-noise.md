# Experiment 23 — Diversity beats repetition under common-cause noise

## Question
Experiment 22 required an error bound, while Experiment 20 showed that correlated errors break ordinary majority guarantees. Can diversity across independent failure domains recover useful robustness?

## Simulation
Binary truth; seven votes. Each vote has 5% independent error. In addition, a failure domain can flip every vote assigned to it with 5% probability. Domain flips are independent across domains. Majority vote decides.

200,000 Monte Carlo trials per condition, fixed experimental seed.

| independent failure domains across 7 votes | observed majority error |
|---:|---:|
| 1 | 5.034% |
| 2 | 4.952% |
| 3 | 1.6045% |
| 4 | 0.9985% |
| 7 | 0.2235% |

For comparison, with no common-cause component and only 5% independent per-vote error, seven-vote majority error was about 0.02% in the same-size simulation.

## Counterexample
Seven repetitions are not seven independent pieces of evidence. With one shared failure domain, the majority error remains approximately the shared-domain error rate: adding votes barely helps against that common cause.

Two domains also provide little benefit here because seven votes necessarily give one domain a majority-sized bloc. The improvement becomes material only when failure mass is distributed across enough genuinely independent domains.

## Transfer
- flaky tests: rerunning the same test in the same environment may not diversify the failure source; changing environment/implementation/oracle can be more valuable than adding repetitions.
- multi-agent review: seven calls to near-identical agents sharing the same evidence/model failure mode can behave like one correlated voter; methodological or evidential diversity matters more than nominal agent count.

## Reusable lesson
Track **independent failure domains**, not raw vote count. Reliability calculations should treat common-cause risk separately from independent noise. When possible, spend verification budget on interventions that break shared failure modes before spending it on more repetitions.

## Limits
The numerical results depend on this deliberately simple common-cause model and do not establish real-world agent error rates. The transferable result is structural: correlation can dominate majority-vote reliability, and diversification can reduce that exposure when the domains are genuinely independent.
