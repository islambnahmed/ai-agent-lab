"""Offline curated-case benchmark; does not perform any network I/O."""
import collections
import json
from pathlib import Path
from robots_gate import decide

root = Path(__file__).parent
cases = json.loads((root / 'c326_offline_seo_corpus.json').read_text(encoding='utf-8'))['cases']
by_category = collections.defaultdict(lambda: {'total': 0, 'passed': 0})
failures = []
for case in cases:
    robots = case['robots'] + case.get('repeat_char', '') * case.get('repeat_count', 0)
    status = decide(robots, case['agent'], case['target']).status
    bucket = by_category[case['category']]
    bucket['total'] += 1
    if status == case['expected']:
        bucket['passed'] += 1
    else:
        failures.append({'id': case['id'], 'expected': case['expected'], 'actual': status})
report = {
    'fixture_count': len(cases),
    'passed': len(cases) - len(failures),
    'failed': len(failures),
    'by_category': dict(sorted(by_category.items())),
    'failures': failures,
    'limitations': 'Synthetic offline cases; not a full RFC or crawler-compliance test.',
}
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
