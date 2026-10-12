import test from 'node:test';
import assert from 'node:assert/strict';
import {validateSpotQuote} from '../spot-quote.mjs';
const asOf='2026-10-12T12:00:00Z';
const good=()=>({updated:'2026-10-12T11:55:00Z',metals:[{symbol:'XAU',ask:'4050.25',bid:'4048.10'}]});
test('accepts a current ordered XAU quote',()=>{
  const q=validateSpotQuote(good(),asOf);
  assert.equal(q.ask,4050.25);assert.equal(q.bid,4048.1);
});
test('rejects crossed bid/ask',()=>{const q=good();q.metals[0].bid='4051';assert.throws(()=>validateSpotQuote(q,asOf),/Crossed/);});
test('rejects nonpositive and invalid prices',()=>{
  for(const p of ['0','-2','NaN','Infinity',null]){const q=good();q.metals[0].ask=p;assert.throws(()=>validateSpotQuote(q,asOf));}
});
test('rejects missing, ambiguous, and stale timestamps',()=>{
  for(const time of [undefined,'2026-10-12T11:55:00','2026-10-10T11:55:00Z']){const q=good();q.updated=time;assert.throws(()=>validateSpotQuote(q,asOf));}
});
test('rejects future quotes beyond tolerance',()=>{const q=good();q.updated='2026-10-12T12:10:00Z';assert.throws(()=>validateSpotQuote(q,asOf),/Future/);});
test('rejects duplicate XAU entries',()=>{const q=good();q.metals.push({...q.metals[0]});assert.throws(()=>validateSpotQuote(q,asOf),/exactly one/);});
