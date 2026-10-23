import test from 'node:test';
import assert from 'node:assert/strict';
import {receiptBoundary,compareAtActual} from './receipt_boundaries.mjs';
const base={calendar:'observations',targetDate:null,originDate:'2026-10-11',baseline:4207.98};
const h1={...base,horizon:1,point:4207.98};
const h7={...base,horizon:7,point:4225.483424799358};
const h30={...base,horizon:30,point:4183.958131173134};
test('1-close model is exactly identical to persistence for any positive actual',()=>{
  assert.equal(receiptBoundary(h1).classification,'identical_to_persistence');
  for(const actual of [1,100,4000,4207.98,5000,100000])assert.equal(compareAtActual(h1,actual).winner,'tie');
});
test('7-close threshold is exact and not a realized score',()=>{
  const b=receiptBoundary(h7);
  assert.equal(b.earliestPossibleTargetDate,'2026-10-18');
  assert.equal(b.actualTargetDate,'unknown');
  assert.ok(Math.abs(b.threshold-4216.731712399679)<1e-9);
  assert.equal(compareAtActual(h7,4000).winner,'baseline');
  assert.equal(compareAtActual(h7,4300).winner,'model');
  assert.equal(compareAtActual(h7,b.threshold).winner,'tie');
});
test('30-close threshold is exact and target not yet necessarily mature',()=>{
  const b=receiptBoundary(h30);
  assert.equal(b.earliestPossibleTargetDate,'2026-11-10');
  assert.ok(Math.abs(b.threshold-4195.969065586567)<1e-9);
  assert.equal(compareAtActual(h30,4000).winner,'model');
  assert.equal(compareAtActual(h30,4300).winner,'baseline');
  assert.equal(compareAtActual(h30,b.threshold).winner,'tie');
});
test('irregular observations cannot be assigned an exact target day',()=>{
  assert.equal(receiptBoundary(h7).actualTargetDate,'unknown');
  assert.throws(()=>receiptBoundary({...h7,targetDate:'2026-10-18'}));
});
test('bad and nonpositive inputs rejected',()=>{
  for(const actual of [0,-1,NaN,Infinity])assert.throws(()=>compareAtActual(h7,actual));
  for(const bad of [{...h7,point:-1},{...h7,baseline:NaN},{...h7,originDate:'2026-02-30'}])assert.throws(()=>receiptBoundary(bad));
});
test('sign of absolute-error difference matches boundary for random actual prices',()=>{
  let state=991;
  for(const receipt of [h7,h30]){
    for(let i=0;i<10000;i++){
      state=(state*1664525+1013904223)>>>0;
      const actual=1+(state/4294967296)*10000;
      const got=compareAtActual(receipt,actual).winner;
      const threshold=receiptBoundary(receipt).threshold;
      const expectModel=receipt.point>receipt.baseline?actual>threshold:actual<threshold;
      assert.equal(got,expectModel?'model':'baseline');
    }
  }
});
