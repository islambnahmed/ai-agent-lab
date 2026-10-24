import test from 'node:test';
import assert from 'node:assert/strict';
import {issueReceipt,verifyReceipt} from '../journal.mjs';
import {checkReceiptCohort} from '../receipt-cohort.mjs';
import {gateSettlement,summarizeSettlements} from '../settlement-eligibility.mjs';

const series=Array.from({length:260},(_,i)=>({
  date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),
  price:2500+i*0.8+3*Math.sin(i*1.7)
}));
const sourceManifest={status:'fetched',url:'https://example.test/history',
  requestedAt:'2025-09-18T11:57:00Z',receivedAt:'2025-09-18T11:58:00Z',
  rawSha256:'a'.repeat(64),storedSha256:'b'.repeat(64)};
const make=issuedAt=>[1,7,30].map(h=>issueReceipt(series,h,{
  issuedAt,source:'Synthetic fixture',codeCommit:'c'.repeat(40),sourceManifest
}));

test('real hashed receipts form a consistent complete cohort',()=>{
  const receipts=make('2025-09-18T12:00:00Z');
  for(const receipt of receipts)assert.equal(verifyReceipt(receipt),true);
  assert.equal(checkReceiptCohort(receipts,series.at(-1).date,verifyReceipt),'complete');
});

test('individually valid receipts from different issue runs cannot form one cohort',()=>{
  const old=make('2025-09-18T12:00:00Z');
  const newRun=make('2025-09-18T12:01:00Z');
  const mixed=[old[0],newRun[1],old[2]];
  mixed.forEach(verifyReceipt);
  assert.throws(()=>checkReceiptCohort(mixed,series.at(-1).date,verifyReceipt),
    /Mixed receipt cohort metadata: issuedAt/);
});

test('valid receipt integrity does not establish prospective scoring eligibility',()=>{
  const receipts=make('2025-09-18T12:00:00Z');
  assert.equal(checkReceiptCohort(receipts,series.at(-1).date,verifyReceipt),'complete');
  const arithmetic={id:receipts[0].id,horizon:1,status:'matured',
    actual:2700,modelAbsError:15,baselineAbsError:25};
  const guarded=gateSettlement(arithmetic);
  assert.equal(guarded.status,'provisional');
  const summary=summarizeSettlements([guarded])[0];
  assert.equal(summary.matured,0);
  assert.equal(summary.provisional,1);
  assert.equal(summary.modelMae,null);
});
