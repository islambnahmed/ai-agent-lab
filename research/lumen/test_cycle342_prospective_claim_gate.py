"""Synthetic Gold Lab claim-gate adversarial contract tests; no vendor data used."""
import unittest
from cycle342_prospective_claim_gate import screen


def fixture():
    receipt = {
        'issuedAt': '2026-10-13T01:00:00Z',
        'originDate': '2026-10-12',
        'horizon': 1,
        'point': 2700.0,
        'baseline': 2680.0,
        'originClose': 2680.0,
        'targetDate': None,
        'calendar': 'observations',
        'source': 'synthetic-provider',
    }
    evidence = {
        'receipt_in_anchored_commit_verified': True,
        'anchorObservedAt': '2026-10-13T02:00:00Z',
        'provider': 'synthetic-provider',
        'unit': 'USD per troy ounce',
        'grain': 'daily',
        'original_vintage_verified': True,
        'complete_provider_sequence_independently_verified': True,
        'futureObservedCloses': [{'date': '2026-10-13', 'price': 2690.0}],
        'targetFirstAvailableAt': '2026-10-14T00:30:00Z',
        'provider_timestamp_independently_verified': True,
    }
    return receipt, evidence


class ClaimGateAdversarialTests(unittest.TestCase):
    def test_complete_synthetic_contract_is_screen_eligible_only(self):
        r, e = fixture()
        result = screen(r, e)
        self.assertEqual(result['status'], 'eligible_for_scoring')
        self.assertEqual(result['modelAbsError'], 10.0)
        self.assertEqual(result['baselineAbsError'], 10.0)
        self.assertEqual(result['improvementVsPersistence'], 0.0)
        self.assertIn('not independent', result['caution'])

    def test_unverified_flags_are_never_accepted_as_truthy(self):
        for flag in (
            'receipt_in_anchored_commit_verified',
            'original_vintage_verified',
            'complete_provider_sequence_independently_verified',
            'provider_timestamp_independently_verified',
        ):
            for invalid in ('false', 'yes', 1, [], None, False):
                with self.subTest(flag=flag, invalid=invalid):
                    r, e = fixture()
                    e[flag] = invalid
                    self.assertNotEqual(screen(r, e)['status'], 'eligible_for_scoring')

    def test_receipt_horizon_requires_integer_not_equivalent_float(self):
        for invalid in (1.0, True, '1', None):
            with self.subTest(invalid=invalid):
                r, e = fixture()
                r['horizon'] = invalid
                self.assertEqual(screen(r, e)['status'], 'invalid_receipt')

    def test_receipt_source_must_be_nonempty(self):
        for invalid in (None, '', 1):
            with self.subTest(invalid=invalid):
                r, e = fixture()
                r['source'] = invalid
                e['provider'] = invalid
                self.assertEqual(screen(r, e)['status'], 'invalid_receipt')
        r, e = fixture()
        del r['source']
        del e['provider']
        self.assertEqual(screen(r, e)['status'], 'invalid_receipt')

    def test_provider_mismatch_blocks_eligibility(self):
        r, e = fixture()
        e['provider'] = 'other-provider'
        self.assertEqual(screen(r, e)['status'], 'insufficient_evidence')

    def test_missing_target_observation_blocks_eligibility(self):
        r, e = fixture()
        e['futureObservedCloses'] = []
        self.assertEqual(screen(r, e)['status'], 'insufficient_evidence')

    def test_target_published_before_anchor_blocks_eligibility(self):
        r, e = fixture()
        e['anchorObservedAt'] = '2026-10-15T00:00:00Z'
        self.assertEqual(screen(r, e)['status'], 'insufficient_evidence')

    def test_original_vintage_flag_absent_blocks_eligibility(self):
        r, e = fixture()
        del e['original_vintage_verified']
        self.assertEqual(screen(r, e)['status'], 'insufficient_evidence')


if __name__ == '__main__':
    unittest.main()
