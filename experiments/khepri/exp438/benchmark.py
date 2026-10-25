"""Deterministic synthetic tests of binding, replay, and authorized replacements."""
from dataclasses import replace
import json
import random
from bound_execution import Action, Gate, REPO, DRIVE_ROOT, NOTION_ROOT, naive_execute

SEED=438
rng=random.Random(SEED)
origins=[
    Action('github','create_file',REPO,'experiments/khepri/exp438/note.md','khepri/exp438','safe'),
    Action('drive','create_file',DRIVE_ROOT,'lab-note.md','','safe'),
    Action('notion','append_child',NOTION_ROOT,'','','safe'),
]
metrics={'seed':SEED,'legitimate_accepted':0,'payload_swap_baseline_accepted':0,
         'payload_swap_guard_accepted':0,'replay_baseline_accepted':0,
         'replay_guard_accepted':0,'same_policy_path_swap_baseline_accepted':0,
         'same_policy_path_swap_guard_accepted':0,'total_trials':0}
for surface, a in enumerate(origins):
    for i in range(1000):
        g=Gate(); p=g.issue(a)
        changed=replace(a,payload=f'unreviewed-{surface}-{i}-{rng.randrange(1<<24)}')
        metrics['payload_swap_baseline_accepted']+=int(naive_execute(a,changed))
        metrics['payload_swap_guard_accepted']+=int(g.execute(p,changed))
        metrics['legitimate_accepted']+=int(g.execute(p,a))
        metrics['replay_baseline_accepted']+=int(naive_execute(a,a))
        metrics['replay_guard_accepted']+=int(g.execute(p,a))
        metrics['total_trials']+=1
for i in range(1000):
    a=origins[0]
    b=replace(a,path=f'experiments/khepri/exp438/other_{i}.md')
    g=Gate(); p=g.issue(a)
    metrics['same_policy_path_swap_baseline_accepted']+=int(naive_execute(a,b))
    metrics['same_policy_path_swap_guard_accepted']+=int(g.execute(p,b))
    metrics['total_trials']+=1
print(json.dumps(metrics,indent=2,sort_keys=True))
with open('benchmark_results.json','w') as f:
    json.dump(metrics,f,indent=2,sort_keys=True)
    f.write('\n')
