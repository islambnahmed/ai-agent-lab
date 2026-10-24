import unittest
from state_bound import FakeStore, Approver, Plan, REPO, BRANCH, PREFIX, plan, in_scope


class StateBoundTests(unittest.TestCase):
    def setup_case(self, guarded=True):
        store = FakeStore()
        p = plan()
        store.seed(p.path, b'original')
        approver = Approver(store, bind_version=guarded)
        return store, p, approver

    def test_scope(self):
        self.assertTrue(in_scope(plan()))
        self.assertFalse(in_scope(Plan('delete', REPO, BRANCH, plan().path)))
        self.assertFalse(in_scope(Plan('write', REPO, BRANCH, '../escape')))
        self.assertFalse(in_scope(plan('../escape')))

    def test_no_interference_both_succeed(self):
        for guarded in (False, True):
            with self.subTest(guarded=guarded):
                s, p, a = self.setup_case(guarded)
                t = a.issue(p, b'agent')
                self.assertTrue(a.redeem(t, p, b'agent').accepted)
                self.assertEqual(s.snapshot(p.path), (b'agent', 2))

    def test_baseline_overwrites_intervening_edit(self):
        s, p, a = self.setup_case(False)
        t = a.issue(p, b'agent')
        s.seed(p.path, b'peer')
        self.assertTrue(a.redeem(t, p, b'agent').accepted)
        self.assertEqual(s.snapshot(p.path)[0], b'agent')

    def test_guard_rejects_intervening_edit(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        s.seed(p.path, b'peer')
        self.assertEqual(a.redeem(t, p, b'agent').reason, 'stale resource version')
        self.assertEqual(s.snapshot(p.path), (b'peer', 2))

    def test_guard_detects_aba(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        s.seed(p.path, b'peer')
        s.seed(p.path, b'original')
        self.assertFalse(a.redeem(t, p, b'agent').accepted)
        self.assertEqual(s.snapshot(p.path), (b'original', 3))

    def test_baseline_misses_aba(self):
        s, p, a = self.setup_case(False)
        t = a.issue(p, b'agent')
        s.seed(p.path, b'peer')
        s.seed(p.path, b'original')
        self.assertTrue(a.redeem(t, p, b'agent').accepted)

    def test_unrelated_resource_change_does_not_block(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        s.seed(plan('other.txt').path, b'peer')
        self.assertTrue(a.redeem(t, p, b'agent').accepted)

    def test_replay_fails(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        self.assertTrue(a.redeem(t, p, b'agent').accepted)
        self.assertFalse(a.redeem(t, p, b'agent').accepted)

    def test_bad_payload_consumes(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        self.assertFalse(a.redeem(t, p, b'wrong').accepted)
        self.assertFalse(a.redeem(t, p, b'agent').accepted)

    def test_bad_plan_consumes(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        self.assertFalse(a.redeem(t, plan('other.txt'), b'agent').accepted)
        self.assertFalse(a.redeem(t, p, b'agent').accepted)

    def test_mutated_approved_plan_does_not_redirect(self):
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        object.__setattr__(p, 'path', plan('other.txt').path)
        self.assertFalse(a.redeem(t, p, b'agent').accepted)

    def test_subclass_rejected(self):
        class WeirdPlan(Plan):
            def __eq__(self, other):
                return True
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        self.assertFalse(a.redeem(t, WeirdPlan('write', REPO, BRANCH, plan('other.txt').path), b'agent').accepted)

    def test_invalid_receipt_does_not_consume_valid(self):
        class BadHash:
            def __hash__(self):
                raise AssertionError('must not hash')
        s, p, a = self.setup_case(True)
        t = a.issue(p, b'agent')
        self.assertFalse(a.redeem(BadHash(), p, b'agent').accepted)
        self.assertTrue(a.redeem(t, p, b'agent').accepted)

    def test_nonbytes_rejected(self):
        s, p, a = self.setup_case(True)
        with self.assertRaises(ValueError):
            a.issue(p, bytearray(b'agent'))

    def test_missing_resource_version_zero(self):
        s = FakeStore()
        p = plan('new.txt')
        a = Approver(s, bind_version=True)
        t = a.issue(p, b'new')
        self.assertTrue(a.redeem(t, p, b'new').accepted)
        self.assertEqual(s.snapshot(p.path), (b'new', 1))

    def test_missing_resource_race(self):
        s = FakeStore()
        p = plan('new.txt')
        a = Approver(s, bind_version=True)
        t = a.issue(p, b'new')
        s.seed(p.path, b'peer-created')
        self.assertFalse(a.redeem(t, p, b'new').accepted)
        self.assertEqual(s.snapshot(p.path)[0], b'peer-created')

    def test_two_approvals_same_version_only_one_succeeds(self):
        s, p, a = self.setup_case(True)
        t1 = a.issue(p, b'one')
        t2 = a.issue(p, b'two')
        self.assertTrue(a.redeem(t1, p, b'one').accepted)
        self.assertFalse(a.redeem(t2, p, b'two').accepted)
        self.assertEqual(s.snapshot(p.path)[0], b'one')


if __name__ == '__main__':
    unittest.main()
