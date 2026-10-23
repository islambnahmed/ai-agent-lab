"""Study lock regression tests: drift, privacy, reviewer independence and reuse."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study_lock import make_study, verify_and_evaluate, main, CODE_PATHS, digest


def audit():
    return {'rows': [
        {'url': '/a', 'status': 'disallowed', 'organic_clicks_30d': 100,
         'segment': 'docs', 'matched_rule': 'Disallow: /a', 'intent_label': 'accidental'},
        {'url': '/b', 'status': 'disallowed', 'organic_clicks_30d': 20,
         'segment': 'blog', 'matched_rule': 'Disallow: /b', 'intent_label': 'intentional'},
        {'url': '/allowed', 'status': 'allowed', 'organic_clicks_30d': 40}
    ]}


def fill(packet):
    packet = copy.deepcopy(packet)
    for item in packet['items']:
        item['label'] = 'accidental' if item['url'] == '/a' else 'intentional'
        item['seconds'] = 5
        item['evidence_note'] = 'fabricated fixture only; no human review'
    return packet


class StudyLockTests(unittest.TestCase):
    def setUp(self):
        self.report = audit()
        self.manifest, a, b = make_study(self.report, 17, [10, 30])
        self.a, self.b = fill(a), fill(b)

    def run_eval(self, **kwargs):
        args = {'manifest': self.manifest, 'report': self.report,
                'a': self.a, 'b': self.b, 'expected_manifest_sha256': digest(self.manifest)}
        args.update(kwargs)
        return verify_and_evaluate(**args)

    def test_happy_path_and_no_private_data_in_manifest(self):
        result = self.run_eval()
        self.assertEqual(result['rankings']['clicks_desc']['at_seconds']['30']['confirmed_accidental'], 1)
        self.assertEqual(result['study_lock']['manifest_sha256'], digest(self.manifest))
        text = json.dumps(self.manifest)
        for private in ('/a', '/b', '/allowed', 'Disallow: /a', 'fabricated fixture'):
            self.assertNotIn(private, text)

    def test_reject_rank_data_change_same_urls(self):
        changed = copy.deepcopy(self.report)
        changed['rows'][0]['organic_clicks_30d'] = 0
        with self.assertRaisesRegex(ValueError, 'audit changed'):
            self.run_eval(report=changed)

    def test_reject_other_audit_row_change(self):
        changed = copy.deepcopy(self.report)
        changed['rows'][-1]['organic_clicks_30d'] = 41
        with self.assertRaisesRegex(ValueError, 'audit changed'):
            self.run_eval(report=changed)

    def test_reject_budget_drift_and_tampered_manifest(self):
        with self.assertRaisesRegex(ValueError, 'budgets differ'):
            self.run_eval(budgets=[30])
        manifest = copy.deepcopy(self.manifest)
        manifest['budget_seconds'] = [5, 30]
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            self.run_eval(manifest=manifest)

    def test_reject_review_packet_order_and_rule_changes(self):
        altered = copy.deepcopy(self.a)
        altered['items'].reverse()
        with self.assertRaisesRegex(ValueError, 'URL order'):
            self.run_eval(a=altered)
        altered = copy.deepcopy(self.a)
        altered['items'][0]['matched_rule'] = 'Disallow: /other'
        with self.assertRaisesRegex(ValueError, 'matched rule'):
            self.run_eval(a=altered)

    def test_reject_unblinding_extra_fields_and_reviewer_swap(self):
        altered = copy.deepcopy(self.a)
        altered['items'][0]['organic_clicks_30d'] = 100
        with self.assertRaisesRegex(ValueError, 'unexpected item'):
            self.run_eval(a=altered)
        with self.assertRaisesRegex(ValueError, 'immutable field'):
            self.run_eval(a=self.b)

    def test_reject_code_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'changed.py'
            path.write_text('changed code')
            with patch.dict(CODE_PATHS, {'ranking_benchmark': path}):
                with self.assertRaisesRegex(ValueError, 'code changed'):
                    self.run_eval()

    def test_labels_and_notes_can_be_completed_without_invalidating_lock(self):
        a = copy.deepcopy(self.a)
        a['items'][0]['label'] = 'unknown'
        a['items'][0]['evidence_note'] = ''
        result = self.run_eval(a=a)
        self.assertEqual(result['rankings']['clicks_desc']['at_seconds']['30']['unresolved'], 1)

    def test_cli_prepare_evaluate_and_refuse_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            src = folder / 'audit.json'
            src.write_text(json.dumps(self.report))
            out = folder / 'study'
            main(['prepare', '--audit', str(src), '--seed', '17',
                  '--budget-seconds', '10', '30', '--output-dir', str(out)])
            self.assertEqual(len(list(out.glob('*.json'))), 3)
            with self.assertRaises(SystemExit):
                main(['prepare', '--audit', str(src), '--seed', '17',
                      '--budget-seconds', '10', '30', '--output-dir', str(out)])
            for name, values in [('reviewer_a.json', self.a), ('reviewer_b.json', self.b)]:
                (out / name).write_text(json.dumps(values))
            result_path = folder / 'result.json'
            main(['evaluate', '--audit', str(src), '--study-dir', str(out), '--output', str(result_path),
                  '--expected-study-sha256', digest(self.manifest)])
            self.assertEqual(json.loads(result_path.read_text())['candidate_count'], 2)
            with self.assertRaises(SystemExit):
                main(['evaluate', '--audit', str(src), '--study-dir', str(out), '--output', str(result_path),
                  '--expected-study-sha256', digest(self.manifest)])

    def test_reject_duplicate_budgets_bool_and_nan(self):
        for bad in ([10, 10], [True], [0], [], [float('nan')]):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, TypeError)):
                    make_study(self.report, 1, bad)


if __name__ == '__main__':
    unittest.main()
