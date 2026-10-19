import test from 'node:test';
import assert from 'node:assert/strict';
import {directionMetrics} from '../direction-metrics.mjs';
const row = (point, actual, originClose=100) => ({point, actual, originClose});
test('persistence abstains rather than being called directionally wrong', () => {
  const m = directionMetrics([row(100,110),row(100,90),row(100,100)]);
  assert.equal(m.directionalCalls,0);
  assert.equal(m.directionalHitRatePct,null);
  assert.equal(m.ternaryExactMatchPct,100/3);
  assert.equal(m.flatActualRatePct,100/3);
});
test('directional denominator excludes abstentions but not flat realized outcomes', () => {
  const m=directionMetrics([row(110,120),row(90,110),row(110,100),row(100,120)]);
  assert.equal(m.directionalCalls,3);
  assert.equal(m.directionalHitRatePct,100/3);
  assert.equal(m.directionalCallRatePct,75);
});
test('always-up can be 100% when the sample only rises; no baseline significance implied',()=>{
  const m=directionMetrics([row(110,120),row(105,120)]);
  assert.equal(m.directionalHitRatePct,100);
  assert.equal(m.ternaryExactMatchPct,100);
});
test('all-flat outcome and all-flat predictions are descriptive, not directional skill',()=>{
  const m=directionMetrics([row(100,100),row(100,100)]);
  assert.equal(m.ternaryExactMatchPct,100);
  assert.equal(m.directionalHitRatePct,null);
  assert.equal(m.directionalCallRatePct,0);
});
test('rejects invalid numbers and empty input',()=>{
  assert.throws(()=>directionMetrics([]));
  assert.throws(()=>directionMetrics([row(NaN,100)]));
  assert.throws(()=>directionMetrics([row(101,0)]));
});
