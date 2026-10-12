import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {issue,settle,verifyReceipt,summarize,validateSeries} from './prospective_ledger.mjs';
const base = Array.from({length:50},(_,i)=>{
  const d=new Date('2026-01-01T12:00:00Z');d.setUTCDate(d.getUTCDate()+i);
  return {date:d.toISOString().slice(0,10),price:2500+i};
});
const params={series:base,horizon:7,model:'momentum',modelRevision:'4e4a2438608955e17f3d0e3dd66764aa5cb6c9b4',issuedAt:'2026-02-20T00:01:00Z',source:'synthetic:test'};
const future = Array.from({length:8},(_,i)=>{
  const d=new Date('2026-02-23T12:00:00Z');for(let n=0;n<i;){d.setUTCDate(d.getUTCDate()+1);if(d.getUTCDay()!==0&&d.getUTCDay()!==6)n++}
  return {date:d.toISOString().slice(0,10),price:2550+i};
});
test('deterministic receipt, nonsecret hash, baseline frozen',()=>{
  const a=issue(params);assert.deepEqual(a,issue(params));assert.equal(a.baseline,2549);assert.equal(verifyReceipt(a),true);
});
test('cannot issue using future observation',()=>assert.throws(()=>issue({...params,issuedAt:'2026-02-01T12:00:00Z'}),/Daily close/));
test('same-day daily close is rejected even at 23:59 UTC',()=>{
  assert.throws(()=>issue({...params,issuedAt:'2026-02-19T23:59:59Z'}),/same-day lookahead/);
});
test('next UTC day passes the conservative chronology gate',()=>{
  assert.equal(verifyReceipt(issue({...params,issuedAt:'2026-02-20T00:00:00Z'})),true);
});
test('self-consistent rehashed receipt cannot bypass chronology gate',()=>{
  const receipt=issue(params),{id:ignored,...payload}=receipt;
  payload.originDate='2026-02-20';
  const id=createHash('sha256').update(JSON.stringify(payload)).digest('hex');
  assert.throws(()=>verifyReceipt({...payload,id}),/origin must predate/);
});
test('invalid calendar date rejected',()=>assert.throws(()=>validateSeries([{date:'2026-02-30',price:3}]),/calendar/));
test('duplicates and unsorted history rejected',()=>assert.throws(()=>issue({...params,series:[...base,base.at(-1)]}),/strictly increasing/));
test('bad price rejected without coercion',()=>assert.throws(()=>issue({...params,series:base.map((x,i)=>i===1?{...x,price:'12'}:x)}),/price/));
test('bad issue time rejected',()=>assert.throws(()=>issue({...params,issuedAt:'2026-03-01'}),/UTC/));
test('not enough history rejected',()=>assert.throws(()=>issue({...params,series:base.slice(0,41)}),/42/));
test('unsupported horizon rejected',()=>assert.throws(()=>issue({...params,horizon:31}),/horizon/));
test('tampering with point detected',()=>{const r=issue(params);assert.throws(()=>settle({...r,point:r.point+1},base),/integrity/)});
test('settlement is pending until 7 new observed sessions, not calendar days',()=>{
  const r=issue(params);assert.deepEqual(settle(r,[...base,...future.slice(0,6)]),{id:r.id,status:'pending',remainingSessions:1});
});
test('settlement on seventh observed session; extra later data irrelevant',()=>{
  const r=issue(params), a=settle(r,[...base,...future.slice(0,7)]),b=settle(r,[...base,...future]);
  assert.equal(a.status,'matured');assert.equal(a.targetDate,'2026-03-03');assert.deepEqual(a,b);
  assert.equal(a.baselineAbsError,Math.abs(2549-2556));
});
test('retroactively dated-after-outcome receipts rejected on settlement',()=>{
  const r=issue({...params,issuedAt:'2026-03-01T12:00:00Z'});
  assert.throws(()=>settle(r,[...base,...future]),/issued after/);
});
test('revised historical vintage rejected',()=>{
  const r=issue(params),changed=base.map((x,i)=>i===1?{...x,price:x.price+0.01}:x);
  assert.throws(()=>settle(r,[...changed,...future]),/vintage/);
});
test('truncated historical prefix rejected',()=>assert.throws(()=>settle(issue(params),base.slice(10)),/history missing/));
test('summary refuses to infer significance and handles pending',()=>{
  const r=issue(params),pending=settle(r,base),matured=settle(r,[...base,...future]);
  assert.equal(summarize([pending]).relativeGain,null);
  const s=summarize([pending,matured]);assert.equal(s.matured,1);assert.equal(s.pending,1);assert.match(s.caveat,/Descriptive only/);
});
test('observed sessions, not elapsed weekdays, determine maturity',()=>{
  const fri=base.map((r,i)=>i===49?{date:'2026-02-20',price:r.price}:r);
  const r=issue({...params,series:fri,issuedAt:'2026-02-21T00:01:00Z',horizon:1});
  const monday={date:'2026-02-23',price:2600};
  const result=settle(r,[...fri,monday]);
  assert.equal(result.status,'matured');assert.equal(result.targetDate,'2026-02-23');
});
test('receipt dated on first future observation date is conservatively rejected',()=>{
  const r=issue({...params,issuedAt:'2026-02-23T01:00:00Z'});
  assert.throws(()=>settle(r,[...base,...future]),/issued after/);
});
test('unversioned model cannot be issued',()=>assert.throws(()=>issue({...params,modelRevision:undefined}),/Pinned/));
