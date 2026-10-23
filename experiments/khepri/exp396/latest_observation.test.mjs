import test from 'node:test';
import assert from 'node:assert/strict';
import {makeLedger} from '../exp395/vintage_gate.mjs';
import {latestObservation} from './latest_observation.mjs';
const D=100000;
const e=(id, effectiveAt, revision=0, value=100, series='gold')=>({
  id,series,revision,value,effectiveAt,providerPublishedAt:effectiveAt
});

test('counterexample: late revision of old observation overrides newer observation in exp395',()=>{
 const l=makeLedger();
 l.append(e('old',D-1000,0,100),D-500);
 l.append(e('new',D-100,0,110),D-300);
 l.append(e('old-revised',D-1000,1,101),D-50);
 assert.equal(l.snapshot('gold',D).id,'old-revised');
 assert.equal(latestObservation(l,'gold',D).id,'new');
});
test('newest vintage of same observation wins',()=>{
 const l=makeLedger();l.append(e('old',D-1000),D-500);
 l.append(e('new',D-100,0,110),D-300);
 l.append(e('new-revised',D-100,1,111),D-50);
 assert.equal(latestObservation(l,'gold',D).id,'new-revised');
});
test('future-received newer observation is excluded',()=>{
 const l=makeLedger();l.append(e('old',D-1000),D-500);
 l.append(e('new',D-100,0,110),D+50);
 assert.equal(latestObservation(l,'gold',D).id,'old');
});
test('future-effective event is excluded even if received early',()=>{
 const l=makeLedger();l.append(e('old',D-1000),D-500);
 l.append(e('future',D+1,0,110),D-100);
 assert.equal(latestObservation(l,'gold',D).id,'old');
});
test('stale observation abstains under maxAge, even if recently revised',()=>{
 const l=makeLedger();l.append(e('old',D-1000),D-500);
 l.append(e('old-revised',D-1000,1),D-1);
 assert.equal(latestObservation(l,'gold',D,{maxAge:200}).status,'abstain');
});
test('source series isolation',()=>{
 const l=makeLedger();l.append(e('gold',D-500,0,100),D-300);
 l.append(e('seo',D-100,0,120,'seo'),D-200);
 assert.equal(latestObservation(l,'gold',D).id,'gold');
 assert.equal(latestObservation(l,'seo',D).id,'seo');
});
test('empty and invalid queries',()=>{
 const l=makeLedger();assert.equal(latestObservation(l,'gold',D).status,'abstain');
 for(const [series,time,opts] of [['',D,{}],['gold',NaN,{}],['gold',D,{maxAge:-1}]]){
  assert.throws(()=>latestObservation(l,series,time,opts));
 }
});
test('historical replay does not include revisions received after query',()=>{
 const l=makeLedger();l.append(e('old',D-1000),D-500);
 l.append(e('new',D-100,0,110),D-300);
 l.append(e('new-revised',D-100,1,115),D+1);
 assert.equal(latestObservation(l,'gold',D).value,110);
 assert.equal(latestObservation(l,'gold',D+2).value,115);
});
test('receipt ordering and observation ordering can diverge for SEO too',()=>{
 const l=makeLedger();l.append(e('yesterday',D-1000,0,90,'seo'),D-600);
 l.append(e('today',D-100,0,100,'seo'),D-400);
 l.append(e('yesterday-correction',D-1000,1,92,'seo'),D-200);
 assert.equal(l.snapshot('seo',D).id,'yesterday-correction');
 assert.equal(latestObservation(l,'seo',D).id,'today');
});
