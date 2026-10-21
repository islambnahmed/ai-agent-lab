import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt, settleReceipt} from '../journal.mjs';

const day = ms => new Date(ms).toISOString().slice(0,10);
const DAY = 86400000;
function history(end, n=325, gapIndex=101) {
  const finish=Date.parse(end+'T00:00:00Z'), rows=[];
  for(let i=n-1;i>=0;i--) {
    if(i===gapIndex) continue;
    rows.push({date:day(finish-i*DAY),price:2400+(n-i)*0.37+4*Math.sin(i/11)});
  }
  return rows;
}
function issue(rows,issuedAt,h=7) {
  return issueReceipt(rows,h,{issuedAt,source:'synthetic-integrity-test',
    codeCommit:'a'.repeat(40),
    sourceManifest:{receivedAt:new Date(Date.parse(issuedAt)-60000).toISOString()}});
}
test('irregular seven-close horizon must not count pre-issue closes',()=>{
  const origin=history('2026-10-01');
  const r=issue(origin,'2026-10-07T09:00:00Z');
  assert.equal(r.calendar,'observations');
  assert.equal(r.targetDate,null);
  const outcomes=Array.from({length:7},(_,i)=>({date:day(Date.parse('2026-10-02T00:00:00Z')+i*DAY),price:2700+i}));
  assert.throws(()=>settleReceipt(r,[...origin,...outcomes],{asOf:'2026-10-10T09:00:00Z'}),/Prospective boundary unverified/);
});
test('same UTC-day first close cannot prove it followed issue time',()=>{
  const origin=history('2026-10-11');
  const r=issue(origin,'2026-10-12T09:00:00Z');
  const outcomes=Array.from({length:7},(_,i)=>({date:day(Date.parse('2026-10-12T00:00:00Z')+i*DAY),price:2700+i}));
  assert.throws(()=>settleReceipt(r,[...origin,...outcomes],{asOf:'2026-10-21T09:00:00Z'}),/Prospective boundary unverified/);
});
test('all seven counted closes strictly after issue may settle',()=>{
  const origin=history('2026-10-11');
  const r=issue(origin,'2026-10-12T09:00:00Z');
  const outcomes=Array.from({length:7},(_,i)=>({date:day(Date.parse('2026-10-13T00:00:00Z')+i*DAY),price:2700+i}));
  const result=settleReceipt(r,[...origin,...outcomes],{asOf:'2026-10-21T09:00:00Z'});
  assert.equal(result.status,'matured');
  assert.equal(result.targetDate,'2026-10-19');
});
