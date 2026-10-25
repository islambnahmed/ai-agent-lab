"""Synthetic, offline field-session accounting checks; never real-site results."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from seo_sitemap_field_score import score, REF_COLS, SESSION_COLS, DECISION_COLS


class FieldScoreTests(unittest.TestCase):
    def fixtures(self):
        refs = [dict(zip(REF_COLS, ('p1', 'u1', 'yes', 'high'))),
                dict(zip(REF_COLS, ('p1', 'u2', 'yes', 'normal'))),
                dict(zip(REF_COLS, ('p1', 'u3', 'no', 'normal'))),
                dict(zip(REF_COLS, ('p1', 'u4', 'uncertain', 'normal')))]
        sessions = [dict(zip(SESSION_COLS, ('p1', 'r1', arm, seconds, '2')))
                    for arm, seconds in (('manual', '80'), ('triage', '40'))]
        decisions = [dict(zip(DECISION_COLS, ('p1', 'r1', arm, url, 'yes', flag)))
                     for arm, entries in (('manual', [('u3', 'yes'), ('u4', 'no')]),
                                          ('triage', [('u1', 'yes'), ('u2', 'yes')]))
                     for url, flag in entries]
        return refs, sessions, decisions

    def test_paired_metrics_and_no_ids_in_output(self):
        refs, sessions, decisions = self.fixtures()
        result = score(refs, sessions, decisions)
        self.assertEqual(result['paired_sessions'], 1)
        self.assertEqual(result['arms']['triage']['tp'], 2)
        self.assertEqual(result['arms']['triage']['recall'], 1)
        self.assertEqual(result['arms']['triage']['seconds_per_true_finding'], 20)
        self.assertEqual(result['arms']['manual']['high_impact_misses'], 1)
        self.assertEqual(result['arms']['manual']['fp'], 1)
        self.assertEqual(result['arms']['manual']['recall'], 0)
        self.assertNotIn('u1', json.dumps(result))
        self.assertNotIn('p1', json.dumps(result))

    def test_rejects_missing_arm_and_budget_mismatch(self):
        refs, sessions, decisions = self.fixtures()
        with self.assertRaisesRegex(ValueError, 'both review arms'):
            score(refs, sessions[:1], decisions)
        sessions[0]['inspection_budget'] = '1'
        with self.assertRaisesRegex(ValueError, 'equal inspection budgets'):
            score(refs, sessions, decisions)

    def test_rejects_uninspected_flag_and_excess_inspection(self):
        refs, sessions, decisions = self.fixtures()
        decisions[0]['inspected'] = 'no'
        with self.assertRaisesRegex(ValueError, 'uninspected'):
            score(refs, sessions, decisions)
        decisions[0]['inspected'] = 'yes'
        decisions.append(dict(zip(DECISION_COLS, ('p1', 'r1', 'manual', 'u1', 'yes', 'no'))))
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            score(refs, sessions, decisions)

    def test_rejects_duplicate_reference_or_decision(self):
        refs, sessions, decisions = self.fixtures()
        with self.assertRaisesRegex(ValueError, 'duplicate reference'):
            score(refs + refs[:1], sessions, decisions)
        with self.assertRaisesRegex(ValueError, 'duplicate review decision'):
            score(refs, sessions, decisions + decisions[:1])

    def test_rejects_reference_pair_with_no_sessions(self):
        refs, sessions, decisions = self.fixtures()
        refs.append(dict(zip(REF_COLS, ('p2', 'u5', 'yes', 'high'))))
        with self.assertRaisesRegex(ValueError, 'reference pair has no paired review sessions'):
            score(refs, sessions, decisions)

        # Adding both arms for the second pair restores complete accounting.
        sessions.extend(dict(zip(SESSION_COLS, ('p2', 'r2', arm, '5', '1')))
                        for arm in ('manual', 'triage'))
        result = score(refs, sessions, decisions)
        self.assertEqual(result['reference_pairs'], 2)
        self.assertEqual(result['paired_sessions'], 2)
        self.assertEqual(result['arms']['manual']['fn'], 3)
        self.assertEqual(result['arms']['triage']['fn'], 1)

    def test_pooled_recall_can_reverse_paired_session_conclusion(self):
        # A large pair dominates pooled recall even when the average paired
        # session moves the opposite direction (Simpson-style reversal).
        refs = [dict(zip(REF_COLS, ('large', f'u{i}', 'yes', 'normal')))
                for i in range(100)]
        refs.append(dict(zip(REF_COLS, ('small', 'u0', 'yes', 'high'))))
        sessions = [dict(zip(SESSION_COLS, (pair, reviewer, arm, '100', budget)))
                    for pair, reviewer, budget in (('large', 'r1', '100'),
                                                   ('small', 'r2', '1'))
                    for arm in ('manual', 'triage')]
        decisions = [dict(zip(DECISION_COLS, ('large', 'r1', arm, f'u{i}', 'yes', 'yes')))
                     for arm, count in (('manual', 80), ('triage', 90))
                     for i in range(count)]
        decisions.append(dict(zip(DECISION_COLS,
                                  ('small', 'r2', 'manual', 'u0', 'yes', 'yes'))))
        result = score(refs, sessions, decisions)
        self.assertGreater(result['arms']['triage']['recall'],
                           result['arms']['manual']['recall'])
        paired = result['paired_recall']
        self.assertEqual(paired['eligible_sessions'], 2)
        self.assertEqual(paired['manual_mean'], 0.9)
        self.assertEqual(paired['triage_mean'], 0.45)
        self.assertEqual(paired['mean_delta'], -0.45)
        self.assertEqual(paired['triage_better'], 1)
        self.assertEqual(paired['manual_better'], 1)
        self.assertNotIn('large', json.dumps(result))

    def test_paired_recall_undefined_for_no_positive_reference(self):
        refs, sessions, decisions = self.fixtures()
        for row in refs:
            row['review_worthy'] = 'no'
        paired = score(refs, sessions, decisions)['paired_recall']
        self.assertEqual(paired['eligible_sessions'], 0)
        self.assertEqual(paired['excluded_no_positive_reference'], 1)
        self.assertIsNone(paired['mean_delta'])

    def test_undefined_metrics_when_no_positive_labels(self):
        refs, sessions, decisions = self.fixtures()
        for row in refs:
            row['review_worthy'] = 'no'
        result = score(refs, sessions, decisions)
        self.assertIsNone(result['arms']['triage']['recall'])
        self.assertIsNone(result['arms']['triage']['seconds_per_true_finding'])

    def test_cli_rejects_malformed_csv_and_aggregates_only(self):
        refs, sessions, decisions = self.fixtures()
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for filename, cols, rows in (('references.csv', REF_COLS, refs),
                                         ('sessions.csv', SESSION_COLS, sessions),
                                         ('decisions.csv', DECISION_COLS, decisions)):
                p = Path(td) / filename
                with p.open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=cols)
                    writer.writeheader()
                    writer.writerows(rows)
                paths.append(p)
            script = Path(__file__).resolve().parents[1] / 'tools' / 'seo_sitemap_field_score.py'
            cmd = [sys.executable, str(script), '--references', str(paths[0]),
                   '--sessions', str(paths[1]), '--decisions', str(paths[2])]
            ok = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads(ok.stdout)['arms']['triage']['tp'], 2)
            self.assertNotIn('u1', ok.stdout)
            paths[0].write_text('bad,header\na,b\n', encoding='utf-8')
            bad = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertFalse(bad.stdout)


if __name__ == '__main__':
    unittest.main()
