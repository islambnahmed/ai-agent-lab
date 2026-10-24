"""Exp419: cross-review of exp418 and exact-plan-type mitigation."""
import unittest
from plan_guard import new_guard_runtime  # adds the two sibling experiment dirs
from approval_receipts import Plan, REPO, BRANCH, PREFIX, new_runtime, in_scope
from identity_receipts import new_strict_runtime

PAYLOAD = b'fixed-approved-bytes'


def plan(suffix):
    return Plan('write', REPO, BRANCH, PREFIX + suffix)


class AlwaysEqualPlan(Plan):
    def __eq__(self, other):
        return True


class ExplodingEqualPlan(Plan):
    def __eq__(self, other):
        raise RuntimeError('untrusted plan equality invoked')


class PlanGuardTests(unittest.TestCase):
    def test_exact_original_blob_fixture_is_loaded(self):
        self.assertTrue(in_scope(plan('approved.txt')))

    def test_original_subclass_redirects_action(self):
        issuer, executor = new_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        attack = AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + 'redirected.txt')
        self.assertTrue(in_scope(attack))
        result = executor.simulate(receipt, attack, PAYLOAD)
        self.assertTrue(result.accepted)
        self.assertEqual(result.simulated_action[-1], PREFIX + 'redirected.txt')

    def test_exp418_strict_receipt_still_redirects_action(self):
        issuer, executor = new_strict_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        attack = AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + 'redirected.txt')
        result = executor.simulate(receipt, attack, PAYLOAD)
        self.assertTrue(result.accepted)
        self.assertEqual(result.simulated_action[-1], PREFIX + 'redirected.txt')

    def test_guard_rejects_redirect_and_consumes_receipt(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        attack = AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + 'redirected.txt')
        self.assertFalse(executor.simulate(receipt, attack, PAYLOAD).accepted)
        self.assertFalse(executor.simulate(receipt, plan('approved.txt'), PAYLOAD).accepted)

    def test_guard_valid_action_works_once(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        result = executor.simulate(receipt, plan('approved.txt'), PAYLOAD)
        self.assertTrue(result.accepted)
        self.assertEqual(result.simulated_action[-1], PREFIX + 'approved.txt')
        self.assertFalse(executor.simulate(receipt, plan('approved.txt'), PAYLOAD).accepted)

    def test_original_and_exp418_invoke_malicious_plan_equality(self):
        attack = ExplodingEqualPlan('write', REPO, BRANCH, PREFIX + 'other.txt')
        for factory in (new_runtime, new_strict_runtime):
            with self.subTest(factory=factory.__name__):
                issuer, executor = factory()
                receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
                with self.assertRaisesRegex(RuntimeError, 'untrusted plan equality'):
                    executor.simulate(receipt, attack, PAYLOAD)

    def test_guard_never_invokes_malicious_plan_equality(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        attack = ExplodingEqualPlan('write', REPO, BRANCH, PREFIX + 'other.txt')
        self.assertFalse(executor.simulate(receipt, attack, PAYLOAD).accepted)

    def test_guard_issuer_rejects_plan_subclass(self):
        issuer, _ = new_guard_runtime()
        with self.assertRaises(TypeError):
            issuer.issue(AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + 'approved.txt'), PAYLOAD)

    def test_original_issuer_accepts_plan_subclass(self):
        issuer, executor = new_runtime()
        receipt = issuer.issue(AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + 'approved.txt'), PAYLOAD)
        self.assertIs(type(receipt), object)
        self.assertTrue(executor.simulate(receipt, plan('approved.txt'), PAYLOAD).accepted)

    def test_original_and_exp418_allow_post_issue_plan_mutation(self):
        for factory in (new_runtime, new_strict_runtime):
            with self.subTest(factory=factory.__name__):
                approved = plan('approved.txt')
                issuer, executor = factory()
                receipt = issuer.issue(approved, PAYLOAD)
                # Python frozen dataclass is not a trust boundary.
                object.__setattr__(approved, 'path', PREFIX + 'redirected.txt')
                result = executor.simulate(receipt, plan('redirected.txt'), PAYLOAD)
                self.assertTrue(result.accepted)
                self.assertEqual(result.simulated_action[-1], PREFIX + 'redirected.txt')

    def test_guard_snapshots_plan_at_issue_time(self):
        approved = plan('approved.txt')
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(approved, PAYLOAD)
        object.__setattr__(approved, 'path', PREFIX + 'redirected.txt')
        self.assertFalse(executor.simulate(receipt, plan('redirected.txt'), PAYLOAD).accepted)
        fresh = issuer.issue(plan('approved.txt'), PAYLOAD)
        self.assertTrue(executor.simulate(fresh, plan('approved.txt'), PAYLOAD).accepted)

    def test_guard_rejects_receipt_subclass_before_hash(self):
        class ExplodingHash:
            def __hash__(self):
                raise RuntimeError('untrusted hash')
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        self.assertFalse(executor.simulate(ExplodingHash(), plan('approved.txt'), PAYLOAD).accepted)
        self.assertTrue(executor.simulate(receipt, plan('approved.txt'), PAYLOAD).accepted)

    def test_guard_wrong_payload_consumes(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        self.assertFalse(executor.simulate(receipt, plan('approved.txt'), b'wrong').accepted)
        self.assertFalse(executor.simulate(receipt, plan('approved.txt'), PAYLOAD).accepted)

    def test_guard_invalid_plan_type_consumes(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        self.assertFalse(executor.simulate(receipt, None, PAYLOAD).accepted)
        self.assertFalse(executor.simulate(receipt, plan('approved.txt'), PAYLOAD).accepted)

    def test_guard_rejects_plain_different_path(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        self.assertFalse(executor.simulate(receipt, plan('other.txt'), PAYLOAD).accepted)

    def test_guard_rejects_out_of_scope_path(self):
        issuer, executor = new_guard_runtime()
        receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
        self.assertFalse(executor.simulate(receipt, Plan('write', REPO, BRANCH, '../escape'), PAYLOAD).accepted)

    def test_transfer_two_domain_labels(self):
        for suffix in ('seo_html.txt', 'gold_feed.txt'):
            with self.subTest(suffix=suffix):
                issuer, executor = new_guard_runtime()
                receipt = issuer.issue(plan('approved.txt'), PAYLOAD)
                attack = AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + suffix)
                self.assertFalse(executor.simulate(receipt, attack, PAYLOAD).accepted)
                issuer2, executor2 = new_guard_runtime()
                receipt2 = issuer2.issue(plan(suffix), PAYLOAD)
                self.assertTrue(executor2.simulate(receipt2, plan(suffix), PAYLOAD).accepted)


if __name__ == '__main__':
    unittest.main()
