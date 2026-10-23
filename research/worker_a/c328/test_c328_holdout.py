"""Regression tests for independently chosen C328 holdout mutants."""
import json
from pathlib import Path
import unittest
from robots_gate import decide
from run_c328_holdout import evaluate, prepare_cases

CASES = json.loads(Path(__file__).with_name('c328_targeted_cases.json').read_text(encoding='utf-8'))['cases']

class HoldoutMutationAudit(unittest.TestCase):
    def test_all_new_cases_pass_on_unmutated_parser(self):
        for c in prepare_cases(CASES):
            with self.subTest(case=c['id']):
                robots=c['robots'] + c.get('repeat_char','')*c.get('repeat_count',0)
                self.assertEqual(decide(robots,c['agent'],c['target']).status,c['expected'])

    def test_exact_input_boundaries(self):
        c=prepare_cases(CASES)[0]
        robots=c['robots']+c['repeat_char']*c['repeat_count']
        self.assertEqual(len(robots.encode('utf-8')), 500*1024)
        self.assertEqual(len(prepare_cases(CASES)[1]['target']), 8192)

    def test_independent_holdout_and_targeted_scores(self):
        before=evaluate()
        after=evaluate(CASES)
        self.assertEqual((before['mutants'],before['killed']),(14,6))
        self.assertEqual((after['mutants'],after['killed']),(14,14))
        self.assertEqual(len(before['survived']),8)
        self.assertEqual(after['survived'],[])
        self.assertTrue(all(x['fixture_kills'] or x['oracle_kill'] for x in after['details']))

    def test_mislabeled_fixture_cannot_inflate_score(self):
        bad={'id':'deliberately-wrong-label','robots':'User-agent: *\nDisallow: /x',
             'agent':'ExampleBot','target':'/x','expected':'allowed'}
        with self.assertRaisesRegex(AssertionError, 'baseline fails expected fixtures'):
            evaluate([bad])

if __name__ == '__main__':
    unittest.main()
