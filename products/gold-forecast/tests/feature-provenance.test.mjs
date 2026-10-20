import test from 'node:test';
import assert from 'node:assert/strict';
import {availableFeatures} from '../feature-store.mjs';

const first={feature:'yield',value:2,observedAt:'2025-01-01T00:00:00Z',availableAt:'2025-01-02T12:00:00Z',source:'A',vintage:'v1'};
const revised={...first,value:3,availableAt:'2025-01-03T12:00:00Z',vintage:'v2'};
const origin='2025-01-04T12:00:00Z';

test('same-value duplicate with different source fails regardless of order',()=>{
  const other={...first,source:'B'};
  for(const rows of [[first,other],[other,first]])assert.throws(()=>availableFeatures(rows,origin),/Conflicting/);
});

test('newer revision cannot hide an older provenance conflict',()=>{
  const other={...first,source:'B'};
  for(const rows of [[revised,first,other],[first,other,revised]])assert.throws(()=>availableFeatures(rows,origin),/Conflicting/);
});

test('exact duplicates and valid revisions remain supported',()=>{
  assert.equal(availableFeatures([first,{...first}],origin).yield.value,2);
  for(const rows of [[first,revised],[revised,first]])assert.equal(availableFeatures(rows,origin).yield.value,3);
});

test('future revision conflicts do not leak into earlier origins',()=>{
  const other={...revised,source:'B'};
  assert.equal(availableFeatures([first,revised,other],'2025-01-02T15:00:00Z').yield.value,2);
  assert.throws(()=>availableFeatures([first,revised,other],origin),/Conflicting/);
});
