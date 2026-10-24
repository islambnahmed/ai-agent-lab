import test from 'node:test';
import assert from 'node:assert/strict';
import {checkReceiptCohort} from '../receipt-cohort.mjs';

const origin = '2026-10-11';
function receipt(horizon) {
  return {id:'id-'+horizon,schemaVersion:1,horizon,issuedAt:'2026-10-12T17:12:52Z',
    source:'Standard Bullion',codeCommit:'a'.repeat(40),modelVersion:'gold-v2.0.0',
    calendar:'observations',originDate:origin,originClose:4207.98,
    historyHash:'b'.repeat(64),historyLength:324,
    sourceManifest:{url:'https://example.test/history',requestedAt:'2026-10-12T17:10:48Z',
      receivedAt:'2026-10-12T17:10:55Z',rawSha256:'c'.repeat(64),storedSha256:'d'.repeat(64)}};
}
const full=()=>[1,7,30].map(receipt);
test('empty cohort permits a new atomic preparation',()=>{
  assert.equal(checkReceiptCohort([null,null,null],origin),'empty');
});
test('a complete consistent cohort is reusable without reissuing',()=>{
  assert.equal(checkReceiptCohort(full(),origin),'complete');
});
test('partial cohorts fail closed instead of silently mixing fetch vintages',()=>{
  for(const slots of [[receipt(1),null,null],[null,receipt(7),null],[receipt(1),receipt(7),null]])
    assert.throws(()=>checkReceiptCohort(slots,origin),/Partial receipt cohort/);
});
test('cohort horizons must correspond to their filenames',()=>{
  const rows=full();rows[1].horizon=30;
  assert.throws(()=>checkReceiptCohort(rows,origin),/horizon or origin/);
});
test('a different history hash is rejected',()=>{
  const rows=full();rows[2].historyHash='e'.repeat(64);
  assert.throws(()=>checkReceiptCohort(rows,origin),/historyHash/);
});
test('mixed code and issue times are rejected',()=>{
  for(const field of ['codeCommit','issuedAt']) {
    const rows=full();rows[1][field]='changed';
    assert.throws(()=>checkReceiptCohort(rows,origin),new RegExp(field));
  }
});
test('mixed source snapshot timestamps and hashes are rejected',()=>{
  for(const field of ['requestedAt','receivedAt','rawSha256','storedSha256','url']) {
    const rows=full();rows[2].sourceManifest[field]='changed';
    assert.throws(()=>checkReceiptCohort(rows,origin),new RegExp(field));
  }
});
test('rejects mismatched origin and malformed receipt structures',()=>{
  assert.throws(()=>checkReceiptCohort(full(),'2026-10-12'),/horizon or origin/);
  assert.throws(()=>checkReceiptCohort([{}, {}, {}],origin),/horizon or origin|manifest/);
  assert.throws(()=>checkReceiptCohort([null, null, undefined],origin),/Malformed receipt/);
});
test('caller-provided receipt integrity verifier is invoked for all receipts',()=>{
  let count=0;
  assert.equal(checkReceiptCohort(full(),origin,()=>{count++;}),'complete');
  assert.equal(count,3);
  assert.throws(()=>checkReceiptCohort(full(),origin,()=>{throw Error('Receipt integrity mismatch');}),/integrity/);
});
