# Worker A — C333: review time can overturn fixed-K SEO conclusions

Date: 2026-10-24. Parent branch: sandbox/worker-a-20261024-c332-ranking-eval.

## Decision and correction

C332 compared confirmed issues in the first K URLs, ignoring the time required to review each URL. A fixed review-count budget is not a time budget. The direction of a ranking comparison can reverse when the real constraint is analyst time. Therefore C332 does not establish any ranking preference or analyst time savings.

Instead of further tuning synthetic SEO rankings, C333 builds a local-only, field-study-ready collection and evaluation protocol. There is no authorized real SEO dataset or independent human review in this experiment; no real-world performance claim is made.

## Capability

time_budget_study.py has two commands.

- prepare: creates independently shuffled sheets for reviewers A and B from a C330/C331-style offline audit. It hides clicks, segments, existing intent labels, and queue membership; includes URL, matched rule, unknown labels, blank times, and evidence notes. It refuses to overwrite existing sheets.
- evaluate: requires every candidate to be reviewed by both raters, with labels (accidental, intentional, unknown), measured integer seconds (1–3600), and evidence notes for known intent. Unknown and disagreeing labels remain unresolved. Compares C332 clicks_desc and segment_round_robin under total reviewer-seconds, not wall-clock time. Strict prefix stops at the first item exceeding the remaining budget; no opportunistic skipping.

Input guards reject duplicate, missing and extra URLs; unmeasured, noninteger, negative or excessive durations; missing evidence for known labels; and invalid budgets. The tool makes no HTTP/DNS calls, does not authenticate reviewers, and does not prove the supplied evidence. Never publish client URLs or private review notes.

## Reproducible tests

From repository root with Python 3.10+:

    python -m unittest discover -s research/worker_a/c332 -p 'test*.py' -q
    python -m unittest discover -s research/worker_a/c333 -p 'test*.py' -q
    python research/worker_a/c333/time_budget_study.py prepare --audit research/worker_a/c332/synthetic_audit.json --seed 42 --output-dir /tmp/c333_blank_sheets

For a synthetic completed-review demonstration, use the accompanying synthetic_reviewer_a.json and synthetic_reviewer_b.json files with:

    python research/worker_a/c333/time_budget_study.py evaluate --audit research/worker_a/c332/synthetic_audit.json --reviewer-a research/worker_a/c333/synthetic_reviewer_a.json --reviewer-b research/worker_a/c333/synthetic_reviewer_b.json --budget-seconds 20 80 160 360 --output /tmp/c333_result.json

Local results: 7/7 C333 tests passed and 12/12 C332 regression tests passed. A targeted counterexample shows that at K=3, round-robin finds two confirmed positives versus clicks-first's one, while at six reviewer-seconds clicks-first finds one versus round-robin's zero. Thus fixed-K preference can reverse under a time budget.

In a separate fabricated 15-URL demonstration, both methods found two confirmed positives at 160 reviewer-seconds; at 360 reviewer-seconds clicks-first found six and round-robin seven. All review times and labels were invented. The reported confirmed_per_reviewer_hour is arithmetic normalization of spent reviewer-seconds, not a causal productivity estimate; budget slack can remain when the next item cannot fit.

## Preregistered field-study requirements (not yet performed)

1. Use only authorized, non-sensitive inventory; keep real site URLs and review notes out of the public repository.
2. Freeze dataset, segments, algorithms, time budgets, label rubric, exclusions and success criteria before observing human labels and durations.
3. Obtain two independent reviewers, blinded to clicks and ranking. Require business-owner or policy evidence for known intent; unknown is valid.
4. Measure reviewer time and expertise, document order/fatigue effects, and adjudicate disagreement separately.
5. Compare fixed-K and time-budget issue yield, unresolved rate, label coverage and inter-rater agreement on held-out sites.
6. For causal productivity comparisons, randomize actual queue assignment across reviewers/sites, account for carryover, and preregister analysis. Retrospective replay alone is not a randomized trial.

## Boundaries and next direction

No main branch changes, real client data, human ratings, production traffic, CI runs, or external network experiments. This is a measurement instrument, not a production SEO tool. Further synthetic ranking cycles have diminishing value; the next cycle should seek authorized field evidence or change to a different lab problem.
