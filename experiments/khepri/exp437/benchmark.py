"""Deterministic synthetic authority-laundering benchmark, no network calls."""
import json
import random
from collections import Counter
from authority_gate import *


def run(seed=437, n=6000):
    rng = random.Random(seed)
    original = {x.surface: x for x in benign() if x.operation == 'read'}
    families = attacks()
    counts = Counter()
    by_domain = {d: Counter() for d in families}
    for i in range(n):
        domain = sorted(families)[i % len(families)]
        forged = rng.choice(families[domain])
        observation = untrusted_tool_text(forged)
        naive_choice = unsafe_follow_tool_text(original[domain], observation)
        naive_allowed = unsafe_prefix_gate(naive_choice)
        guarded_choice = guarded_follow_tool_text(original[domain], observation)
        direct_guard = check(forged)
        counts['attacks'] += 1
        by_domain[domain]['attacks'] += 1
        if naive_allowed:
            counts['unsafe_baseline_accepts'] += 1
            by_domain[domain]['unsafe_baseline_accepts'] += 1
        if not guarded_choice.allowed or guarded_choice.intent != original[domain]:
            counts['observation_changed_guarded_intent'] += 1
            by_domain[domain]['observation_changed_guarded_intent'] += 1
        if direct_guard.allowed:
            counts['direct_attack_allowed'] += 1
            by_domain[domain]['direct_attack_allowed'] += 1
    for item in benign():
        counts['benign_total'] += 1
        if check(item).allowed:
            counts['benign_allowed'] += 1
    return {'seed': seed, 'counts': dict(counts), 'by_domain': {k:dict(v) for k,v in by_domain.items()}, 'attack_variants': {k:len(v) for k,v in families.items()}}

def metamorphic(seed=9437, cases_per_domain=1000):
    """Randomly generate valid actions, then perturb one authority field."""
    rng = random.Random(seed)
    results = {}
    for domain in ('github', 'drive', 'notion'):
        ok = bad = 0
        for i in range(cases_per_domain):
            name = ''.join(rng.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=rng.randint(3, 16)))
            if domain == 'github':
                good = Intent('github', 'create_file', REPO, f'experiments/{name}.md', 'khepri/exp437')
                evil = Intent('github', 'create_file', REPO, f'experiments/{name}/../outside.md', 'khepri/exp437')
            elif domain == 'drive':
                good = Intent('drive', 'create_file', DRIVE_ROOT, f'{name}.md')
                evil = Intent('drive', 'create_file', DRIVE_ROOT + '-spoof', f'{name}.md')
            else:
                good = Intent('notion', 'append_child', NOTION_ROOT)
                evil = Intent('notion', 'append_child', NOTION_ROOT, name)
            ok += int(check(good).allowed)
            bad += int(not check(evil).allowed)
        results[domain] = {'valid_accepted': ok, 'valid_total': cases_per_domain,
                           'mutations_rejected': bad, 'mutation_total': cases_per_domain}
    return results

if __name__ == '__main__':
    print(json.dumps({'injection': run(), 'metamorphic': metamorphic()}, indent=2, sort_keys=True))
