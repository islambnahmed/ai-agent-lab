import test from 'node:test';
import assert from 'node:assert/strict';
import {directionDiagnostics} from '../direction-diagnostics.mjs';

const row = (point, actual, originClose=100) => ({point, actual, originClose});

test('persistence cannot earn directional credit from unchanged prices', () => {
  const r=directionDiagnostics([row(100,100),row(100,110),row(100,90)]);
  assert.equal(r.ternarySignMatchPct,100/3);
  assert.equal(r.signalCoveragePct,0);
  assert.equal(r.directionalHitPctWhenSignaled,null);
  assert.equal(r.upDownHitPctExcludingFlatOutcomes,null);
  assert.equal(r.flatHits,1);
  assert.equal(r.actualFlat,1);
});

test('up/down signal accuracy is separated from flat realized outcomes', () => {
  const r=directionDiagnostics([row(110,120),row(110,100),row(90,120),row(90,80),row(100,100)]);
  assert.equal(r.predictedDirectional,4);
  assert.equal(r.directionalHits,2);
  assert.equal(r.signalCoveragePct,80);
  assert.equal(r.directionalHitPctWhenSignaled,50);
  assert.equal(r.upDownHitPctExcludingFlatOutcomes,200/3);
  assert.equal(r.ternarySignMatchPct,60);
  assert.equal(r.confusion.up.flat,1);
});

test('always-up forecast on always-down outcomes scores zero', () => {
  const r=directionDiagnostics([row(101,99),row(101,99)]);
  assert.equal(r.signalCoveragePct,100);
  assert.equal(r.directionalHitPctWhenSignaled,0);
  assert.equal(r.ternarySignMatchPct,0);
});

test('all flat outcomes are not an up/down win', () => {
  const r=directionDiagnostics([row(100,100),row(100,100)]);
  assert.equal(r.ternarySignMatchPct,100);
  assert.equal(r.directionalHitPctWhenSignaled,null);
});

test('rejects invalid rows and empty input', () => {
  assert.throws(()=>directionDiagnostics([]));
  assert.throws(()=>directionDiagnostics([row(Infinity,100)]));
  assert.throws(()=>directionDiagnostics([{}]));
});
