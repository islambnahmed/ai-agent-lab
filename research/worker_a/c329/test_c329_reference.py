"""Independent published-example conformance cases; no fixtures derived from parser output."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
PARSER=HERE.parent/'c318'/'robots_gate.py'
spec=importlib.util.spec_from_file_location('c329_robots_gate',PARSER)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

class PublishedReferenceTests(unittest.TestCase):
    def test_published_cases(self):
        cases=json.loads((HERE/'c329_reference_cases.json').read_text(encoding='utf-8'))['cases']
        self.assertGreaterEqual(len(cases),25)
        for case in cases:
            with self.subTest(id=case['id']):
                self.assertEqual(mod.decide(case['robots'],case['agent'],case['target']).status,case['expected'],case['source'])

    def test_malformed_absolute_url_must_abstain(self):
        # Input validation expectation (not an RFC 9309 crawling-policy rule).
        robots='User-agent: *\nDisallow: /private'
        invalid=['https://example.com:bad/private',
                 'https://example.com:99999/private',
                 'https://exa mple.com/private',
                 'https://example.com\n.evil.com/private']
        for url in invalid:
            with self.subTest(url=repr(url)):
                self.assertEqual(mod.decide(robots,'ExampleBot',url).status,'unknown')

if __name__=='__main__':unittest.main()
