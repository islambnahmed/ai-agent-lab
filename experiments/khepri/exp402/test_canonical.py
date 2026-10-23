import json
import subprocess
import unittest
from canonical import (InvalidPayload, canonical_bytes, canonical_decimal,
                       digest, gold_payload, seo_payload)

class CanonicalTests(unittest.TestCase):
    def test_key_order(self):
        self.assertEqual(digest({'Zoo':'z','Alpha':'a'}),digest({'Alpha':'a','Zoo':'z'}))
    def test_gold_decimal_exact(self):
        self.assertEqual(digest(gold_payload('x','1.23000')),digest(gold_payload('x','1.23')))
    def test_negative_zero(self):
        self.assertEqual(canonical_decimal('-0.000'),'0')
    def test_large_decimal_no_float(self):
        self.assertEqual(canonical_decimal('123456789012345678901234567890.1234500'),
                         '123456789012345678901234567890.12345')
    def test_invalid_decimal(self):
        for s in ['01','+1','1e2','1.','.1',' 1','NaN','Infinity','']:
            with self.subTest(s=s),self.assertRaises(InvalidPayload):canonical_decimal(s)
    def test_numbers_rejected(self):
        for v in [0,1,1.0,2**100,float('nan'),{'Amount':1},[False,0]]:
            with self.subTest(v=v),self.assertRaises(InvalidPayload):digest(v)
    def test_boolean_and_null(self):
        self.assertEqual(canonical_bytes({'Yes':True,'No':False,'Nil':None}),b'{"Nil":null,"No":false,"Yes":true}')
    def test_unicode_roundtrip(self):
        self.assertIn('ناريفيشن'.encode(),canonical_bytes({'Text':'ناريفيشن🚀'}))
    def test_unicode_not_normalized(self):
        self.assertNotEqual(digest({'Text':'é'}),digest({'Text':'e\u0301'}))
    def test_surrogates_rejected(self):
        for s in ['\ud800','\udc00','a\ud800b']:
            with self.subTest(s=repr(s)),self.assertRaises(InvalidPayload):digest({'Text':s})
    def test_unsafe_keys(self):
        for k in ['1foo','_proto','__proto__','a-b','أ']:
            with self.subTest(k=k),self.assertRaises(InvalidPayload):digest({k:'x'})
    def test_depth(self):
        v='x'
        for _ in range(26):v=[v]
        with self.assertRaises(InvalidPayload):digest(v)
    def test_size(self):
        with self.assertRaises(InvalidPayload):digest({'Text':'a'*1048576})
    def test_second_domain(self):
        self.assertEqual(digest(seo_payload('id','/arabic','123.00','عنوان')),
                         digest(seo_payload('id','/arabic','123','عنوان')))
    def test_cross_runtime_targeted(self):
        cases=[{'payload':{'Text':'ناريفيشن🚀','Amount':'1.23'}},
               {'payload':{'Text':'é'}},{'payload':{'Text':'e\u0301'}},
               {'payload':{'Text':'\ud800'}},{'payload':{'Amount':1.0}}]
        s=''.join(json.dumps(c,ensure_ascii=True)+'\n' for c in cases)
        p=subprocess.run(['node','runner.mjs'],input=s,text=True,capture_output=True,check=True)
        results=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(results),len(cases))
        for q,r in zip(cases,results):
            try:
                h=digest(q['payload']);self.assertTrue(r['ok']);self.assertEqual(r['hash'],h)
            except InvalidPayload:self.assertFalse(r['ok'])
    def test_duplicate_keys_are_a_known_limit(self):
        # The strict canonicalizer sees only a parsed object; duplicate raw keys are lost.
        duplicate='{"Id":"first","Id":"second"}'
        self.assertEqual(json.loads(duplicate),{'Id':'second'})
        self.assertEqual(digest(json.loads(duplicate)),digest({'Id':'second'}))

if __name__=='__main__':unittest.main()
