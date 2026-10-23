import test from 'node:test';
import assert from 'node:assert/strict';
import {assessComparison,evaluatePriceCandidates} from './definition_gate.mjs';
const base={instrument:'XAU',unit:'USD/troy_oz',date:'2026-10-18',closeMethod:'dealer_last_capture',clockBasis:'UTC',releaseEvidence:'archive'};
const a={...base,source:'vendor-a',price:4192.32};
const b={...base,source:'vendor-b',price:4165.56};
test('different close methods cannot certify a mismatch',()=>assert.deepEqual(assessComparison(a,{...b,closeMethod:'site_close_unspecified'}).status,'not_comparable'));
test('unknown clock basis is not comparable',()=>assert.equal(assessComparison(a,{...b,clockBasis:null}).status,'not_comparable'));
test('same named source is not independent',()=>assert.equal(assessComparison(a,{...a}).status,'not_independent'));
test('missing independent release evidence is not certified',()=>assert.equal(assessComparison(a,{...b,releaseEvidence:null}).status,'not_certified'));
test('comparable but divergent sources flag discrepancy',()=>{const x=assessComparison(a,b);assert.equal(x.status,'divergent_by_threshold');assert.ok(Math.abs(x.deltaUsd-26.76)<1e-8)});
test('comparable close prices are consistent by threshold, not certified',()=>assert.equal(assessComparison(a,{...b,price:4193}).status,'consistent_by_threshold'));
test('ranking stays baseline for both incompatible observations',()=>{
  const x=evaluatePriceCandidates({point:4225.483424799358,baseline:4207.98,observations:[a,b]});
  assert.ok(Math.abs(x.threshold-4216.731712399678)<1e-9);
  assert.deepEqual(x.rankings.map(r=>r.winner),['baseline','baseline']);
});
test('ranking flips above midpoint',()=>assert.equal(evaluatePriceCandidates({point:4225.483424799358,baseline:4207.98,observations:[{price:4230,source:'test'}]}).rankings[0].winner,'model'));
test('invalid price is rejected',()=>assert.throws(()=>assessComparison({...a,price:NaN},b)));
