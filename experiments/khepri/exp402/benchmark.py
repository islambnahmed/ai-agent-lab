"""Deterministic differential test, includes deliberate negative and ambiguity cases."""
import hashlib
import json
import random
import subprocess
from canonical import digest, gold_payload, seo_payload, InvalidPayload

R = random.Random(402)
UNICODE = ['ن', 'َ', 'م', 'ا', 'ر', '😄', '🚀', 'é', 'e\u0301', '漢', '字', '\n', '\t', '\x00', '/', '\\', '"', '<', '>', '\u2028']

def word(n):
    return ''.join(R.choice(UNICODE) for _ in range(n))

def gen(depth=0):
    if depth>3 or R.random()<.65:
        return R.choice([None, True, False, word(R.randrange(15))])
    if R.random()<.5:
        return [gen(depth+1) for _ in range(R.randrange(5))]
    return {'Key'+str(i):gen(depth+1) for i in range(R.randrange(5))}

def test_cases():
    cases=[]
    for i in range(1800):
        if i%3==0:
            amount = R.choice(['0','-0.000','12.3400','100.000','0.0010','-25.100','123456789012345678901234567890.001'])
            cases.append({'kind':'gold','args':[f'gold-{i}', amount, 'USD', word(12)]})
        elif i%3==1:
            count = R.choice(['0','1.0','000.1','1200','200.00','-0','98765432101234567890'])
            cases.append({'kind':'seo','args':[f'seo-{i}', '/arabic/'+word(6), count, word(25)]})
        else:
            cases.append({'kind':'raw','payload':gen()})
    negatives=[{'kind':'raw','payload':v} for v in [
        {'v':1}, {'v':1.0}, {'v':9007199254740993}, {'v':float('nan')},
        {'v':'\ud800'}, {'v':'\udc00'}, {'1bad':'x'}, {'_proto':'x'},
        {'v':[1]}, {'v':{'Nested':2.0}}, {'v':(1<<200)},
        {'v':'x'*1048576}, {'v':[[[[[[[[[[[[[[[[[[[[[[[[['x']]]]]]]]]]]]]]]]]]]]]]]]]}
    ]]
    # Intentionally malformed decimal representations are rejected by both.
    for i,s in enumerate(['01','+1','1e3','1.',' 1','NaN','Infinity','-01','.2','']):
        negatives.append({'kind':'gold','args':[f'invalid-{i}',s,'USD','']})
    return cases+negatives

def py_result(q):
    try:
        if q['kind']=='gold':v=gold_payload(*q['args'])
        elif q['kind']=='seo':v=seo_payload(*q['args'])
        else:v=q['payload']
        return {'ok':True,'hash':digest(v)}
    except (InvalidPayload, UnicodeEncodeError):return {'ok':False}

def main():
    cases=test_cases()
    data=''.join(json.dumps(c,ensure_ascii=True,allow_nan=True)+'\n' for c in cases)
    p=subprocess.run(['node','runner.mjs'],input=data,text=True,capture_output=True,check=True)
    js=[json.loads(x) for x in p.stdout.splitlines()]
    assert len(js)==len(cases), (len(js),len(cases),p.stderr)
    mismatches=[]; valid=0; rejected=0; kinds={}
    for i,(q,j) in enumerate(zip(cases,js)):
        py=py_result(q)
        kinds[q['kind']]=kinds.get(q['kind'],0)+1
        if py['ok'] != j['ok'] or (py['ok'] and py['hash'] != j['hash']):
            mismatches.append({'index':i,'case':q,'python':py,'js':j})
        valid+=py['ok']; rejected+=not py['ok']
    # Same canonical semantic content with different key insertion order.
    assert digest({'Alpha':'ناريفيشن','Beta':['🚀','e\u0301']}) == digest({'Beta':['🚀','e\u0301'],'Alpha':'ناريفيشن'})
    # Unicode normalization must NOT alias distinct content.
    assert digest({'Text':'é'}) != digest({'Text':'e\u0301'})
    # Gold decimal normalization is exact and not floating point.
    assert digest(gold_payload('a','12.3400')) == digest(gold_payload('a','12.34'))
    # Source failure from exp401: Python floats differ from JS Number JSON serialization.
    naive_py=json.dumps({'v':1.0},separators=(',',':'))
    naive_js=subprocess.check_output(['node','-e','process.stdout.write(JSON.stringify({v:1.0}))'],text=True)
    assert naive_py != naive_js
    out={'experiment':'exp402','cases':len(cases),'valid':valid,'rejected':rejected,
         'cross_runtime_mismatches':len(mismatches),'by_kind':kinds,
         'naive_python_json':naive_py,'naive_js_json':naive_js,
         'unicode_normalization_preserved':True,'decimal_string_normalization':True,
         'mismatch_examples':mismatches[:3]}
    with open('results.json','w',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    assert not mismatches

if __name__=='__main__':main()
