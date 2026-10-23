"""Deterministic synthetic sweep of redundancy plans, two application domains."""
import json
import random
from pathlib import Path
from statistics import mean
from planner import Tool, Plan, exact_success, naive_success, monte_carlo, select

SEED = 403
N = 2000


def case(domain, rng):
    if domain == 'gold':
        reward = 10.0
        q_shared = rng.uniform(0, .30)
        q_diverse = rng.uniform(.01, .12)
        healthy_shared = rng.uniform(.98, .999)
        outage_shared = rng.uniform(.005, .12)
        healthy_diverse = rng.uniform(.94, .99)
        outage_diverse = rng.uniform(.10, .40)
        shared_cost = rng.uniform(.25, .7)
        diverse_cost = rng.uniform(.8, 1.5)
    else:
        reward = 12.0
        q_shared = rng.uniform(0, .25)
        q_diverse = rng.uniform(.01, .10)
        healthy_shared = rng.uniform(.97, .995)
        outage_shared = rng.uniform(.01, .10)
        healthy_diverse = rng.uniform(.93, .985)
        outage_diverse = rng.uniform(.15, .40)
        shared_cost = rng.uniform(.30, .70)
        diverse_cost = rng.uniform(.75, 1.45)
    tools = {
        'shared1': Tool('shared1', 'shared', healthy_shared, outage_shared, shared_cost),
        'shared2': Tool('shared2', 'shared', healthy_shared, outage_shared, shared_cost),
        'diverse1': Tool('diverse1', 'independent1', healthy_diverse, outage_diverse, diverse_cost),
        'diverse2': Tool('diverse2', 'independent2', healthy_diverse, outage_diverse, diverse_cost),
    }
    q = {'shared': q_shared, 'independent1': q_diverse, 'independent2': q_diverse}
    plans = (Plan('shared', (('shared1', 'shared2'),)), Plan('diverse', (('diverse1', 'diverse2'),)))
    return tools, q, plans, reward


def assess(domain):
    rng = random.Random(SEED + (0 if domain == 'gold' else 1))
    disagreements = 0
    regrets = []
    underestimation_regrets = []
    exact_vs_mc_max_error = 0.0
    for i in range(N):
        tools, q, plans, reward = case(domain, rng)
        optimal, exact_utilities = select(tools, q, plans, reward, 'exact')
        naive, _ = select(tools, q, plans, reward, 'naive')
        underestimated_q = {d: p / 2 for d, p in q.items()}
        underestimated, _ = select(tools, underestimated_q, plans, reward, 'exact')
        disagreements += optimal != naive
        regrets.append(exact_utilities[optimal] - exact_utilities[naive])
        underestimation_regrets.append(exact_utilities[optimal] - exact_utilities[underestimated])
        if i < 12:
            for plan in plans:
                mc = monte_carlo(tools, q, plan, 30000, SEED + i)
                exact_vs_mc_max_error = max(exact_vs_mc_max_error, abs(mc - exact_success(tools, q, plan)))
    return {
        'scenarios': N,
        'naive_disagreement_count': disagreements,
        'naive_mean_regret_per_scenario': round(mean(regrets), 6),
        'naive_worst_regret': round(max(regrets), 6),
        'underestimated_outage_mean_regret': round(mean(underestimation_regrets), 6),
        'underestimated_outage_wrong_decisions': sum(x > 1e-10 for x in underestimation_regrets),
        'mc_max_abs_error_first_24_checks': round(exact_vs_mc_max_error, 6),
    }


def focal():
    tools = {
        'a1': Tool('a1', 'shared', .99, .02, .4),
        'a2': Tool('a2', 'shared', .99, .02, .4),
        'b1': Tool('b1', 'independent1', .96, .25, 1.0),
        'b2': Tool('b2', 'independent2', .96, .25, 1.0),
    }
    q = {'shared': .18, 'independent1': .08, 'independent2': .08}
    plans = (Plan('shared', (('a1', 'a2'),)), Plan('diverse', (('b1', 'b2'),)))
    return {
        'exact_probabilities': {p.name: round(exact_success(tools, q, p), 6) for p in plans},
        'naive_probabilities': {p.name: round(naive_success(tools, q, p), 6) for p in plans},
        'true_expected_utilities': {k: round(v, 6) for k, v in select(tools, q, plans, 10, 'exact')[1].items()},
        'true_optimal': select(tools, q, plans, 10, 'exact')[0],
        'naive_choice': select(tools, q, plans, 10, 'naive')[0],
        'zero_outage_estimate_choice': select(tools, {d: 0 for d in q}, plans, 10, 'exact')[0],
    }


if __name__ == '__main__':
    result = {'seed': SEED, 'focal': focal(), 'gold': assess('gold'), 'seo': assess('seo')}
    Path('results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
