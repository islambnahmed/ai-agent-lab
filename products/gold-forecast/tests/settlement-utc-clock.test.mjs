import test from 'node:test';
import assert from 'node:assert/strict';
import {hash,settleReceipt} from '../journal.mjs';

// Synthetic dates and prices only; no live provider data.
const start=Date.UTC(2026,4,6);
const history=Array.from({length:165},(_,i)=>({
  date:new Date(start+i*86400000).toISOString().slice(0,10),price:2000+i
}));
const series=[...history,{date:'2026-10-18',price:2165}];
function receipt(issuedAt='2026-10-17T12:00:00Z'){
  const payload={
    schemaVersion:1,issuedAt,codeCommit:'b'.repeat(40),horizon:1,
    historyLength:165,historyHash:hash(history),targetDate:'2026-10-18',
    point:2164,baseline:2164,lower:2100,upper:2200
  };
  return {...payload,id:hash(payload)};
}
test('equivalent asOf instants with different offsets settle identically',()=>{
  const r=receipt();
  const offset=settleReceipt(r,series,{asOf:'2026-10-18T23:00:00-05:00'});
  const utc=settleReceipt(r,series,{asOf:'2026-10-19T04:00:00Z'});
  assert.deepEqual(offset,utc);
  assert.equal(offset.status,'matured');
  assert.equal(offset.actual,2165);
});
test('same UTC target day remains pending despite next-day textual offset',()=>{
  const r=receipt();
  const utc=settleReceipt(r,series,{asOf:'2026-10-18T22:00:00Z'});
  const offset=settleReceipt(r,series,{asOf:'2026-10-19T01:00:00+03:00'});
  assert.deepEqual(offset,utc);
  assert.equal(utc.status,'pending');
});
test('issue timestamp UTC day controls predates-issue gate',()=>{
  // Text says Oct 19, but the instant is Oct 18 UTC.
  const r=receipt('2026-10-19T00:30:00+03:00');
  const settled=settleReceipt(r,series,{asOf:'2026-10-19T04:00:00Z'});
  assert.equal(settled.status,'matured');
  assert.equal(settled.targetDate,'2026-10-18');
});
test('genuinely earlier target UTC day remains rejected',()=>{
  // Text says Oct 18, but this issue instant is Oct 19 UTC.
  const r=receipt('2026-10-18T23:30:00-05:00');
  assert.throws(
    ()=>settleReceipt(r,series,{asOf:'2026-10-19T12:00:00Z'}),
    /Outcome predates issue/
  );
});
