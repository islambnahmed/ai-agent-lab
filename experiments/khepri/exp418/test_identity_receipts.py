"""Reproducible cross-review tests against exp417 original and exp418 adapter."""
import random
import unittest
from identity_receipts import new_runtime, new_strict_runtime
from approval_receipts import Plan, REPO, BRANCH, PREFIX

PLAN = Plan('write', REPO, BRANCH, PREFIX + 'approved.txt')
PAYLOAD = b'approved content'


class EqualImpostor:
    """Requires the receipt hash; never holds or passes the receipt itself."""
    def __init__(self, leaked_hash):
        self.leaked_hash = leaked_hash
    def __hash__(self):
        return self.leaked_hash
    def __eq__(self, other):
        return True


class ExplodingHash:
    def __hash__(self):
        raise RuntimeError('untrusted hash executed')


class ExplodingEq:
    def __init__(self, leaked_hash):
        self.leaked_hash = leaked_hash
    def __hash__(self):
        return self.leaked_hash
    def __eq__(self, other):
        raise RuntimeError('untrusted equality executed')


class ReceiptIdentityTests(unittest.TestCase):
    def test_original_accepts_forged_equal_key(self):
        issuer, executor = new_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        fake = EqualImpostor(hash(receipt))
        self.assertIsNot(fake, receipt)
        self.assertTrue(executor.simulate(fake, PLAN, PAYLOAD).accepted)
        self.assertFalse(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_strict_rejects_forged_equal_key_and_keeps_legitimate_receipt(self):
        issuer, executor = new_strict_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        self.assertFalse(executor.simulate(EqualImpostor(hash(receipt)), PLAN, PAYLOAD).accepted)
        self.assertTrue(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_original_unhashable_crashes(self):
        issuer, executor = new_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        with self.assertRaises(TypeError):
            executor.simulate([], PLAN, PAYLOAD)
        self.assertTrue(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_strict_unhashable_fails_closed(self):
        issuer, executor = new_strict_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        self.assertFalse(executor.simulate([], PLAN, PAYLOAD).accepted)
        self.assertTrue(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_original_calls_untrusted_hash(self):
        issuer, executor = new_runtime()
        issuer.issue(PLAN, PAYLOAD)  # nonempty dict forces key hashing
        with self.assertRaisesRegex(RuntimeError, 'untrusted hash'):
            executor.simulate(ExplodingHash(), PLAN, PAYLOAD)

    def test_strict_never_calls_untrusted_hash(self):
        _, executor = new_strict_runtime()
        self.assertFalse(executor.simulate(ExplodingHash(), PLAN, PAYLOAD).accepted)

    def test_original_calls_untrusted_equality(self):
        issuer, executor = new_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        with self.assertRaisesRegex(RuntimeError, 'untrusted equality'):
            executor.simulate(ExplodingEq(hash(receipt)), PLAN, PAYLOAD)

    def test_strict_never_calls_untrusted_equality(self):
        issuer, executor = new_strict_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        self.assertFalse(executor.simulate(ExplodingEq(hash(receipt)), PLAN, PAYLOAD).accepted)
        self.assertTrue(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_forged_key_rejected_across_two_domains(self):
        for label in ('github_issue', 'seo_html'):
            with self.subTest(domain=label):
                issuer, executor = new_strict_runtime()
                payload = label.encode()
                receipt = issuer.issue(PLAN, payload)
                self.assertFalse(executor.simulate(EqualImpostor(hash(receipt)), PLAN, payload).accepted)
                self.assertTrue(executor.simulate(receipt, PLAN, payload).accepted)

    def test_replay_rejected(self):
        issuer, executor = new_strict_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        self.assertTrue(executor.simulate(receipt, PLAN, PAYLOAD).accepted)
        self.assertFalse(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_wrong_payload_consumes_real_receipt(self):
        issuer, executor = new_strict_runtime()
        receipt = issuer.issue(PLAN, PAYLOAD)
        self.assertFalse(executor.simulate(receipt, PLAN, b'wrong').accepted)
        self.assertFalse(executor.simulate(receipt, PLAN, PAYLOAD).accepted)

    def test_random_forgery_property(self):
        rng = random.Random(418)
        for _ in range(2000):
            issuer, executor = new_strict_runtime()
            payload = rng.randbytes(rng.randrange(0, 80))
            receipt = issuer.issue(PLAN, payload)
            self.assertFalse(executor.simulate(EqualImpostor(hash(receipt)), PLAN, payload).accepted)
            self.assertTrue(executor.simulate(receipt, PLAN, payload).accepted)


if __name__ == '__main__':
    unittest.main()
