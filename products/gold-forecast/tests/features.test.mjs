import test from 'node:test';
import assert from 'node:assert/strict';
import {availableFeatures} from '../feature-store.mjs';
const record=(value,availableAt)=>({feature:'yield',value,observedAt:'2025-01-01T00:00:00Z',availableAt,source:'test',vintage:availableAt});
test('observation date cannot reveal a release published after the prediction',()=>{
  const row=record(2,'2025-01-03T15:00:00Z');
  assert.deepEqual(availableFeatures([row],'2025-01-02T12:00:00Z'),{});
  assert.equal(availableFeatures([row],'2025-01-03T16:00:00Z').yield.value,2);
});
test('future data revision cannot change the feature known at an earlier origin',()=>{
  const rows=[record(2,'2025-01-02T12:00:00Z'),record(3,'2025-02-01T12:00:00Z')];
  assert.equal(availableFeatures(rows,'2025-01-10T12:00:00Z').yield.value,2);
  assert.equal(availableFeatures(rows,'2025-02-02T12:00:00Z').yield.value,3);
  assert.equal(availableFeatures(rows,'2025-02-02T12:00:00Z').yield.stale,true);
});
test('features must have honest publication order and cannot conflict within one vintage',()=>{
  assert.throws(()=>availableFeatures([record(2,'2024-12-31T12:00:00Z')],'2025-01-10T12:00:00Z'),/before observation/);
  assert.throws(()=>availableFeatures([record(2,'2025-01-02T12:00:00Z'),record(3,'2025-01-02T12:00:00Z')],'2025-01-10T12:00:00Z'),/Conflicting/);
});
