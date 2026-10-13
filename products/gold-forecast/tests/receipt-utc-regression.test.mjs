import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt,settleReceipt} from '../journal.mjs';

const data=n=>Array.from({length:n},(_,i)=>({
  date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),
  price:2500+i+3*Math.sin(i*.13)
}));
const metadata=issuedAt=>({
  issuedAt,source:'fixed-test-fixture',codeCommit:'a'.repeat(40),
  sourceManifest:{receivedAt:new Date(Date.parse(issuedAt)-60000).toISOString()}
});
test('issue: timezone offset cannot disguise a target already past in UTC',()=>{
  assert.throws(()=>issueReceipt(data(259),1,metadata('2025-09-17T23:30:00-03:00')),
    /Target date has already passed/);
});
test('settle: UTC-completed target matures even when local asOf day is earlier',()=>{
  const receipt=issueReceipt(data(260),1,metadata('2025-09-18T12:00:00Z'));
  const result=settleReceipt(receipt,data(261),{asOf:'2025-09-18T23:30:00-03:00'});
  assert.equal(result.status,'matured');
  assert.equal(result.targetDate,'2025-09-18');
});
