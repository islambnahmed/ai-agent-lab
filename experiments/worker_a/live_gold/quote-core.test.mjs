import {test} from 'node:test';
import assert from 'node:assert/strict';
import {normalizeQuote, parseProviderUtcTimestamp, fetchQuote, quoteLabel, ENDPOINT, FRESH_MS} from './quote-core.mjs';

const stamp = '2026-10-10T12:00:00Z';
const now = Date.parse(stamp);
const good = (patch={}) => ({symbol:'XAU',currency:'USD',price:4200.25,updatedAt:stamp,...patch});

test('valid UTC timestamp and unchanged numeric value',()=>{
  const q=normalizeQuote(good(),now);
  assert.equal(q.price,4200.25); assert.equal(q.isFresh,true);
  assert.equal(q.ageMs,0); assert.equal(q.instrument,'XAU/USD indicative spot');
  assert.ok(Object.isFrozen(q));
});
test('valid leap day is accepted',()=>assert.equal(parseProviderUtcTimestamp('2024-02-29T23:59:59Z'),Date.parse('2024-02-29T23:59:59Z')));
test('invalid nonleap February 29 is rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-02-29T12:00:00Z'),/calendar/));
test('invalid February 30 is rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-02-30T12:00:00Z'),/calendar/));
test('invalid April 31 is rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-04-31T12:00:00Z'),/calendar/));
test('invalid hour 24 rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-10-10T24:00:00Z'),/calendar|timestamp/));
test('invalid leap second rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-10-10T12:00:60Z'),/timestamp/));
test('invalid minute rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-10-10T12:60:00Z'),/timestamp/));
test('timezone offset not allowed',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-10-10T12:00:00+00:00'),/UTC/));
test('fractional precision up to nine digits allowed',()=>assert.equal(parseProviderUtcTimestamp('2026-10-10T12:00:00.123456789Z'),now+123));
test('fractional precision above nine digits rejected',()=>assert.throws(()=>parseProviderUtcTimestamp('2026-10-10T12:00:00.1234567890Z'),/UTC/));
test('bad instrument and currency rejected',()=>{for(const patch of [{symbol:'XAG'},{currency:'EUR'}])assert.throws(()=>normalizeQuote(good(patch),now),/instrument/)});
test('bad prices rejected',()=>{for(const price of [0,-1,Infinity,NaN,'4200',1_000_001])assert.throws(()=>normalizeQuote(good({price}),now),/price/)});
test('bad response object rejected',()=>{for(const x of [null,[],42,'hi'])assert.throws(()=>normalizeQuote(x,now),/object/)});
test('bad observation clock rejected',()=>assert.throws(()=>normalizeQuote(good(),NaN),/clock/));
test('freshness boundary',()=>{assert.equal(normalizeQuote(good(),now+FRESH_MS).isFresh,true);assert.equal(normalizeQuote(good(),now+FRESH_MS+1).isFresh,false);});
test('provider future skew over two minutes rejected',()=>assert.throws(()=>normalizeQuote(good(),now-120001),/future/));
test('small clock skew accepted and age floored',()=>assert.equal(normalizeQuote(good(),now-120000).ageMs,0));
test('stale quote visibly labeled',()=>assert.match(quoteLabel(normalizeQuote(good(),now+FRESH_MS+1)),/قديم/));
test('HTTP failure rejects and endpoint fixed',async()=>{await assert.rejects(fetchQuote({nowMs:now,fetchImpl:async url=>{assert.equal(url,ENDPOINT);return{ok:false,status:503}}}),/503/)});
test('HTTP success validates schema and method',async()=>{const q=await fetchQuote({nowMs:now,fetchImpl:async(url,opts)=>{assert.equal(url,ENDPOINT);assert.equal(opts.method,'GET');return{ok:true,json:async()=>good()}}});assert.equal(q.price,4200.25)});
test('HTTP success with malformed calendar rejects',async()=>await assert.rejects(fetchQuote({nowMs:Date.parse('2026-03-02T12:00:00Z'),fetchImpl:async()=>({ok:true,json:async()=>good({updatedAt:'2026-02-30T12:00:00Z'})})}),/calendar/));
