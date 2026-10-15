import test from 'node:test';
import assert from 'node:assert/strict';
import {directionalDiagnostics as diag,legacyDirectionAccuracy as legacy} from '../directional-diagnostics.mjs';
const row=(point,actual,originClose=100)=>({point,actual,originClose});
const alternating=Array.from({length:100},(_,i)=>row(100,i%2?90:110));
const approx=(a,b,tol=1e-9)=>assert.ok(Math.abs(a-b)<tol,`${a} vs ${b}`);
test('baseline persistence has 0 legacy accuracy despite zero directional bets',()=>{
  assert.equal(legacy(alternating),0);
  const d=diag(alternating);
  assert.equal(d.issuedSignals,0);assert.equal(d.abstained,100);
  assert.equal(d.hitRateOnIssuedPct,null);assert.equal(d.priceMae,10);
});
test('sub-basis-point epsilon can game legacy accuracy without price improvement',()=>{
  const jitter=alternating.map(r=>({...r,point:100+1e-9}));
  assert.equal(legacy(jitter),50);
  assert.equal(diag(jitter).issuedSignals,0);
  approx(diag(jitter).priceMae,diag(alternating).priceMae);
});
test('meaningful correct directional signals score 100%',()=>{
  const a=alternating.map(r=>({...r,point:r.actual}));
  const d=diag(a);assert.equal(d.issuedSignals,100);
  assert.equal(d.hitRateOnIssuedPct,100);assert.equal(d.hitRateOnSignaledMaterialMovesPct,100);
});
test('meaningful wrong signals score zero',()=>{
  const a=alternating.map(r=>({...r,point:200-r.actual}));
  assert.equal(diag(a).hitRateOnIssuedPct,0);
});
test('flat actual is not silently scored as correct positive direction',()=>{
  const d=diag([row(110,100),row(100,100)]);
  assert.equal(d.flatActualMoves,2);assert.equal(d.issuedSignals,1);
  assert.equal(d.hitRateOnIssuedPct,0);assert.equal(d.hitRateOnSignaledMaterialMovesPct,null);
});
test('scaling prices preserves bps signal decisions and rates',()=>{
  const a=[row(100.1,110),row(99.8,90),row(100.000001,100)];
  const b=a.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,v*1000])));
  const x=diag(a,{signalDeadbandBps:2}),y=diag(b,{signalDeadbandBps:2});
  for(const k of ['issuedSignals','abstained','signalRatePct','hitRateOnIssuedPct','materialActualMoves'])assert.equal(x[k],y[k]);
});
test('same capability transfers to energy-demand forecasting',()=>{
  const electricity=[row(500,540,500),row(500,480,500),row(510,530,500)];
  const d=diag(electricity,{signalDeadbandBps:20});
  assert.equal(d.issuedSignals,1);assert.equal(d.hitRateOnIssuedPct,100);
});
test('threshold equality is abstention',()=>{
  const d=diag([row(101,110)],{signalDeadbandBps:100});
  assert.equal(d.issuedSignals,0);
});
test('invalid inputs fail closed',()=>{
  for(const rows of [[],[row(NaN,100)],[row(100,Infinity)],[row(100,100,0)],null])assert.throws(()=>diag(rows));
  for(const opts of [{signalDeadbandBps:-1},{signalDeadbandBps:NaN},{actualDeadbandBps:10000}])assert.throws(()=>diag([row(100,100)],opts));
});
test('actual deadband excludes immaterial realized moves from material count',()=>{
  const d=diag([row(110,100.001),row(110,110)],{actualDeadbandBps:1});
  assert.equal(d.materialActualMoves,1);assert.equal(d.flatActualMoves,1);
  assert.equal(d.hitRateOnIssuedPct,50);
});
test('majority class is hindsight-only and not a valid deployed benchmark',()=>{
  const a=[row(100,110),row(100,110),row(100,90)];
  assert.ok(diag(a).retrospectiveMajorityClassHitRatePct>50);
  assert.equal(diag(a).hitRateOnIssuedPct,null);
});
