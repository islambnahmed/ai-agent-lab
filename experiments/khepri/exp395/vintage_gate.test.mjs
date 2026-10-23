import test from 'node:test';
import assert from 'node:assert/strict';
import {makeLedger,naiveLatest,naivePublishedCutoff} from './vintage_gate.mjs';
const D=100000;
const event=(id,revision,value=100,effectiveAt=D-1000,providerPublishedAt=D-500)=>({id,series:'gold',revision,value,effectiveAt,providerPublishedAt});
test('future revision never appears in past snapshot',()=>{
 const l=makeLedger();l.append(event('v0',0),D-200);l.append(event('v1',1,120),D+200);
 assert.equal(l.snapshot('gold',D).id,'v0');assert.equal(naiveLatest(l.receipts(),'gold').id,'v1');
});
test('provider backdating cannot override trusted receipt',()=>{
 const l=makeLedger();l.append(event('v0',0),D-200);l.append(event('v1',1,150,D-1000,D-10000),D+200);
 assert.equal(naivePublishedCutoff(l.receipts(),'gold',D).id,'v1');assert.equal(l.snapshot('gold',D).id,'v0');
});
test('late-only observation abstains',()=>{
 const l=makeLedger();l.append(event('late',0),D+1);assert.equal(l.snapshot('gold',D).status,'abstain');
});
test('available earlier revision can be replaced by later pre-decision receipt',()=>{
 const l=makeLedger();l.append(event('v0',0),D-200);l.append(event('v1',1,101),D-1);
 assert.equal(l.snapshot('gold',D).id,'v1');
});
test('future-effective data cannot leak despite early receipt',()=>{
 const l=makeLedger();l.append(event('forecast',0,105,D+1),D-2);assert.equal(l.snapshot('gold',D).status,'abstain');
});
test('stale data abstains under maxAge',()=>{
 const l=makeLedger();l.append(event('old',0,100,D-10000),D-10);assert.equal(l.snapshot('gold',D,{maxAge:100}).status,'abstain');
});
test('replayed ids are rejected',()=>{
 const l=makeLedger();l.append(event('x',0),D-100);assert.throws(()=>l.append(event('x',1),D-99));
});
test('receipt clock cannot move backwards',()=>{
 const l=makeLedger();l.append(event('x',0),D-100);assert.throws(()=>l.append(event('y',1),D-101));
});
test('invalid values rejected',()=>{
 const l=makeLedger();assert.throws(()=>l.append(event('x',0,NaN),D));assert.throws(()=>l.append(event('x',0,-5),D));
});
test('receipt copy mutation does not mutate ledger',()=>{
 const l=makeLedger();l.append(event('x',0),D-100);const copy=l.receipts();copy[0].value=999;
 assert.equal(l.snapshot('gold',D).value,100);
});
test('source revision number does not override arrival time',()=>{
 const l=makeLedger();l.append(event('revision9',9,99),D-100);l.append(event('revision1',1,101),D-10);
 assert.equal(l.snapshot('gold',D).id,'revision1');
});
test('two domains remain separate',()=>{
 const l=makeLedger();l.append(event('g',0),D-100);l.append({...event('s',0,90),series:'seo'},D-50);
 assert.equal(l.snapshot('seo',D).value,90);assert.equal(l.snapshot('gold',D).value,100);
});
test('invalid query rejected',()=>{
 const l=makeLedger();assert.throws(()=>l.snapshot('gold',NaN));assert.throws(()=>l.snapshot('gold',D,{maxAge:-1}));
});
