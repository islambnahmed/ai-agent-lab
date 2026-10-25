import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from bound_execution import Action, Permit, Gate, REPO, DRIVE_ROOT, NOTION_ROOT, naive_execute

class FakeClock:
    def __init__(self, t=0): self.t=t
    def __call__(self): return self.t

BASE = [
    Action('github','create_file',REPO,'experiments/khepri/exp438/note.md','khepri/exp438','safe'),
    Action('drive','create_file',DRIVE_ROOT,'lab-note.md','','safe'),
    Action('notion','append_child',NOTION_ROOT,'','','safe'),
]

class BoundExecutionTests(unittest.TestCase):
    def test_valid_each_surface(self):
        for a in BASE:
            with self.subTest(a=a):
                g=Gate(clock=FakeClock()); p=g.issue(a)
                self.assertIsNotNone(p)
                self.assertTrue(g.execute(p,a))
                self.assertEqual(g.executed,[a])

    def test_payload_swap_blocked_but_naive_accepts(self):
        for a in BASE:
            with self.subTest(a=a):
                g=Gate(clock=FakeClock()); p=g.issue(a)
                b=replace(a,payload='UNREVIEWED')
                self.assertTrue(naive_execute(a,b))
                self.assertFalse(g.execute(p,b))
                self.assertTrue(g.execute(p,a))

    def test_authorized_target_swap_blocked(self):
        a=BASE[0]; b=replace(a,path='experiments/khepri/exp438/other.md')
        self.assertTrue(naive_execute(a,b)); self.assertTrue(naive_execute(b,a))
        g=Gate(clock=FakeClock()); p=g.issue(a)
        self.assertFalse(g.execute(p,b))
        self.assertTrue(g.execute(p,a))

    def test_branch_swap_blocked(self):
        a=BASE[0]; b=replace(a,branch='khepri/another')
        g=Gate(clock=FakeClock()); p=g.issue(a)
        self.assertFalse(g.execute(p,b))

    def test_cross_surface_swap_blocked(self):
        g=Gate(clock=FakeClock()); p=g.issue(BASE[0])
        self.assertFalse(g.execute(p,BASE[1]))

    def test_replay_denied(self):
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        self.assertTrue(g.execute(p,a)); self.assertFalse(g.execute(p,a))

    def test_expiry_denied(self):
        a=BASE[0]; clock=FakeClock(); g=Gate(clock=clock); p=g.issue(a,ttl=5)
        clock.t=6
        self.assertFalse(g.execute(p,a))
        clock.t=5
        self.assertTrue(g.execute(p,a))

    def test_revision_change_denied(self):
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        g.policy_revision+=1
        self.assertFalse(g.execute(p,a))

    def test_forged_token_denied(self):
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        forged=replace(p,token='forged')
        self.assertFalse(g.execute(forged,a)); self.assertTrue(g.execute(p,a))

    def test_forged_digest_denied(self):
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        self.assertFalse(g.execute(replace(p,digest='0'*64),a))

    def test_unauthorized_issuance_denied(self):
        g=Gate(clock=FakeClock())
        self.assertIsNone(g.issue(replace(BASE[0],branch='main')))
        self.assertIsNone(g.issue(replace(BASE[0],target='other/repo')))

    def test_concurrent_exactly_one(self):
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        with ThreadPoolExecutor(max_workers=20) as pool:
            results=list(pool.map(lambda _: g.execute(p,a),range(100)))
        self.assertEqual(sum(results),1)
        self.assertEqual(len(g.executed),1)

    def test_crash_between_permit_consumption_and_external_effect_loses_action(self):
        # In production, consuming the permit cannot atomically commit a remote side effect.
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        self.assertTrue(g.execute(p,a))  # simulated permission consumption
        remote_effects=[]                 # crash before remote write
        self.assertFalse(g.execute(p,a)) # retry blocked; effect is lost
        self.assertEqual(remote_effects,[])

    def test_mutated_fields_fail(self):
        a=BASE[0]; g=Gate(clock=FakeClock()); p=g.issue(a)
        mutations={'surface':'drive','operation':'delete_file','target':'other/repo',
                   'path':'experiments/khepri/exp438/other.md',
                   'branch':'khepri/other','payload':'altered'}
        for field,value in mutations.items():
            with self.subTest(field=field):
                self.assertFalse(g.execute(p,replace(a,**{field:value})))
        self.assertTrue(g.execute(p,a))

if __name__=='__main__': unittest.main(verbosity=2)
