"""Cycle 317 regression fixtures from RFC 9309 and Google robots.txt documentation.

Run after placing this file alongside robots_gate.py from Cycle 316 and applying
c317_robots_gate.patch. No network access is needed.
"""
import unittest
from robots_gate import decide

class PublishedFixtures(unittest.TestCase):
    def check(self, robots, agent, path, expected):
        self.assertEqual(decide(robots, agent, path).status, expected)

    def test_google_wildcard_longer(self):
        self.check('User-agent: *\nAllow: /page\nDisallow: /*.htm',
                   'Googlebot', '/page.htm', 'disallowed')

    def test_google_wildcard_tie(self):
        self.check('User-agent: *\nAllow: /page\nDisallow: /*.ph',
                   'Googlebot', '/page.php5', 'allowed')

    def test_root_anchor_more_specific(self):
        robots='User-agent: *\nDisallow: /$\nAllow: /'
        self.check(robots, 'Googlebot', '/', 'disallowed')
        self.check(robots, 'Googlebot', '/page', 'allowed')

    def test_root_anchor_allow(self):
        robots='User-agent: *\nAllow: /$\nDisallow: /'
        self.check(robots, 'Googlebot', '/', 'allowed')
        self.check(robots, 'Googlebot', '/page', 'disallowed')

    def test_sitemap_does_not_split(self):
        robots='User-agent: a\nSitemap: https://example.org/sitemap.xml\nUser-agent: b\nDisallow: /'
        self.check(robots, 'a', '/private', 'disallowed')
        self.check(robots, 'b', '/private', 'disallowed')

    def test_empty_disallow_splits_groups(self):
        robots='User-agent: Foo\nDisallow:\nUser-agent: Bar\nDisallow: /private'
        self.check(robots, 'Foo', '/private', 'allowed')
        self.check(robots, 'Bar', '/private', 'disallowed')

    def test_empty_allow_splits_groups(self):
        robots='User-agent: Foo\nAllow:\nUser-agent: Bar\nDisallow: /private'
        self.check(robots, 'Foo', '/private', 'allowed')
        self.check(robots, 'Bar', '/private', 'disallowed')

    def test_rfc_longest_match(self):
        robots='User-agent: foobot\nAllow: /example/page/\nDisallow: /example/page/disallowed.gif'
        self.check(robots, 'foobot', '/example/page/disallowed.gif', 'disallowed')
        self.check(robots, 'foobot', '/example/page/allowed.gif', 'allowed')

    def test_google_agent_merge(self):
        robots=('User-agent: Googlebot-News\nDisallow: /fish\n'
                'User-agent: *\nDisallow: /carrots\n'
                'User-agent: Googlebot-News\nDisallow: /shrimp')
        self.check(robots, 'Googlebot-News', '/fish', 'disallowed')
        self.check(robots, 'Googlebot-News', '/shrimp', 'disallowed')
        self.check(robots, 'Googlebot-News', '/carrots', 'allowed')
        self.check(robots, 'Otherbot', '/carrots', 'disallowed')

if __name__ == '__main__':
    unittest.main()
