import test from 'node:test';
import assert from 'node:assert/strict';
import {gateSettlement, summarizeSettlements} from '../settlement-eligibility.mjs';

const mature = (horizon = 1) => ({id:'forecast',horizon,status:'matured',
  targetDate:'2026-10-13',actual:4210,modelAbsError:1,baselineAbsError:2,covered:true});

test('a price observation alone never verifies prospective publication timing', () => {
  const row = gateSettlement(mature());
  assert.equal(row.status,'provisional');
  assert.equal(row.timingEvidence,'unverified_publication_before_target_close');
  assert.equal(row.modelAbsError,1);
});
test('gate does not mutate the original arithmetic result', () => {
  const input=mature(); const output=gateSettlement(input);
  assert.equal(input.status,'matured');
  assert.notEqual(output,input);
});
test('pending remains pending', () => {
  assert.deepEqual(gateSettlement({id:'x',horizon:7,status:'pending'}),
    {id:'x',horizon:7,status:'pending'});
});
test('quarantine is never promoted', () => {
  assert.equal(gateSettlement({id:'x',horizon:30,status:'quarantined',error:'revision'}).status,
    'quarantined');
});
test('unknown outcome statuses fail closed', () => {
  for (const bad of [null, {}, [], {status:'success'}, {status:'verified'}])
    assert.throws(()=>gateSettlement(bad),TypeError);
});
test('provisional errors do not leak into headline MAE', () => {
  const rows=[gateSettlement(mature()),gateSettlement(mature()),
    {id:'pending',horizon:1,status:'pending'}];
  const s=summarizeSettlements(rows)[0];
  assert.equal(s.matured,0);
  assert.equal(s.provisional,2);
  assert.equal(s.pending,1);
  assert.equal(s.modelMae,null);
  assert.equal(s.baselineMae,null);
});
test('all horizons are separately counted and quarantines are visible', () => {
  const rows=[gateSettlement(mature(1)),gateSettlement(mature(7)),
    {id:'bad',horizon:30,status:'quarantined',error:'bad vintage'}];
  const s=summarizeSettlements(rows);
  assert.deepEqual(s.map(x=>x.provisional),[1,1,0]);
  assert.deepEqual(s.map(x=>x.quarantined),[0,0,1]);
});
test('invalid horizon is rejected rather than silently excluded', () => {
  assert.throws(()=>summarizeSettlements([{status:'pending',horizon:365}]),TypeError);
});
test('raw matured input cannot bypass the gate via the summary API', () => {
  const s=summarizeSettlements([
    {...mature(7),modelAbsError:2,baselineAbsError:6},
    {...mature(7),modelAbsError:4,baselineAbsError:2}
  ])[1];
  assert.equal(s.matured,0);
  assert.equal(s.provisional,2);
  assert.equal(s.modelMae,null);
  assert.equal(s.baselineMae,null);
});
test('malformed headline errors cannot create a performance score', () => {
  for(const n of [NaN,Infinity,-1]) {
    const s=summarizeSettlements([{...mature(),modelAbsError:n}])[0];
    assert.equal(s.matured,0);
    assert.equal(s.modelMae,null);
  }
});
