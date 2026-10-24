import test from 'node:test';
import assert from 'node:assert/strict';
import {hash,settleReceipt} from '../journal.mjs';

// Synthetic daily series; no external prices.
const start=Date.UTC(2026,4,6);
const history=Array.from({length:165},(_,i)=>({
  date:new Date(start+i*86400000).toISOString().slice(0,10),price:2000+i
}));
const series=[...history,{date:'2026-10-18',price:2165}];
const payload={
  schemaVersion:1,issuedAt:'2026-10-17T12:00:00Z',horizon:1,
  historyLength:165,historyHash:hash(history),targetDate:'2026-10-18',
  point:2164,baseline:2164,lower:2100,upper:2200
};
const receipt={...payload,id:hash(payload)};
test('offset and UTC timestamps yield the same matured result',()=>{
  const offset=settleReceipt(receipt,series,{asOf:'2026-10-18T23:00:00-05:00'});
  const utc=settleReceipt(receipt,series,{asOf:'2026-10-19T04:00:00Z'});
  assert.deepEqual(offset,utc);
  assert.equal(offset.status,'matured');
  assert.equal(offset.actual,2165);
});
test('current UTC day remains pending',()=>{
  assert.equal(settleReceipt(receipt,series,{asOf:'2026-10-18T22:00:00Z'}).status,'pending');
});

test('equivalent offsets on UTC target day remain pending',()=>{
  const utc=settleReceipt(receipt,series,{asOf:'2026-10-18T22:00:00Z'});
  const offset=settleReceipt(receipt,series,{asOf:'2026-10-19T01:00:00+03:00'});
  assert.deepEqual(offset,utc);
  assert.equal(offset.status,'pending');
});
