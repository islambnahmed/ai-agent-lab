"""C327 offline regressions for gaps discovered by mutation testing."""
import json
from pathlib import Path
import unittest
from robots_gate import decide
from run_mutation_benchmark import evaluate, CORPUS, TARGETED


class MutationBenchmark(unittest.TestCase):
    def test_targeted_cases(self):
        for case in TARGETED:
            with self.subTest(id=case['id']):
                robots = case['robots'] + case.get('repeat_char', '') * case.get('repeat_count', 0)
                self.assertEqual(decide(robots, case['agent'], case['target']).status, case['expected'])

    def test_all_mutants_killed_by_augmented_suite(self):
        report = evaluate(CORPUS + TARGETED)
        self.assertEqual(report['mutants'], 22)
        self.assertEqual(report['survived'], [])
        self.assertEqual(report['killed'], 22)
        self.assertFalse(any('error' in str(x['oracle_kill']) for x in report['details']))

    def test_baseline_has_three_known_gaps(self):
        report = evaluate(CORPUS)
        self.assertEqual(report['killed'], 19)
        self.assertEqual(set(report['survived']), {
            'file_limit_disabled', 'url_query_dropped', 'prefix_score_ignores_anchor'
        })


if __name__ == '__main__':
    unittest.main()
