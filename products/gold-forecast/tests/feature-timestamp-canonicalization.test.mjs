import test from 'node:test';
import assert from 'node:assert/strict';
import {availableFeatures} from '../feature-store.mjs';

const first={feature:'yield',value:2,observedAt:'2025-01-01T00:00:00Z',availableAt:'2025-01-02T12:00:00Z',source:'A',vintage:'v1'};
const equivalent={...first,observedAt:'2024-12-31T19:00:00-05:00',availableAt:'2025-01-02T14:00:00+02:00'};
const revised={...first,value:3,availableAt:'2025-01-03T12:00:00Z',vintage:'v2'};
const origin='2025-01-04T12:00:00Z';

test('equivalent timezone offsets for both timestamps do not create fake provenance conflicts',()=>{
  for(const rows of [[first,equivalent],[equivalent,first]]){
    const result=availableFeatures(rows,origin).yield;
    assert.equal(result.value,2);
    assert.equal(result.ageDays,3.5);
  }
});

test('canonical output is order-independent and UTC normalized',()=>{
  const a=availableFeatures([first,equivalent],origin);
  const b=availableFeatures([equivalent,first],origin);
  assert.deepEqual(a,b);
  assert.equal(a.yield.observedAt,'2025-01-01T00:00:00.000Z');
  assert.equal(a.yield.availableAt,'2025-01-02T12:00:00.000Z');
});

test('same instant but different source, vintage or value still fails regardless of order',()=>{
  for(const change of [{source:'B'},{vintage:'v-other'},{value:4}]){
    const conflict={...equivalent,...change};
    for(const rows of [[first,conflict],[conflict,first]])assert.throws(()=>availableFeatures(rows,origin),/Conflicting/);
  }
});

test('newer revision cannot hide conflict in old equivalent-time vintage',()=>{
  const conflict={...equivalent,source:'B'};
  for(const rows of [[revised,first,conflict],[first,revised,conflict]])assert.throws(()=>availableFeatures(rows,origin),/Conflicting/);
});

test('valid newer revision wins and future revision cannot leak',()=>{
  for(const rows of [[first,equivalent,revised],[revised,equivalent,first]])assert.equal(availableFeatures(rows,origin).yield.value,3);
  assert.equal(availableFeatures([first,{...revised,source:'B'}],'2025-01-02T15:00:00Z').yield.value,2);
});

test('timezone-less timestamps remain invalid',()=>{
  assert.throws(()=>availableFeatures([{...first,observedAt:'2025-01-01T00:00:00'}],origin),/timezone/);
});
