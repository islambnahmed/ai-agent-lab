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
