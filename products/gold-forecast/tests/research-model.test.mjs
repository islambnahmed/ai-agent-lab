import test from 'node:test';import assert from 'node:assert/strict';
import {fitRidgeAt} from '../research-model.mjs';
test('Research Ridge excludes unmatured labels and future context',()=>{
  const prices=Array.from({length:140},(_,i)=>2000*Math.exp(i*.001+Math.sin(i)*.005));
  const vectors=prices.map((_,i)=>[Math.sin(i),Math.cos(i)]);
  const original=fitRidgeAt(prices,vectors,100,7);
  const changedPrices=prices.map((p,i)=>i>100?p*10:p),changedVectors=vectors.map((v,i)=>i>100?[999,999]:v);
  assert.deepEqual(fitRidgeAt(changedPrices,changedVectors,100,7),original);
  assert.equal(original.trainingRows,94);
});
test('Missing macro origin and insufficient matured labels cannot predict',()=>{
  const p=Array(100).fill(2000),v=p.map(()=>[1]);v[80]=null;
  assert.equal(fitRidgeAt(p,v,80,7),null);assert.equal(fitRidgeAt(p,v,20,7),null);
});
