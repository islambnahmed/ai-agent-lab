import itertools
import math
import unittest
from cluster_evidence import ClusterAudit, EProcess


class EvidenceTests(unittest.TestCase):
    def test_initial_wealth(self):
        self.assertAlmostEqual(EProcess().log_e, 0)

    def test_reject_bad_alpha(self):
        for a in (0, 1, -0.1, float('nan'), True):
            with self.subTest(a=a), self.assertRaises(ValueError): EProcess(a)

    def test_reject_bad_lambdas(self):
        for ls in ((), (1,), (-0.01,), (float('nan'),), (True,)):
            with self.subTest(ls=ls), self.assertRaises(ValueError): EProcess(lambdas=ls)

    def test_reject_invalid_gains(self):
        e = EProcess()
        for x in (True, None, 1.01, -1.01, float('nan'), float('inf'), '1'):
            with self.subTest(x=x), self.assertRaises(ValueError): e.update(x)
        self.assertEqual(e.n, 0)

    def test_cluster_invalid_is_atomic(self):
        e = ClusterAudit()
        for cluster in ([], [1, 2], [0, float('nan')], [False]):
            with self.subTest(cluster=cluster), self.assertRaises(ValueError): e.add_cluster(cluster)
        self.assertEqual(e.events_seen, 0)
        self.assertEqual(e.clustered.n, 0)
        self.assertEqual(e.event_naive.n, 0)

    def test_cluster_means_equal_one_update(self):
        e = ClusterAudit()
        e.add_cluster([1, -1, 0, 0])
        self.assertEqual(e.clustered.n, 1)
        self.assertEqual(e.event_naive.n, 4)
        self.assertAlmostEqual(e.clustered.log_e, 0)

    def test_singleton_equivalence(self):
        e = ClusterAudit()
        for x in [1, -1, 1, 1, -1, 1]: e.add_cluster([x])
        self.assertAlmostEqual(e.clustered.log_e, e.event_naive.log_e)

    def test_identical_cluster_not_eight_updates(self):
        e = ClusterAudit()
        e.add_cluster([1] * 8)
        self.assertLess(e.clustered.log_e, e.event_naive.log_e)

    def test_exact_fair_coin_expectation(self):
        # Enumerate all independent cluster signs for up to 8 clusters.
        for n in range(1, 9):
            total = 0.
            for seq in itertools.product((-1, 1), repeat=n):
                e = EProcess()
                for x in seq: e.update(x)
                total += math.exp(e.log_e)
            self.assertAlmostEqual(total / 2**n, 1., places=11)

    def test_zero_gain_wealth(self):
        e = EProcess()
        for _ in range(100): e.update(0)
        self.assertAlmostEqual(e.log_e, 0)

    def test_crossing_record_is_first(self):
        e = EProcess()
        for _ in range(50): e.update(1)
        first = e.first_crossing
        self.assertIsNotNone(first)
        for _ in range(50): e.update(-1)
        self.assertEqual(e.first_crossing, first)

    def test_all_negative_never_cross(self):
        e = EProcess()
        for _ in range(100): e.update(-1)
        self.assertIsNone(e.first_crossing)

    def test_cluster_order_irrelevant_to_mean(self):
        a, b = ClusterAudit(), ClusterAudit()
        a.add_cluster([1, 1, -1, 0]); b.add_cluster([-1, 0, 1, 1])
        self.assertAlmostEqual(a.clustered.log_e, b.clustered.log_e)


if __name__ == '__main__': unittest.main()
