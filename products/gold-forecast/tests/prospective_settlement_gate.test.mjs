import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {assessProspectiveSettlement as assess} from '../scripts/prospective_settlement_gate.mjs';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const day=i=>new Date(Date.UTC(2026,3,1+i)).toISOString().slice(0,10);
const prefix=Array.from({length:165},(_,i)=>({date:day(i),price:4000+i}));
const origin=prefix.at(-1).date;
const issuedAt=origin+'T17:00:00Z';
const anchorAt=origin+'T17:01:00Z';
const next=day(165),after=day(166);
function receipt(h=1){const r={schemaVersion:1,issuedAt,calendar:'observations',targetDate:null,
  originDate:origin,originClose:4164,historyLength:165,historyHash:hash(prefix),horizon:h,
  point:4180,baseline:4164};return {...r,id:hash(r)};}
const opts={anchorAt,asOf:day(167)+'T12:00:00Z'};
test('matured next-day observation remains conditional, not proof of skill',()=>{
 const r=assess(receipt(),[...prefix,{date:next,price:4200}],opts);
 assert.equal(r.settlementStatus,'matured_observation_unverified_provenance');
 assert.equal(r.prospectiveStatus,'later_target_date_conditional');
 assert.equal(r.errorReductionUsd,Math.abs(4164-4200)-Math.abs(4180-4200));
 assert.equal(r.verifiedPredictiveSkill,false);
});
test('receipt published after first target date cannot be called prospective',()=>{
 const r=assess(receipt(),[...prefix,{date:next,price:4200}],{
   anchorAt:after+'T12:00:00Z',asOf:day(168)+'T12:00:00Z'});
 assert.equal(r.prospectiveStatus,'target_date_before_anchor');
});
test('same-day target with later issue cannot occur as a unique future observation',()=>{
 assert.throws(()=>assess(receipt(),[...prefix,{date:origin,price:4300}],opts),/Duplicate or out-of-order/);
});
test('first publication after anchor remains conditional on authenticating evidence',()=>{
 const r=assess(receipt(),[...prefix,{date:next,price:4200}],{
  ...opts,targetFirstPublishedAt:next+'T19:00:00Z'});
 assert.equal(r.prospectiveStatus,'post_anchor_publication_conditional_on_external_authentication');
 assert.equal(r.verifiedPredictiveSkill,false);
});
test('pre-anchor target availability blocks prospectiveness',()=>{
 const r=assess(receipt(),[...prefix,{date:next,price:4200}],{
  anchorAt:next+'T20:00:00Z',asOf:day(168)+'T12:00:00Z',targetFirstPublishedAt:next+'T19:00:00Z'});
 assert.equal(r.prospectiveStatus,'target_already_available_at_anchor');
});
test('horizon counts observed rows, not calendar days',()=>{
 const r=assess(receipt(7),[...prefix,...Array.from({length:7},(_,i)=>({date:day(165+i*2),price:4200+i}))],
  {anchorAt,asOf:day(180)+'T12:00:00Z'});
 assert.equal(r.targetDate,day(177));
 assert.equal(r.actual,4206);
});
test('not enough future closes remains pending without invented target date',()=>{
 const r=assess(receipt(7),[...prefix,{date:next,price:4200}],opts);
 assert.equal(r.settlementStatus,'pending');
 assert.equal(r.remainingObservations,6);
});
test('historical revisions are quarantined even if later prices are present',()=>{
 const altered=prefix.map(x=>({...x}));altered[30].price+=1;
 assert.throws(()=>assess(receipt(),[...altered,{date:next,price:4200}],opts),/prefix mismatch/);
});
test('forged hash, unsorted dates, and incomplete same-day closes are rejected',()=>{
 const bad={...receipt(),point:1};
 assert.throws(()=>assess(bad,[...prefix,{date:next,price:4200}],opts),/hash mismatch/);
 assert.throws(()=>assess(receipt(),[...prefix,{date:next,price:4200},{date:next,price:4200}],opts),/Duplicate/);
 assert.throws(()=>assess(receipt(),[...prefix,{date:day(167),price:4200}],opts),/not completed/);
});
test('publication timestamp later than snapshot is rejected',()=>{
 assert.throws(()=>assess(receipt(),[...prefix,{date:next,price:4200}],{
  ...opts,targetFirstPublishedAt:day(169)+'T00:00:00Z'}),/after settlement snapshot/);
});
