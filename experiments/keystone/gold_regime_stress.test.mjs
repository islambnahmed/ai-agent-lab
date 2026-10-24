import test from 'node:test';
import assert from 'node:assert/strict';
import {generate,evaluate,run,SCENARIOS,HORIZONS,MODELS} from './gold_regime_stress.mjs';

test('deterministic and positive synthetic series, with distinct regimes', () => {
  const a=generate('iid',42),b=generate('iid',42);
  assert.deepEqual(a,b);
  assert.equal(a.length,360);
  assert(a.every(x=>Number.isFinite(x)&&x>0));
  assert.notDeepEqual(a,generate('momentum',42));
});
test('selection excludes labels crossing the boundary; audit excludes future labels', () => {
  const prices=generate('iid',123);
  for(const h of HORIZONS){
    const sel=evaluate(prices,h,'selection'), audit=evaluate(prices,h,'audit');
    assert.equal(sel.n,Math.ceil((240-h-80)/h));
    assert.equal(audit.n,Math.ceil((360-h-240)/h));
    for(const model of MODELS) assert(Number.isFinite(sel.mae[model])&&Number.isFinite(audit.mae[model]));
  }
});
test('changing audit-only future cannot affect selection metrics', () => {
  const a=generate('iid',91),b=a.slice();
  for(let i=240;i<b.length;i++) b[i]*=1.3;
  for(const h of HORIZONS) assert.deepEqual(evaluate(a,h,'selection'),evaluate(b,h,'selection'));
});
test('report is reproducible and bounded, with no real-world performance claims', () => {
  const a=run({seeds:2}),b=run({seeds:2});
  assert.deepEqual(a,b);
  assert.equal(a.results.length,SCENARIOS.length*HORIZONS.length);
  assert.equal(a.kind,'synthetic_falsification_only');
  assert.throws(()=>run({seeds:1}));
  assert.throws(()=>run({seeds:65}));
});
