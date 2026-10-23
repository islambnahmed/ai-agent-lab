"""No-network behavioral and input-boundary tests for the inventory audit."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from offline_robots_inventory_audit import audit, _origin

ROBOTS = '''User-agent: *\nDisallow: /private\nAllow: /private/public\n'''


class InventoryAuditTests(unittest.TestCase):
    def test_mixed_inventory_prioritized_and_origin_bound(self):
        items = [
            {'url': 'https://example.com/private/a', 'segment': 'sales', 'organic_clicks_30d': 60},
            {'url': '/private/public/a', 'segment': 'sales', 'organic_clicks_30d': 10},
            {'url': 'https://evil.example/private/a', 'segment': 'sales', 'organic_clicks_30d': 90},
            {'url': '/about', 'segment': 'info', 'organic_clicks_30d': 4},
            {'url': '/private/a', 'segment': 'sales', 'organic_clicks_30d': 20},
            {'url': '/bad%QQ', 'segment': 'info', 'organic_clicks_30d': 7},
        ]
        report = audit(ROBOTS, 'https://example.com', 'Googlebot', items)
        self.assertEqual(report['summary'], {
            'input_rows': 6, 'unique_rows': 5, 'duplicate_rows_ignored': 1,
            'allowed': 2, 'disallowed': 1, 'unknown': 1, 'out_of_scope': 1,
            'flagged_organic_clicks_30d': 67,
        })
        self.assertEqual([r['status'] for r in report['review_queue']], ['disallowed', 'unknown'])
        self.assertEqual(report['segments']['sales']['disallowed'], 1)
        self.assertEqual(report['segments']['sales']['flagged_organic_clicks_30d'], 60)

    def test_default_ports_equivalent_and_protocol_not_equivalent(self):
        r = audit(ROBOTS, 'https://example.com', 'Googlebot', [
            {'url': 'https://example.com:443/private'},
            {'url': 'http://example.com/private'},
        ])
        self.assertEqual([x['status'] for x in r['rows']], ['disallowed', 'out_of_scope'])

    def test_relative_network_path_not_accepted(self):
        r = audit(ROBOTS, 'https://example.com', 'Googlebot', [{'url': '//evil.com/private'}])
        self.assertEqual(r['rows'][0]['status'], 'unknown')

    def test_invalid_origin_rejected(self):
        for origin in ['https://example.com/robots.txt', 'https://example.com?x=1',
                       'https://user@example.com', 'ftp://example.com', 'https://exa mple.com',
                       'https://example.com:99999', 'https://example.com:0', 'https://bad-.example']:
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                _origin(origin)

    def test_invalid_clicks_and_token_rejected(self):
        for clicks in [True, -1, 1.5, '30', 10**10]:
            with self.subTest(clicks=clicks), self.assertRaises(ValueError):
                audit(ROBOTS, 'https://example.com', 'Googlebot', [{'url': '/a', 'organic_clicks_30d': clicks}])
        with self.assertRaises(ValueError):
            audit(ROBOTS, 'https://example.com', 'Google bot', [{'url': '/a'}])

    def test_bad_urls_abstain(self):
        urls = ['https://example.com:bad/private', 'https://example.com\\evil.com/private',
                'https://example.com/private#fragment', '/a\n/b', '/a#fragment', 'javascript:alert(1)']
        r = audit(ROBOTS, 'https://example.com', 'Googlebot', [{'url': u} for u in urls])
        self.assertEqual([x['status'] for x in r['rows']], ['unknown'] * len(urls))

    def test_invalid_robots_abstains_not_allows(self):
        r = audit('User-agent: *\nDisallow: /ok%ZZ', 'https://example.com',
                  'Googlebot', [{'url': '/ok'}, {'url': '/about'}])
        self.assertEqual([x['status'] for x in r['rows']], ['unknown', 'unknown'])

    def test_many_cross_origin_urls_never_get_crawl_verdict(self):
        import random
        rng = random.Random(3302026)
        urls = [{'url': f'https://other-{rng.randrange(10000)}.example.com/private/{i}'}
                for i in range(300)]
        r = audit(ROBOTS, 'https://example.com', 'Googlebot', urls)
        self.assertEqual(r['summary']['out_of_scope'], 300)
        self.assertEqual(len(r['review_queue']), 0)

    def test_cli_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / 'robots.txt').write_text(ROBOTS)
            (p / 'inventory.json').write_text(json.dumps([{'url': '/private/x'}]))
            script = Path(__file__).with_name('offline_robots_inventory_audit.py')
            cp = subprocess.run([sys.executable, str(script), '--origin', 'https://example.com',
                                 '--user-agent', 'Googlebot', '--robots-file', str(p / 'robots.txt'),
                                 '--inventory', str(p / 'inventory.json'), '--output', str(p / 'report.json')],
                                capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertEqual(json.loads((p / 'report.json').read_text())['summary']['disallowed'], 1)


if __name__ == '__main__':
    unittest.main()
