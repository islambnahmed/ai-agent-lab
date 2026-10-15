import test from 'node:test';
import assert from 'node:assert/strict';
import {metrics} from '../forecast.mjs';

const row=(originClose,point,actual)=>({originClose,point,actual});

test('persistence abstains even when realized price is unchanged',()=>{
  const result=metrics([row(100,100,100),row(100,100,110),row(100,100,90)]);
  assert.equal(result.directionAccuracy,null);
  assert.equal(result.directionCallCount,0);
  assert.equal(result.directionAbstentionCount,3);
  assert.equal(result.directionFlatActualCount,1);
  assert.equal(result.directionParticipationPct,0);
});

test('accuracy conditions on nonzero directional calls, not abstentions',()=>{
  const result=metrics([
    row(100,101,105), // correct up
    row(100,99,95),   // correct down
    row(100,101,95),  // wrong up
    row(100,100,100), // abstain
    row(100,99,100),  // wrong down (flat actual)
  ]);
  assert.equal(result.n,5);
  assert.equal(result.directionCallCount,4);
  assert.equal(result.directionHitCount,2);
  assert.equal(result.directionMissCount,2);
  assert.equal(result.directionAbstentionCount,1);
  assert.equal(result.directionParticipationPct,80);
  assert.equal(result.directionAccuracy,50);
  assert.equal(result.directionAccuracyOnCallsPct,50);
  assert.equal(result.directionFlatActualCount,2);
});

test('wrong directional call on unchanged actual is not a hit',()=>{
  const result=metrics([row(100,101,100)]);
  assert.equal(result.directionAccuracy,0);
  assert.equal(result.directionHitCount,0);
});

test('ordinary price errors remain unchanged by directional metrics',()=>{
  const result=metrics([row(100,100,110),row(100,90,100)]);
  assert.equal(result.mae,10);
  assert.equal(result.rmse,10);
  assert.equal(result.mape,100*(10/110+10/100)/2);
});

test('empty evaluation set is rejected',()=>{
  assert.throws(()=>metrics([]),/No evaluation rows/);
});
