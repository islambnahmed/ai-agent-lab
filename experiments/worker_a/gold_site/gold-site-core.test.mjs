import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeQuote,createBaseline,evaluatePending,appendIfNew,loadLedger,HORIZON_MS} from './gold-site-core.mjs';
const T=Date.parse('2026-10-12T10:00:00.000Z');
const raw=(updatedAt='2026-10-12T10:00:00Z',price=4100)=>({symbol:'XAU',currency:'USD',updatedAt,price});
const quote=(at=T,price=4100,updatedAt=new Date(at).toISOString())=>normalizeQuote(raw(updatedAt,price),at);
test('75-minute issuance anchored persistence',()=>{
 const f=createBaseline(quote(),T);assert.equal(f.prediction,4100);
 assert.equal(Date.parse(f.targetAt)-Date.parse(f.issuedAt),HORIZON_MS);assert.equal(f.status,'pending');
});
test('reject stale, future, wrong instrument and invalid prices',()=>{
 assert.throws(()=>createBaseline(quote(T,4100,new Date(T-11*60000).toISOString()),T),/stale/);
 assert.throws(()=>normalizeQuote(raw(new Date(T+3*60000).toISOString()),T),/ahead/);
 assert.throws(()=>createBaseline(quote(T,4100,new Date(T+60000).toISOString()),T),/not yet available/);
 assert.throws(()=>normalizeQuote({...raw(),symbol:'XAG'},T),/instrument/);
 assert.throws(()=>normalizeQuote(raw(undefined,-1),T),/price/);
});
test('before target remains pending',()=>{
 const f=createBaseline(quote(),T);assert.equal(evaluatePending(f,quote(T+74*60000)),f);
});
test('timely outcome and audit caveat',()=>{
 const f=createBaseline(quote(),T),e=evaluatePending(f,quote(T+HORIZON_MS,4103));
 assert.equal(e.status,'evaluated');assert.equal(e.outcome.absoluteError,3);
 assert.equal(e.outcome.captureEvidence,'self-reported-browser-clock');
});
test('late outcome expires rather than cherry-picking',()=>{
 const f=createBaseline(quote(),T);assert.equal(evaluatePending(f,quote(T+HORIZON_MS+11*60000)).status,'expired');
});
test('delayed old capture cannot be scored',()=>{
 const f=createBaseline(quote(),T),t=T+HORIZON_MS;
 assert.equal(evaluatePending(f,quote(t+11*60000,4102,new Date(t).toISOString())).status,'pending');
});
test('ledger deduplicates and rejects invalid shape',()=>{
 const f=createBaseline(quote(),T);assert.equal(appendIfNew([f],f).length,1);
 assert.equal(loadLedger(JSON.stringify([f])).length,1);assert.throws(()=>loadLedger('{}'),/ledger/);
});
test('invalid calendar timestamp rejected',()=>{
 assert.throws(()=>normalizeQuote(raw('2026-02-30T10:00:00Z'),T),/timestamp/);
});
