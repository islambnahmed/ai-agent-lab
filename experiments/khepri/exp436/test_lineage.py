import random
import unittest
from lineage import Artifact, Revision, ProvenanceError, choose_revision, lineage_ready, guarded_join


class LineageTests(unittest.TestCase):
    def test_backdated_revision_leaks_under_effective_only(self):
        rs = [Revision('old', 1, 1, 0, 'a'), Revision('new', 1, 11, 1, 'b')]
        self.assertEqual(choose_revision(rs, 10, enforce_capture=False).selected_alias, 'b')
        self.assertEqual(choose_revision(rs, 10, enforce_capture=True).selected_alias, 'a')

    def test_valid_late_capture_not_eligible(self):
        rs = [Revision('late', 0, 11, 0, 'a')]
        self.assertIsNone(choose_revision(rs, 10, enforce_capture=True))

    def test_early_capture_future_effective_not_eligible(self):
        rs = [Revision('future', 11, 1, 0, 'a')]
        self.assertIsNone(choose_revision(rs, 10, enforce_capture=True))

    def test_tie_breaker_deterministic(self):
        rs = [Revision('x', 2, 1, 0, 'a'), Revision('y', 2, 1, 1, 'b')]
        self.assertEqual(choose_revision(rs, 10, enforce_capture=True).selected_alias, 'b')

    def test_descendant_cannot_backdate_parent(self):
        nodes = {'raw': Artifact('raw', 1), 'map': Artifact('map', 12),
                 'join': Artifact('join', 2, ('raw', 'map'))}
        self.assertEqual(lineage_ready(nodes, 'join', 10), (False, 12))

    def test_future_effective_dependency_rejected_even_if_captured_early(self):
        nodes = {'raw': Artifact('raw', 1, (), 11),
                 'join': Artifact('join', 2, ('raw',))}
        self.assertEqual(lineage_ready(nodes, 'join', 10), (False, 11))

    def test_fallback_to_older_complete_lineage(self):
        rs = [Revision('old', 1, 1, 0, 'a'), Revision('new', 2, 2, 0, 'b')]
        nodes = {'raw': Artifact('raw', 1), 'late': Artifact('late', 11),
                 'join_old': Artifact('join_old', 2, ('raw',)),
                 'join_new': Artifact('join_new', 2, ('raw', 'late'))}
        self.assertEqual(guarded_join(rs, nodes, 10), 'a')

    def test_missing_parent_fails_closed(self):
        with self.assertRaisesRegex(ProvenanceError, 'missing'):
            lineage_ready({'join': Artifact('join', 1, ('missing',))}, 'join', 10)

    def test_cycle_fails_closed(self):
        nodes = {'a': Artifact('a', 1, ('b',)), 'b': Artifact('b', 1, ('a',))}
        with self.assertRaisesRegex(ProvenanceError, 'cycle'):
            lineage_ready(nodes, 'a', 10)

    def test_negative_time_fails_closed(self):
        with self.assertRaisesRegex(ProvenanceError, 'negative'):
            lineage_ready({'a': Artifact('a', -1)}, 'a', 10)

    def test_guarded_join_uses_lineage_not_only_mapping_capture(self):
        rs = [Revision('old', 1, 1, 0, 'a')]
        nodes = {'raw': Artifact('raw', 1), 'external': Artifact('external', 12),
                 'join_old': Artifact('join_old', 1, ('raw', 'external'))}
        self.assertIsNone(guarded_join(rs, nodes, 10))

    def test_guarded_join_accepts_complete_early_provenance(self):
        rs = [Revision('old', 1, 1, 0, 'a')]
        nodes = {'raw': Artifact('raw', 1), 'map': Artifact('map', 1),
                 'join_old': Artifact('join_old', 2, ('raw', 'map'))}
        self.assertEqual(guarded_join(rs, nodes, 10), 'a')

    def test_false_capture_is_undetectable_without_trust(self):
        rs = [Revision('forged', 1, 1, 0, 'b')]
        nodes = {'raw': Artifact('raw', 1), 'map': Artifact('map', 1),
                 'join_forged': Artifact('join_forged', 1, ('raw', 'map'))}
        # In the real world the map first existed at 11, but all supplied
        # timestamps are forged as 1. This guard cannot authenticate them.
        self.assertEqual(guarded_join(rs, nodes, 10), 'b')

    def test_random_dag_max_parent_capture_property(self):
        rng = random.Random(436)
        for _ in range(2000):
            n = rng.randint(1, 30)
            nodes = {}
            captures = []
            for i in range(n):
                parents = tuple('n'+str(p) for p in range(i) if rng.random() < .13)
                captured = rng.randrange(30)
                nodes['n'+str(i)] = Artifact('n'+str(i), captured, parents)
                captures.append(max([captured]+[captures[int(p[1:])] for p in parents]))
            cutoff = rng.randrange(30)
            self.assertEqual(lineage_ready(nodes, 'n'+str(n-1), cutoff),
                             (captures[-1] <= cutoff, captures[-1]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
