import test from 'node:test';
import assert from 'node:assert/strict';
import {availableFeatures} from './feature-store.mjs';
import {guardedFeatures} from './provenance_guard.mjs';
const origin='2025-02-10T00:00:00Z';
const r=(source,vintage,value=5,observedAt='2025-02-01T00:00:00Z',availableAt='2025-02-02T00:00:00Z',feature='yield')=>({feature,source,vintage,value,observedAt,availableAt});
const a=r('FRED','v1'),b=r('ALFRED','v2');
test('counterexample: upstream silently chooses first provenance with equal value',()=>{
  assert.equal(availableFeatures([a,b],origin).yield.source,'FRED');
  assert.equal(availableFeatures([b,a],origin).yield.source,'ALFRED');
});
test('guard rejects equal-value ambiguous provenance independent of order',()=>{
  assert.throws(()=>guardedFeatures([a,b],origin),/Ambiguous/);
  assert.throws(()=>guardedFeatures([b,a],origin),/Ambiguous/);
});
test('exact duplicates are accepted deterministically',()=>{
  assert.deepEqual(guardedFeatures([a,{...a}],origin),guardedFeatures([a],origin));
});
test('older revision does not conflict with uniquely latest release',()=>{
  const late=r('FRED','v2',6,'2025-02-01T00:00:00Z','2025-02-04T00:00:00Z');
  assert.equal(guardedFeatures([late,a],origin).yield.value,6);
  assert.equal(guardedFeatures([a,late],origin).yield.value,6);
});
test('future revision excluded at earlier origin',()=>{
  const late=r('FRED','v2',6,'2025-02-01T00:00:00Z','2025-03-01T00:00:00Z');
  assert.equal(guardedFeatures([late,a],origin).yield.value,5);
});
test('different features do not collide',()=>{
  const seo=r('Analytics','v1',100,'2025-02-01T00:00:00Z','2025-02-02T00:00:00Z','seo_clicks');
  assert.equal(guardedFeatures([a,seo],origin).seo_clicks.value,100);
});
test('same value from two sources for SEO still ambiguous',()=>{
  const x=r('GA4','v1',200,'2025-02-01T00:00:00Z','2025-02-02T00:00:00Z','seo_clicks');
  const y=r('SearchConsole','v1',200,'2025-02-01T00:00:00Z','2025-02-02T00:00:00Z','seo_clicks');
  assert.throws(()=>guardedFeatures([x,y],origin),/Ambiguous/);
});
test('conflicting numeric ties rejected',()=>{
  assert.throws(()=>guardedFeatures([a,r('FRED','v1',6)],origin),/Ambiguous/);
});
test('invalid availability ordering rejected',()=>{
  assert.throws(()=>guardedFeatures([r('FRED','v1',5,'2025-02-03T00:00:00Z','2025-02-02T00:00:00Z')],origin),/before observation/);
});
test('staleness matches upstream for unambiguous record',()=>{
  assert.equal(guardedFeatures([a],origin,{maxAgeDays:2}).yield.stale,true);
  assert.equal(guardedFeatures([a],origin).yield.value,availableFeatures([a],origin).yield.value);
});
test('empty, invalid, and future records handled safely',()=>{
  assert.deepEqual(guardedFeatures([],origin),{});
  assert.deepEqual(guardedFeatures([r('FRED','v1',5,'2025-03-01T00:00:00Z','2025-03-02T00:00:00Z')],origin),{});
  assert.throws(()=>guardedFeatures([r('FRED','v1',NaN)],origin),/Invalid/);
  assert.throws(()=>guardedFeatures([a],origin,{maxAgeDays:-1}),/Invalid/);
});

test('semantic timestamp aliases are not false conflicts',()=>{
  const alias={...a,observedAt:'2025-02-01T02:00:00+02:00',availableAt:'2025-02-02T02:00:00+02:00'};
  assert.equal(guardedFeatures([a,alias],origin).yield.value,5);
  assert.equal(JSON.stringify(guardedFeatures([a,alias],origin)),JSON.stringify(guardedFeatures([alias,a],origin)));
});
test('two features produce stable JSON despite shuffled input order',()=>{
  const seo=r('GSC','v1',12,'2025-02-01T00:00:00Z','2025-02-02T00:00:00Z','seo_clicks');
  assert.notEqual(JSON.stringify(availableFeatures([a,seo],origin)),JSON.stringify(availableFeatures([seo,a],origin)));
  assert.equal(JSON.stringify(guardedFeatures([a,seo],origin)),JSON.stringify(guardedFeatures([seo,a],origin)));
});
test('special feature names remain own data properties',()=>{
  const weird=r('GSC','v1',7,'2025-02-01T00:00:00Z','2025-02-02T00:00:00Z','__proto__');
  const output=guardedFeatures([weird],origin);
  assert.equal(Object.hasOwn(output,'__proto__'),true);
  assert.equal(output.__proto__.value,7);
  assert.equal(Object.getPrototypeOf(output),Object.prototype);
});

test('unrecognized metadata is rejected rather than arbitrarily chosen',()=>{
  assert.throws(()=>guardedFeatures([{...a,unit:'pct'}],origin),/Invalid/);
});
test('noncanonical input key order does not alter output serialization',()=>{
  const reordered={vintage:a.vintage,source:a.source,availableAt:a.availableAt,observedAt:a.observedAt,value:a.value,feature:a.feature};
  assert.equal(JSON.stringify(guardedFeatures([a],origin)),JSON.stringify(guardedFeatures([reordered],origin)));
});
