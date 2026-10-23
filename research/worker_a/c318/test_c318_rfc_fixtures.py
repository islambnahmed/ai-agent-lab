"""Independent offline cases from RFC 9309 Figure 6 and Google robots spec.

References:
  RFC 9309 §2.2.2–2.2.3, Figures 4 and 6:
    https://www.rfc-editor.org/rfc/rfc9309.html
  Google robots.txt interpretation, File format and URL matching:
    https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec

These are manually transcribed specification examples and conservative
metamorphic variations; no live website access is performed.
"""
import unittest
from robots_gate import decide


class RFC9309IndependentFixtures(unittest.TestCase):
    def assert_status(self, rule, path, status, agent='ExampleBot'):
        robots = 'User-agent: *\n' + rule
        got = decide(robots, agent, path)
        self.assertEqual(got.status, status, (rule, path, got))

    # RFC 9309 Figure 6: percent-encoded wildcard and end-anchor as literal
    # URI characters. The rule is literal; raw URI spelling is equivalent to
    # the corresponding percent-encoded spelling.
    def test_rfc_figure6_literal_asterisk_raw_uri(self):
        self.assert_status('Disallow: /path/file-with-a-%2A.html', '/path/file-with-a-*.html', 'disallowed')

    def test_rfc_figure6_literal_dollar_raw_uri(self):
        self.assert_status('Disallow: /path/foo-%24', '/path/foo-$', 'disallowed')

    def test_rfc_figure6_literal_asterisk_encoded_uri(self):
        self.assert_status('Disallow: /path/file-with-a-%2A.html', '/path/file-with-a-%2a.html', 'disallowed')

    def test_rfc_figure6_literal_dollar_encoded_uri(self):
        self.assert_status('Disallow: /path/foo-%24', '/path/foo-%24', 'disallowed')

    def test_rfc_figure6_does_not_match_different_literal(self):
        self.assert_status('Disallow: /path/file-with-a-%2A.html', '/path/file-with-a-x.html', 'allowed')

    def test_encoded_asterisk_in_query(self):
        self.assert_status('Disallow: /*?q=%2A', '/search?q=*', 'disallowed')

    def test_encoded_dollar_in_query(self):
        self.assert_status('Disallow: /*?q=%24', '/search?q=$', 'disallowed')

    # Google File format: a leading UTF-8 BOM is ignored; the following
    # User-agent line is still valid and its rules must not be dropped.
    def test_google_bom_does_not_drop_first_group(self):
        txt = '\ufeffUser-agent: *\nDisallow: /private'
        self.assertEqual(decide(txt, 'ExampleBot', '/private').status, 'disallowed')

    def test_google_bom_specific_agent_precedence(self):
        txt = '\ufeffUser-agent: ExampleBot\nDisallow: /private\nUser-agent: *\nAllow: /'
        self.assertEqual(decide(txt, 'ExampleBot', '/private').status, 'disallowed')
        self.assertEqual(decide(txt, 'OtherBot', '/private').status, 'allowed')

    def test_no_bom_same_as_bom(self):
        txt = 'User-agent: *\nDisallow: /private'
        self.assertEqual(decide(txt, 'ExampleBot', '/private').status,
                         decide('\ufeff' + txt, 'ExampleBot', '/private').status)

    # Other independent cases from RFC 9309 Figure 4 and Google examples.
    def test_rfc_unreserved_percent_decoding(self):
        self.assert_status('Disallow: /foo/bar/baz', '/foo/bar/%62%61%7A', 'disallowed')

    def test_rfc_unicode_raw_encoded_equivalence(self):
        self.assert_status('Disallow: /foo/ツ', '/foo/%E3%83%84', 'disallowed')

    def test_google_php_end_anchor_with_query(self):
        self.assert_status('Disallow: /*.php$', '/folder/filename.php?parameters', 'allowed')

    def test_google_php_unanchored_with_query(self):
        self.assert_status('Disallow: /*.php', '/folder/filename.php?parameters', 'disallowed')

    def test_google_sitemap_between_agents_does_not_split(self):
        txt = 'User-agent: a\nSitemap: https://example.test/map.xml\nUser-agent: b\nDisallow: /'
        self.assertEqual(decide(txt, 'a', '/x').status, 'disallowed')


if __name__ == '__main__':
    unittest.main()
