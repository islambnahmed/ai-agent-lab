"""Independent deterministic offline evaluation; never makes network requests."""
import itertools
import json
from pathlib import Path
import re
import unittest
from robots_gate import decide

CORPUS = Path(__file__).with_name('c326_offline_seo_corpus.json')

def reference_prefix(rules, target):
    applicable = [(len(prefix), kind == 'Allow', kind) for kind, prefix in rules if target.startswith(prefix)]
    if not applicable:
        return 'allowed'
    return 'allowed' if max(applicable)[1] else 'disallowed'

def reference_glob(pattern, target):
    anchor = pattern.endswith('$')
    core = pattern[:-1] if anchor else pattern
    expression = ''.join('.*' if c == '*' else re.escape(c) for c in core)
    if anchor:
        return re.fullmatch(expression, target) is not None
    return re.match(expression, target) is not None

class OfflineSEOCorpus(unittest.TestCase):
    def test_curated_cases(self):
        data = json.loads(CORPUS.read_text(encoding='utf-8'))
        ids = set()
        for case in data['cases']:
            with self.subTest(id=case['id']):
                self.assertNotIn(case['id'], ids)
                ids.add(case['id'])
                robots = case['robots'] + case.get('repeat_char', '') * case.get('repeat_count', 0)
                self.assertEqual(decide(robots, case['agent'], case['target']).status, case['expected'])

    def test_independent_prefix_oracle(self):
        paths = ['/' + ''.join(s) for n in range(5) for s in itertools.product('ab', repeat=n)]
        prefixes = ['/' + ''.join(s) for n in range(4) for s in itertools.product('ab', repeat=n)]
        for a in prefixes:
            for b in prefixes:
                for first_kind, second_kind in [('Allow', 'Disallow'), ('Disallow', 'Allow')]:
                    rules = [(first_kind, a), (second_kind, b)]
                    robots = 'User-agent: *\n' + '\n'.join(f'{k}: {p}' for k, p in rules)
                    for target in paths:
                        expected = reference_prefix(rules, target)
                        got = decide(robots, 'ExampleBot', target).status
                        self.assertEqual(got, expected, (rules, target))

    def test_independent_wildcard_oracle(self):
        paths = ['/' + ''.join(s) for n in range(5) for s in itertools.product('ab', repeat=n)]
        patterns = ['/' + ''.join(s) for n in range(5) for s in itertools.product('ab*', repeat=n)]
        for pattern in patterns:
            for anchor in ['', '$']:
                rule = pattern + anchor
                robots = f'User-agent: *\nDisallow: {rule}'
                for target in paths:
                    expected = 'disallowed' if reference_glob(rule, target) else 'allowed'
                    got = decide(robots, 'ExampleBot', target).status
                    self.assertEqual(got, expected, (rule, target))

    def test_bom_and_rule_order_invariance(self):
        rules = ['Disallow: /private', 'Allow: /private/public', 'Disallow: /tmp']
        targets = ['/private', '/private/public/x', '/tmp', '/public', '/robots.txt']
        for perm in itertools.permutations(rules):
            base = 'User-agent: *\n' + '\n'.join(perm)
            for target in targets:
                expected = decide(base, 'ExampleBot', target).status
                self.assertEqual(decide('\ufeff' + base, 'ExampleBot', target).status, expected)
                self.assertEqual(decide(base.replace('\n', '\r\n'), 'ExampleBot', target).status, expected)
                canonical = 'User-agent: *\n' + '\n'.join(rules)
                self.assertEqual(expected, decide(canonical, 'ExampleBot', target).status)

if __name__ == '__main__':
    unittest.main()
