import itertools
import unittest
from dependence_witness import extremal_witnesses
from dependence_bounds import all_fail_bounds


class WitnessTests(unittest.TestCase):
    def assert_witness(self, marginals, pairs):
        result = extremal_witnesses(marginals, pairs)
        expected = all_fail_bounds(marginals, pairs)
        for key, value in zip(('minimum', 'maximum'), expected):
            item = result[key]
            self.assertAlmostEqual(item['allFail'], value, places=9)
            self.assertLessEqual(item['maxResidual'], 1e-8)
            dist = {tuple(map(int, entry['world'])): entry['mass']
                    for entry in item['support']}
            self.assertAlmostEqual(sum(dist.values()), 1, places=9)
            for i, p in enumerate(marginals):
                self.assertAlmostEqual(
                    sum(prob for world, prob in dist.items() if world[i]),
                    p, places=9)
            for (i, j), q in pairs.items():
                self.assertAlmostEqual(
                    sum(prob for world, prob in dist.items()
                        if world[i] and world[j]), q, places=9)
            self.assertAlmostEqual(
                dist.get((1,) * len(marginals), 0), value, places=9)

    def test_four_pairwise_independent_not_mutual(self):
        self.assert_witness([.5] * 4,
                            {(i, j): .25 for i, j in itertools.combinations(range(4), 2)})

    def test_sparse_unequal(self):
        self.assert_witness([.2, .3, .4, .6], {(0, 1): .08, (2, 3): .22})

    def test_degenerate(self):
        self.assert_witness([1, 0, 1], {(0, 1): 0, (0, 2): 1})

    def test_invalid(self):
        with self.assertRaises(ValueError):
            extremal_witnesses([.1, .1], {(0, 1): .2})
        with self.assertRaises(ValueError):
            extremal_witnesses([.5] * 5)


if __name__ == '__main__':
    unittest.main()
