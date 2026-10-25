import unittest
from pit_eval import (Example, Revision, feature_snapshot, walk_forward_folds,
                      synthetic_domain, benchmark, score)


class PointInTimeTests(unittest.TestCase):
    def test_future_revision_is_excluded(self):
        e = Example('a', 10, 1, 12)
        rs = [Revision('a', 9, 9, 1, 0), Revision('a', 9, 11, 2, 1)]
        self.assertEqual(feature_snapshot([e], rs)['a'].value, 0)
        self.assertEqual(feature_snapshot([e], rs, False)['a'].value, 1)

    def test_available_revision_is_allowed(self):
        e = Example('a', 10, 1, 12)
        rs = [Revision('a', 9, 9, 1, 0), Revision('a', 9, 10, 2, 1)]
        self.assertEqual(feature_snapshot([e], rs)['a'].value, 1)

    def test_future_observation_excluded_even_when_backfilled(self):
        e = Example('a', 10, 1, 12)
        rs = [Revision('a', 11, 9, 1, 1)]
        self.assertNotIn('a', feature_snapshot([e], rs, False))

    def test_tie_break_revision(self):
        e = Example('a', 10, 1, 12)
        rs = [Revision('a', 9, 9, 1, 0), Revision('a', 9, 9, 2, 1)]
        self.assertEqual(feature_snapshot([e], rs)['a'].value, 1)

    def test_missing_features_use_prior(self):
        train = [Example('a', 1, 1, 2), Example('b', 2, 1, 3)]
        test = [Example('c', 3, 1, 4)]
        self.assertEqual(score(train, test, {}), (1, 1))

    def test_fold_label_maturity_and_gap(self):
        ex = [Example(str(i), i, i % 2, i+5) for i in range(30)]
        folds = list(walk_forward_folds(ex, min_train=10, test_size=5, gap=2))
        self.assertEqual(len(folds), 4)
        for train, test in folds:
            self.assertTrue(all(e.label_ready_at <= test[0].decision_at for e in train))
            self.assertLess(max(e.decision_at for e in train), test[0].decision_at-1)

    def test_invalid_folds(self):
        with self.assertRaises(ValueError):
            list(walk_forward_folds([Example('a', 1, 1, 1)], min_train=0))
        with self.assertRaises(ValueError):
            list(walk_forward_folds([Example('a', 1, 1, 1), Example('b', 1, 0, 1)], min_train=1))

    def test_duplicate_keys(self):
        with self.assertRaises(ValueError):
            feature_snapshot([Example('a', 1, 0, 2), Example('a', 2, 1, 3)], [])

    def test_no_future_features_on_both_domains(self):
        for domain in ('gold', 'seo'):
            ex, rev = synthetic_domain(domain)
            snaps = feature_snapshot(ex, rev)
            self.assertEqual(len(snaps), len(ex))
            self.assertTrue(all(snaps[e.key].available_at <= e.decision_at for e in ex))

    def test_leakage_counterexample_transfers(self):
        for domain in ('gold', 'seo'):
            r = benchmark(domain)
            self.assertEqual(r['future_revision_fraction'], 1.0)
            self.assertGreater(r['leaky_accuracy']-r['strict_accuracy'], .2)

    def test_deterministic(self):
        self.assertEqual(benchmark('gold'), benchmark('gold'))
        self.assertEqual(benchmark('seo'), benchmark('seo'))

    def test_invalid_domain(self):
        with self.assertRaises(ValueError):
            synthetic_domain('other')


class LeakageControls(unittest.TestCase):
    def test_late_revision_cannot_change_strict_snapshot(self):
        from dataclasses import replace
        examples, revisions = synthetic_domain('seo', 888)
        altered = [replace(r, value=1-r.value) if r.revision == 2 else r for r in revisions]
        self.assertEqual(feature_snapshot(examples, revisions),
                         feature_snapshot(examples, altered))
        self.assertNotEqual(feature_snapshot(examples, revisions, False),
                            feature_snapshot(examples, altered, False))

    def test_negative_control_does_not_inflate_gold(self):
        from stress import negative_control
        control = negative_control('gold', 434)
        self.assertLess(control['leaky'], .65)


if __name__ == '__main__':
    unittest.main()
