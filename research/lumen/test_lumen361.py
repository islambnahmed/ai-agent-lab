import copy
import random
import unittest
from lumen360 import Group, InvalidEvidence, robust_bounds
from lumen361 import (snapshot_payload, digest_snapshot, verify_snapshot,
                      audited_bounds, counterexample)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.entities = tuple('ABCDEF')
        self.groups = [Group('g1', ('A','B'), 'count', 1),
                       Group('g2', ('B','C'), 'or', 1)]
        self.snapshot = snapshot_payload(self.entities, self.groups, frame_version='v1')
        self.digest = digest_snapshot(self.snapshot)

    def test_canonical_permutation_invariance(self):
        p = snapshot_payload(tuple(reversed(self.entities)),
                             [Group(g.name, tuple(reversed(g.members)), g.kind, g.value)
                              for g in reversed(self.groups)], frame_version='v1')
        self.assertEqual(p, self.snapshot)
        self.assertEqual(digest_snapshot(p), self.digest)

    def test_value_changes_not_part_of_membership_commitment(self):
        modified = [Group(g.name, g.members, g.kind, 0) for g in self.groups]
        self.assertEqual(digest_snapshot(snapshot_payload(self.entities, modified,
                                                           frame_version='v1')), self.digest)

    def test_report_values_used_after_commitment(self):
        actual = audited_bounds(self.snapshot, self.digest, self.groups)
        expected = robust_bounds(self.entities, self.groups)
        self.assertEqual((actual['min_errors'], actual['max_errors']),
                         (expected['min_errors'], expected['max_errors']))

    def test_wrong_anchor_rejected(self):
        with self.assertRaisesRegex(InvalidEvidence, 'trusted digest'):
            audited_bounds(self.snapshot, '0'*64, self.groups)

    def test_membership_swap_rejected(self):
        changed = [self.groups[0], Group('g2', ('A','C'), 'or', 1)]
        with self.assertRaisesRegex(InvalidEvidence, 'membership'):
            audited_bounds(self.snapshot, self.digest, changed)

    def test_group_kind_change_rejected(self):
        changed = [self.groups[0], Group('g2', ('B','C'), 'count', 1)]
        with self.assertRaisesRegex(InvalidEvidence, 'membership/kind'):
            audited_bounds(self.snapshot, self.digest, changed)

    def test_extra_group_rejected(self):
        with self.assertRaisesRegex(InvalidEvidence, 'group set'):
            audited_bounds(self.snapshot, self.digest,
                           self.groups + [Group('g3', ('E',), 'or', 0)])

    def test_missing_group_rejected(self):
        with self.assertRaisesRegex(InvalidEvidence, 'group set'):
            audited_bounds(self.snapshot, self.digest, self.groups[:1])

    def test_frame_version_change_rejected(self):
        p = copy.deepcopy(self.snapshot)
        p['frame_version'] = 'v2'
        with self.assertRaisesRegex(InvalidEvidence, 'trusted digest'):
            audited_bounds(p, self.digest, self.groups)

    def test_noncanonical_payload_rejected(self):
        p = copy.deepcopy(self.snapshot)
        p['entities'].reverse()
        with self.assertRaisesRegex(InvalidEvidence, 'canonical'):
            verify_snapshot(p, self.digest)

    def test_extra_snapshot_metadata_rejected(self):
        p = copy.deepcopy(self.snapshot)
        p['timestamp'] = 'fake-before-outcomes'
        with self.assertRaisesRegex(InvalidEvidence, 'malformed'):
            verify_snapshot(p, self.digest)

    def test_duplicate_member_rejected(self):
        with self.assertRaises(InvalidEvidence):
            snapshot_payload(self.entities, [Group('g1', ('A','A'), 'count', 0)], frame_version='v1')

    def test_unknown_entity_rejected(self):
        with self.assertRaises(InvalidEvidence):
            snapshot_payload(self.entities, [Group('g1', ('A','Z'), 'or', 1)], frame_version='v1')

    def test_malformed_report_value_rejected_even_with_corruption_budget(self):
        bad = [Group('g1', ('A','B'), 'count', 4), self.groups[1]]
        with self.assertRaises(InvalidEvidence):
            audited_bounds(self.snapshot, self.digest, bad, max_corrupt_values=2)

    def test_corrupt_value_budget_matches_base_solver(self):
        for k in (0, 1, 2):
            actual = audited_bounds(self.snapshot, self.digest, self.groups,
                                    max_corrupt_values=k)
            expected = robust_bounds(self.entities, self.groups, max_corrupt=k)
            self.assertEqual((actual['min_errors'], actual['max_errors']),
                             (expected['min_errors'], expected['max_errors']))

    def test_real_attack_rejected_but_self_signed_forgery_passes(self):
        result = counterexample()
        self.assertEqual(result['authentic_rate'], [0.5, 0.5])
        self.assertEqual(result['tampered_unanchored_rate'], [1/6, 1/6])
        self.assertEqual(result['self_signed_forgery_accepted_rate'], [1/6, 1/6])
        self.assertIn('membership', result['independently_anchored_tamper_rejection'])

    def test_randomized_equivalence_250(self):
        rng = random.Random(361)
        for i in range(250):
            n = rng.randrange(2, 9)
            entities = tuple(f'e{j}' for j in range(n))
            truth = {e:rng.randrange(2) for e in entities}
            groups = []
            for j in range(rng.randrange(1, 8)):
                members = tuple(sorted(rng.sample(entities, rng.randint(1, n))))
                kind = rng.choice(('or','count'))
                val = sum(truth[x] for x in members)
                if kind == 'or': val = int(val > 0)
                groups.append(Group(f'g{j}', members, kind, val))
            p = snapshot_payload(entities, groups, frame_version=f'v{i}')
            for k in (0, 1):
                a = audited_bounds(p, digest_snapshot(p), groups, max_corrupt_values=k)
                b = robust_bounds(entities, groups, max_corrupt=k)
                self.assertEqual((a['min_errors'],a['max_errors']),
                                 (b['min_errors'],b['max_errors']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
