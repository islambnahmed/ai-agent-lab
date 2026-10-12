import test from 'node:test';
import assert from 'node:assert/strict';
import {parsePriceCSV,evaluateSeries,HORIZON_MS,utcMs} from './gold-site-offline-eval.mjs';
const T=Date.parse('2026-09-01T00:00:00.000Z');
const series=(n,fn)=>Array.from({length:n},(_,i)=>({t:T+i*60_000,price:fn(i),source:'synthetic'}));
const opts={holdoutStartMs:T+300*60_000,strideMs:HORIZON_MS};
const csv=(arr)=>'timestamp,price,source\n'+arr.map(x=>`${new Date(x.t).toISOString()},${x.price},${x.source}`).join('\n');
test('strict CSV parser rejects nonmonotonic time, duplicates, invalid prices and mixed sources',()=>{
 const rows=series(2,i=>4100+i);assert.deepEqual(parsePriceCSV(csv(rows)),rows);
 assert.throws(()=>parsePriceCSV(csv([rows[1],rows[0]])),/non-monotonic/);
 assert.throws(()=>parsePriceCSV(csv([rows[0],rows[0]])),/non-monotonic/);
 assert.throws(()=>parsePriceCSV(csv([{...rows[0],price:-1}])),/Invalid price/);
 assert.throws(()=>parsePriceCSV(csv([rows[0],{...rows[1],source:'another'}])),/Mixed/);
 assert.throws(()=>utcMs('2026-02-30T00:00:00Z'),/Invalid/);
});
test('fixed momentum wins on synthetic linear trend, not proof of real market skill',()=>{
 const s=evaluateSeries(series(2000,i=>4000+i*0.1),opts);
 assert.ok(s.evaluated>=15);assert.equal(s.coverage,1);
 assert.ok(s.momentum30.mae<1e-9);assert.ok(s.persistence.mae>7);
 assert.ok(s.pairedSkillVsPersistence>0.999);
});
test('persistence beats momentum on alternating noise, showing model dependence',()=>{
 const s=evaluateSeries(series(2000,i=>4000+(i%2?1:-1)),opts);
 assert.ok(s.evaluated>=15);assert.equal(s.coverage,1);
 assert.ok(s.persistence.mae<=s.momentum30.mae);
});
test('missing target quotes count in coverage denominator and cannot be cherry-picked',()=>{
 const all=series(1300,i=>4000+i/100);
 const gaps=all.filter(x=>x.t<T+950*60_000||x.t>T+1050*60_000);
 const s=evaluateSeries(gaps,{holdoutStartMs:T+600*60_000,strideMs:75*60_000});
 assert.ok(s.missing>=1);assert.ok(s.coverage<1);assert.equal(s.evaluated+s.missing,s.matured);
});
test('future targets are excluded from denominator rather than scored as misses',()=>{
 const s=evaluateSeries(series(450,i=>4000+i),opts);
 assert.ok(s.notMatured>=1);assert.equal(s.evaluated+s.missing,s.matured);
});
test('no holdout maturities returns null errors rather than fake zero',()=>{
 const s=evaluateSeries(series(50,i=>4000+i),{holdoutStartMs:T+49*60_000});
 assert.equal(s.matured,0);assert.equal(s.persistence.mae,null);assert.equal(s.coverage,null);
});
test('evaluation is deterministic and uses no future prices for issued predictions',()=>{
 const a=series(600,i=>4000+i*0.02);
 const first=evaluateSeries(a,{holdoutStartMs:T+300*60_000,asOfMs:T+500*60_000});
 const b=[...a,...series(100,i=>4100+i).map((r,i)=>({...r,t:T+(600+i)*60_000}))];
 const second=evaluateSeries(b,{holdoutStartMs:T+300*60_000,asOfMs:T+500*60_000});
 assert.deepEqual(first,second);
});
