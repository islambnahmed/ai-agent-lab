"""Privacy-safe offline ranking evaluation regression tests."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_sitemap_budget_eval import evaluate, QUEUE_COLUMNS, LABEL_COLUMNS

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'seo_sitemap_budget_eval.py'


def fixtures():
    queue = [
        dict(zip(QUEUE_COLUMNS, ('P1', 'removed', 'https://example.com/a', 'review', 'csv_only_unverified', '', '0'))),
        dict(zip(QUEUE_COLUMNS, ('P2', 'changed', 'https://example.com/b', 'review', 'csv_only_unverified', '1', '2'))),
        dict(zip(QUEUE_COLUMNS, ('P3', 'added', 'https://example.com/c', 'review', 'csv_only_unverified', '0', ''))),
    ]
    labels = [
        dict(zip(LABEL_COLUMNS, ('https://example.com/a', 'no', 'normal'))),
        dict(zip(LABEL_COLUMNS, ('https://example.com/b', 'yes', 'high'))),
        dict(zip(LABEL_COLUMNS, ('https://example.com/c', 'yes', 'normal'))),
    ]
    return queue, labels


class BudgetEvalTests(unittest.TestCase):
    def test_full_queue_recall_is_tautologically_one(self):
        queue, labels = fixtures()
        result = evaluate(queue, labels, 3)
        self.assertEqual(result['priority_queue']['recall_at_budget'], 1)
        self.assertEqual(result['priority_queue']['false_positives'], 1)

    def test_budget_exposes_missed_important_item(self):
        queue, labels = fixtures()
        result = evaluate(queue, labels, 1)
        self.assertEqual(result['priority_queue']['true_positives'], 0)
        self.assertEqual(result['priority_queue']['high_impact_misses'], 1)
        self.assertEqual(result['priority_queue']['recall_at_budget'], 0)
        self.assertEqual(result['priority_queue']['precision_at_budget'], 0)

    def test_budget_two_catches_high_but_not_all(self):
        queue, labels = fixtures()
        result = evaluate(queue, labels, 2)
        self.assertEqual(result['priority_queue']['recall_at_budget'], .5)
        self.assertEqual(result['priority_queue']['high_impact_misses'], 0)

    def test_rejects_missing_and_duplicate_labels(self):
        queue, labels = fixtures()
        with self.assertRaisesRegex(ValueError, 'exactly'):
            evaluate(queue, labels[:-1], 2)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            evaluate(queue, labels + labels[:1], 2)

    def test_rejects_duplicate_queue_and_mixed_evidence(self):
        queue, labels = fixtures()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            evaluate(queue + queue[:1], labels, 2)
        queue[0]['evidence'] = 'local_csv_sha_checked'
        with self.assertRaisesRegex(ValueError, 'mixed'):
            evaluate(queue, labels, 2)

    def test_uncertain_and_no_positives_are_explicit(self):
        queue, labels = fixtures()
        labels[1]['review_worthy'] = 'uncertain'
        labels[2]['review_worthy'] = 'no'
        result = evaluate(queue, labels, 2)
        self.assertIsNone(result['priority_queue']['recall_at_budget'])
        self.assertEqual(result['priority_queue']['uncertain_reviewed'], 1)
        self.assertIsNone(result['no_priority_shuffle_baseline']['mean_recall_at_budget'])

    def test_reproducible_baseline_and_no_urls_in_output(self):
        queue, labels = fixtures()
        first = evaluate(queue, labels, 2, seed=8)
        self.assertEqual(first, evaluate(queue, labels, 2, seed=8))
        self.assertNotIn('example.com', json.dumps(first))

    def test_cli_emits_only_aggregates_and_rejects_invalid_header(self):
        queue, labels = fixtures()
        with tempfile.TemporaryDirectory() as temp:
            qpath, lpath = Path(temp) / 'queue.csv', Path(temp) / 'labels.csv'
            for path, columns, rows in ((qpath, QUEUE_COLUMNS, queue), (lpath, LABEL_COLUMNS, labels)):
                with path.open('w', newline='', encoding='utf-8') as stream:
                    writer = csv.DictWriter(stream, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
            p = subprocess.run([sys.executable, str(SCRIPT), '--queue', str(qpath),
                                '--labels', str(lpath), '--budget', '1'],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn('example.com', p.stdout)
            self.assertEqual(json.loads(p.stdout)['priority_queue']['high_impact_misses'], 1)
            qpath.write_text('bad,header\na,b\n', encoding='utf-8')
            bad = subprocess.run([sys.executable, str(SCRIPT), '--queue', str(qpath),
                                  '--labels', str(lpath), '--budget', '1'],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, '')


if __name__ == '__main__':
    unittest.main()
