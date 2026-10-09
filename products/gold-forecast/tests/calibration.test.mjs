import test from 'node:test';
import assert from 'node:assert/strict';
import {logError,calibrateMultiplicativeInterval,intervalAt,empiricalCoverage} from '../calibration.mjs';
const pairs=(predicted,actual,n=50)=>Array.from({length:n},()=>({predicted,actual}));
test('underprediction: MAPE coverage can be 100% while displayed band covers 0%',()=>{
  const p=pairs(90,100),oldMAPE=Math.abs(90-100)/100;
  assert.equal(p.filter(({predicted,actual})=>Math.abs(predicted-actual)/actual<=oldMAPE).length,50);
  assert.equal(p.filter(({predicted,actual})=>actual>=predicted*(1-oldMAPE)&&actual<=predicted*(1+oldMAPE)).length,0);
  const {logRadius}=calibrateMultiplicativeInterval(p);
  const {lower,upper}=intervalAt(90,logRadius);
  assert.ok(lower<100 && upper>=100-1e-9);
  assert.equal(empiricalCoverage(p,logRadius),100);
});
test('overprediction transfer: log bands and direct coverage remain aligned',()=>{
  const p=pairs(110,100),{logRadius}=calibrateMultiplicativeInterval(p);
  const {lower,upper}=intervalAt(110,logRadius);
  assert.ok(lower<=100+1e-9 && upper>100);
  assert.equal(empiricalCoverage(p,logRadius),100);
});
test('coverage measures the displayed interval, not unrelated MAPE threshold',()=>{
  const p=[...pairs(90,100,8),...pairs(100,100,2)];
  const {logRadius}=calibrateMultiplicativeInterval(p);
  assert.equal(empiricalCoverage(p,logRadius),100);
  assert.equal(empiricalCoverage(pairs(50,100),logRadius),0);
});
test('invalid and empty inputs fail closed',()=>{
  assert.throws(()=>logError(0,100));
  assert.throws(()=>logError(NaN,100));
  assert.throws(()=>calibrateMultiplicativeInterval([]));
  assert.throws(()=>calibrateMultiplicativeInterval([{predicted:1,actual:-1}]));
  assert.throws(()=>empiricalCoverage([],0.1));
  assert.throws(()=>intervalAt(0,0.1));
});
test('log error is symmetric under reciprocal price ratios',()=>{
  assert.ok(Math.abs(logError(90,100)-logError(100,90))<1e-14);
});
