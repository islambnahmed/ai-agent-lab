"""Origin authority regression tests; all data synthetic and offline."""
import unittest
from origin_gate import decide_scoped

ROBOTS = 'User-agent: *\nDisallow: /private\n'
R = 'https://example.test/robots.txt'
T = 'https://example.test/private/secret'


class OriginScopeTests(unittest.TestCase):
    def check(self, expected, robots_url=R, target_url=T, **kwargs):
        result = decide_scoped(ROBOTS, 'ExampleBot', robots_url, target_url, **kwargs)
        self.assertEqual(result.status, expected, result)
        return result

    def test_same_origin_disallow(self): self.check('disallowed')
    def test_same_origin_allow(self): self.check('allowed', target_url='https://example.test/public')
    def test_host_case_default_port_equivalence(self):
        self.check('disallowed', 'HTTPS://EXAMPLE.TEST:443/robots.txt', T)
    def test_different_host_unknown(self):
        self.check('unknown', target_url='https://other.test/private')
    def test_subdomain_not_parent(self):
        self.check('unknown', target_url='https://sub.example.test/private')
    def test_different_scheme_unknown(self):
        self.check('unknown', target_url='http://example.test/private')
    def test_different_port_unknown(self):
        self.check('unknown', target_url='https://example.test:444/private')
    def test_explicit_default_port_matches(self):
        self.check('disallowed', target_url='https://example.test:443/private')
    def test_http_default_port_matches(self):
        self.check('disallowed', 'http://example.test:80/robots.txt', 'http://example.test/private')
    def test_ipv6_equivalent_spelling(self):
        self.check('disallowed', 'http://[2001:db8::1]/robots.txt', 'http://[2001:0db8:0:0::1]:80/private')
    def test_ipv6_other_address_unknown(self):
        self.check('unknown', 'http://[2001:db8::1]/robots.txt', 'http://[2001:db8::2]/private')
    def test_bad_robots_path(self):
        self.check('unknown', robots_url='https://example.test/a/robots.txt')
    def test_robots_query(self):
        self.check('unknown', robots_url=R+'?v=1')
    def test_robots_empty_query(self):
        self.check('unknown', robots_url=R+'?')
    def test_target_userinfo(self):
        self.check('unknown', target_url='https://user@example.test/private')
    def test_target_empty_userinfo(self):
        self.check('unknown', target_url='https://@example.test/private')
    def test_target_fragment(self):
        self.check('unknown', target_url=T+'#section')
    def test_backslash_ambiguous(self):
        self.check('unknown', target_url='https://example.test\\@evil.test/private')
    def test_space_ambiguous(self):
        self.check('unknown', target_url=' https://example.test/private')
    def test_percent_host_ambiguous(self):
        self.check('unknown', target_url='https://exa%6dple.test/private')
    def test_unicode_hostname_abstains(self):
        self.check('unknown', target_url='https://exämple.test/private')
    def test_trailing_dot_abstains(self):
        self.check('unknown', target_url='https://example.test./private')
    def test_ambiguous_numeric_hostname(self):
        self.check('unknown', target_url='https://2130706433/private')
    def test_invalid_port(self):
        self.check('unknown', target_url='https://example.test:99999/private')
    def test_missing_port_value(self):
        # An empty port is ambiguous; currently treated as default by urlsplit.
        self.check('unknown', target_url='https://example.test:/private')
    def test_unavailable_not_implicitly_allow(self):
        result=self.check('unknown', fetch_state='unavailable')
        self.assertEqual(result.fetch_state, 'unavailable')
    def test_unreachable_not_implicitly_disallow(self):
        self.check('unknown', fetch_state='unreachable')
    def test_not_fetched_abstains(self):
        self.check('unknown', fetch_state='not_fetched')
    def test_missing_body_abstains(self):
        self.assertEqual(decide_scoped(None, 'ExampleBot', R, T).status, 'unknown')
    def test_invalid_fetch_state(self):
        self.check('unknown', fetch_state='success')
    def test_query_preserved_for_matching(self):
        result=decide_scoped('User-agent: *\nDisallow: /search?secret=1',
                             'ExampleBot', R, 'https://example.test/search?secret=1')
        self.assertEqual(result.status, 'disallowed')


if __name__ == '__main__':
    unittest.main()
