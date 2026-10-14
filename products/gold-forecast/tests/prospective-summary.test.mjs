import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeProspective} from '../prospective-summary.mjs';
const matured=(id,horizon,modelAbsError,baselineAbsError,covered)=>
  ({id,horizon,status:'matured',modelAbsError,baselineAbsError,covered});

test('pending only: no invented skill or coverage',()=>{
  const r=summarizeProspective([{id:'a',horizon:1,status:'pending'}]);
  assert.equal(r.summaries[0].pending,1);
  assert.equal(r.summaries[0].modelMae,null);
  assert.equal(r.summaries[0].empiricalCoveragePct,null);
  assert.equal(r.evidenceStatus,'not_verified_for_promotion');
});
test('MAE, coverage and skill are horizon separated',()=>{
  const r=summarizeProspective([matured('a',1,2,4,true),matured('b',1,4,6,false),
    matured('c',7,30,20,true),{id:'d',horizon:30,status:'pending'}]);
  assert.equal(r.summaries[0].modelMae,3);
  assert.equal(r.summaries[0].baselineMae,5);
  assert.equal(r.summaries[0].empiricalCoveragePct,50);
  assert.equal(r.summaries[0].relativeMaeSkillPct,40);
  assert.equal(r.summaries[1].relativeMaeSkillPct,-50);
  assert.equal(r.summaries[2].pending,1);
});
test('duplicate receipts, malformed metrics and unknown horizons fail closed',()=>{
  assert.throws(()=>summarizeProspective([matured('a',1,1,2,true),matured('a',7,1,2,true)]),/Duplicate/);
  assert.throws(()=>summarizeProspective([matured('a',2,1,2,true)]),/horizon/);
  assert.throws(()=>summarizeProspective([matured('a',1,-1,2,true)]),/metrics/);
  assert.throws(()=>summarizeProspective([matured('a',1,1,NaN,true)]),/metrics/);
  assert.throws(()=>summarizeProspective([matured('a',1,1,2,1)]),/metrics/);
});
test('unattributed quarantines remain visible, zero baseline skill stays null',()=>{
  const r=summarizeProspective([{id:'bad',status:'quarantined',error:'Receipt invalid'},
    {id:'pending',horizon:7,status:'pending'},matured('ok',7,0,0,true)]);
  assert.equal(r.unattributedQuarantined,1);
  assert.equal(r.summaries[1].matured,1);
  assert.equal(r.summaries[1].relativeMaeSkillPct,null);
  assert.equal(r.evidenceStatus,'not_verified_for_promotion');
});
