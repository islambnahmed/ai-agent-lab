"""Reproducible synthetic benchmark; counts are not real-world attack rates."""
import json
import posixpath
import random
from urllib.parse import unquote
from semantic_boundary import (Adapter, BoundExecutor, Request, Rejected,
                               REPO, NOTION_ROOT, weak_first_wins, toy_last_wins)

rng = random.Random(439)
a = Adapter()
e = BoundExecutor()
counts = dict(valid_github=0, valid_notion=0, duplicate_rejected=0,
              path_alias_rejected=0, payload_swap_rejected=0,
              adapter_drift_rejected=0, parser_disagreements=0,
              path_aliases_escape_sample_prefix=0)
N = 2000
for i in range(N):
    # Legitimate GitHub operations, varying payload and path.
    r = Request('github', REPO, 'create_file',
                f'experiments/khepri/exp439/note_{i}.md', 'khepri/exp439', str(i))
    p = e.issue(r, a)
    assert e.execute(p, r, a)
    counts['valid_github'] += 1

    # Legitimate JSON with reordered fields; canonical semantic representation.
    original = '{"kind":"paragraph","text":"note-%d"}' % i
    reordered = '{"text":"note-%d", "kind":"paragraph"}' % i
    r = Request('notion', NOTION_ROOT, 'append_child', payload=original)
    r2 = Request('notion', NOTION_ROOT, 'append_child', payload=reordered)
    p = e.issue(r, a)
    assert e.execute(p, r2, a)
    counts['valid_notion'] += 1

    # Two parsers disagree on duplicate-key JSON. Strict preparation rejects.
    bad = '{"kind":"paragraph","kind":"command","text":"note-%d"}' % i
    assert weak_first_wins(bad)['kind'] != toy_last_wins(bad)['kind']
    counts['parser_disagreements'] += 1
    try:
        e.issue(Request('notion', NOTION_ROOT, 'append_child', payload=bad), a)
        raise AssertionError('accepted duplicate keys')
    except Rejected:
        counts['duplicate_rejected'] += 1

    # Synthetic percent-decoding downstream adapter. Actual GitHub may reject.
    path = f'experiments/khepri/%2e%2e/%2e%2e/outside_{i}.md'
    assert path.startswith('experiments/khepri/')
    interpreted = posixpath.normpath(unquote(path))
    if not interpreted.startswith('experiments/khepri/'):
        counts['path_aliases_escape_sample_prefix'] += 1
    try:
        e.issue(Request('github', REPO, 'create_file', path, 'khepri/exp439', 'x'), a)
        raise AssertionError('accepted ambiguous path')
    except Rejected:
        counts['path_alias_rejected'] += 1

    # The permit must not allow payload substitutions or changed adapter versions.
    r = Request('github', REPO, 'create_file',
                f'experiments/khepri/exp439/swap_{i}.md', 'khepri/exp439', 'original')
    p = e.issue(r, a)
    changed = Request(r.surface, r.target, r.operation, r.path, r.branch,
                      'modified' + str(rng.randrange(10**6)))
    assert not e.execute(p, changed, a)
    counts['payload_swap_rejected'] += 1
    assert not e.execute(p, r, Adapter('v2'))
    counts['adapter_drift_rejected'] += 1
    assert e.execute(p, r, a)

assert len(e.effects) == N * 3
counts['total_cases'] = N * 6
counts['simulated_effects'] = len(e.effects)
print(json.dumps(counts, indent=2, sort_keys=True))
with open('benchmark_results.json', 'w') as f:
    json.dump(counts, f, indent=2, sort_keys=True)
    f.write('\n')
