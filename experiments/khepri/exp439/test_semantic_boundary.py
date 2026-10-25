import json
import threading
import unittest
from semantic_boundary import (Request, Adapter, BoundExecutor, Rejected,
    REPO, NOTION_ROOT, weak_first_wins, toy_last_wins)

G = lambda **kw: Request('github', REPO, 'create_file',
                         path='experiments/khepri/exp439/report.md',
                         branch='khepri/exp439', payload='safe', **kw)
N = lambda payload: Request('notion', NOTION_ROOT, 'append_child', payload=payload)

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.a = Adapter()
        self.e = BoundExecutor()

    def test_github_normal_execution(self):
        r = G(); p = self.e.issue(r, self.a)
        self.assertTrue(self.e.execute(p, r, self.a))
        self.assertEqual(len(self.e.effects), 1)

    def test_replay_rejected(self):
        r = G(); p = self.e.issue(r, self.a)
        self.assertTrue(self.e.execute(p, r, self.a))
        self.assertFalse(self.e.execute(p, r, self.a))

    def test_payload_change_rejected(self):
        r = G(); p = self.e.issue(r, self.a)
        changed = Request(r.surface, r.target, r.operation, r.path, r.branch, 'changed')
        self.assertFalse(self.e.execute(p, changed, self.a))
        self.assertTrue(self.e.execute(p, r, self.a))

    def test_adapter_version_drift_rejected(self):
        r = G(); p = self.e.issue(r, self.a)
        self.assertFalse(self.e.execute(p, r, Adapter('v2')))
        self.assertTrue(self.e.execute(p, r, self.a))

    def test_percent_encoded_dot_segments_rejected(self):
        r = Request('github', REPO, 'create_file',
                    'experiments/khepri/%2e%2e/%2e%2e/outside.md', 'khepri/exp439', 'x')
        with self.assertRaises(Rejected): self.a.prepare(r)

    def test_literal_dot_segments_rejected(self):
        r = Request('github', REPO, 'create_file',
                    'experiments/khepri/../outside.md', 'khepri/exp439', 'x')
        with self.assertRaises(Rejected): self.a.prepare(r)

    def test_backslash_and_duplicate_separator_rejected(self):
        for path in ('experiments/khepri/..\\outside.md',
                     'experiments/khepri//outside.md'):
            with self.subTest(path=path), self.assertRaises(Rejected):
                self.a.prepare(Request('github', REPO, 'create_file', path, 'khepri/exp439', 'x'))

    def test_non_nfc_path_rejected(self):
        with self.assertRaises(Rejected):
            self.a.prepare(Request('github', REPO, 'create_file',
                        'experiments/khepri/cafe\u0301.md', 'khepri/exp439', 'x'))

    def test_not_allowed_repo_rejected(self):
        with self.assertRaises(Rejected):
            self.a.prepare(Request('github', 'other/repo', 'create_file',
                'experiments/khepri/a.md', 'khepri/exp439', 'x'))

    def test_duplicate_json_top_level_rejected(self):
        with self.assertRaises(Rejected):
            self.a.prepare(N('{"kind":"paragraph","kind":"image","text":"ok"}'))

    def test_duplicate_json_nested_rejected(self):
        with self.assertRaises(Rejected):
            self.a.prepare(N('{"kind":"paragraph","text":"ok","nested":{"a":1,"a":2}}'))

    def test_json_reordering_semantically_equivalent(self):
        a = self.a.prepare(N('{"kind":"paragraph","text":"hello"}'))
        b = self.a.prepare(N('{"text":"hello", "kind":"paragraph"}'))
        self.assertEqual(a.digest(), b.digest())

    def test_not_accepted_nonfinite(self):
        with self.assertRaises(Rejected):
            self.a.prepare(N('{"kind":"paragraph","text":"x","other":NaN}'))

    def test_not_accepted_unknown_schema(self):
        with self.assertRaises(Rejected):
            self.a.prepare(N('{"kind":"command","text":"hi"}'))

    def test_invalid_unicode_rejected_without_crashing(self):
        with self.assertRaises(Rejected):
            self.a.prepare(N('{"kind":"paragraph","text":"\\ud800"}'))

    def test_excessive_json_rejected(self):
        with self.assertRaises(Rejected):
            self.a.prepare(N('{"kind":"paragraph","text":"' + 'x'*70000 + '"}'))

    def test_expiry(self):
        now = [10]
        ex = BoundExecutor(clock=lambda: now[0])
        r = G(); p = ex.issue(r, self.a, ttl=2)
        now[0] = 13
        self.assertFalse(ex.execute(p, r, self.a))

    def test_concurrent_replay_only_once(self):
        r = G(); p = self.e.issue(r, self.a)
        results = []
        lock = threading.Lock()
        def worker():
            v = self.e.execute(p, r, self.a)
            with lock: results.append(v)
        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 49)

    def test_weak_first_wins_vs_last_wins_counterexample(self):
        raw = '{"kind":"paragraph","kind":"command","text":"hello"}'
        self.assertEqual(weak_first_wins(raw)['kind'], 'paragraph')
        self.assertEqual(toy_last_wins(raw)['kind'], 'command')
        with self.assertRaises(Rejected): self.a.prepare(N(raw))

    def test_crash_window_not_solved(self):
        r = G(); p = self.e.issue(r, self.a)
        self.assertTrue(self.e.execute(p, r, self.a))
        # Simulated crash after permit consumed but before a real external write.
        self.e.effects.clear()
        self.assertFalse(self.e.execute(p, r, self.a))
        self.assertEqual(self.e.effects, [])

if __name__ == '__main__': unittest.main()
