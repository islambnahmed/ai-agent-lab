import test from 'node:test';
import assert from 'node:assert/strict';
import {validateHistoricalCloses as gate} from '../historical-integrity.mjs';
const day=i=>new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10);
const data=n=>Array.from({length:n},(_,i)=>({date:day(i),price:2600+i}));
const asOf='2025-09-20T12:00:00Z';
const check=(rows,opts={})=>gate(rows,{asOf,requireFresh:false,minRows:1,...opts});
test('sort and accept exact duplicates',()=>{
  const r=check([{date:day(1),price:100},{date:day(0),close:'90'},{date:day(1),price:100}]);
  assert.deepEqual(r.series,[{date:day(0),price:90},{date:day(1),price:100}]);
});
test('reject future observations even when historical count is sufficient',()=>{
  assert.throws(()=>check([...data(180),{date:'2025-10-01',price:1e7}]),/Future-dated/);
});
test('exclude current UTC day provisional close',()=>{
  const r=check([...data(180),{date:'2025-09-20',price:1e7}]);
  assert.equal(r.excludedSameDay,1);assert.ok(r.series.every(x=>x.date<'2025-09-20'));
});
test('reject conflicting same-day duplicate',()=>{
  assert.throws(()=>check([{date:day(1),price:100},{date:day(1),price:101}]),/Conflicting duplicate/);
});
test('reject impossible dates and timestamps without timezone',()=>{
  assert.throws(()=>check([{date:'2025-02-30',price:100}]),/Invalid observation date/);
  assert.throws(()=>check([{t:'2025-02-01T12:00:00',price:100}]),/timezone/);
  assert.throws(()=>check([{t:'2025-02-30T12:00:00Z',price:100}]),/calendar date/);
});
test('reject missing, nonpositive and nonfinite prices',()=>{
  for(const price of ['',0,-1,Infinity,NaN,'not-a-number'])
    assert.throws(()=>check([{date:day(0),price}]),/Invalid close price/);
});
test('stale completed close blocks live forecast',()=>{
  assert.throws(()=>check(data(180),{requireFresh:true,maxAgeDays:7}),/Stale/);
});
test('fresh completed series accepted with measured age',()=>{
  const r=gate(data(260),{asOf,minRows:165,maxAgeDays:7});
  assert.equal(r.latestDate,'2025-09-17');assert.equal(r.ageDays,3);assert.equal(r.series.length,260);
});
test('timezone offsets map to UTC calendar date',()=>{
  const r=check([{date:'2025-09-18',price:99},{t:'2025-09-19T23:30:00-03:00',price:100}]);
  assert.equal(r.excludedSameDay,1);assert.equal(r.series.length,1);
});
test('insufficient history after same-day exclusion blocks forecast',()=>{
  assert.throws(()=>check([{date:'2025-09-20',price:100}]),/Insufficient/);
});
test('asOf must be timezone-aware',()=>{
  assert.throws(()=>gate(data(200),{asOf:'2025-09-20T12:00:00'}),/timezone/);
});
test('invalid options fail closed',()=>{
  assert.throws(()=>check(data(180),{minRows:0}),/options/);
  assert.throws(()=>check(data(180),{requireFresh:'no'}),/options/);
});
