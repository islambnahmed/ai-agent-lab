import test from 'node:test';
import assert from 'node:assert/strict';
import {generate, schedule, evaluate, benchmark} from './delayed-feedback.mjs';

const demo = () => generate(13,[{n:20,p:.03},{n:20,p:.97}]);
test('deterministic generator and benchmark',()=>{
  assert.deepEqual(generate(10),generate(10));
  assert.deepEqual(benchmark({trials:5}),benchmark({trials:5}));
});
test('all feedback arrives no earlier than next event, even with zero lag',()=>{
  const data=demo();
  for(const [arrival,items] of schedule(data.stream,{maxLag:15}).deliveries){
    for(const item of items)assert.ok(arrival>item.eventTime);
  }
});
test('with lag zero and no missing labels, delayed EMA equals immediate oracle',()=>{
  const r=evaluate(demo(),{maxLag:0});
  assert.deepEqual(r.choices.oracle,r.choices.arrivalEMA);
  assert.deepEqual(r.errors.oracle,r.errors.arrivalEMA);
});
test('drop 100% means no labels delivered and frozen matches both delayed learners',()=>{
  const r=evaluate(demo(),{maxLag:20,drop:1});
  assert.equal(r.deliveries.delivered,0);
  assert.deepEqual(r.choices.frozen,r.choices.arrivalEMA);
  assert.deepEqual(r.choices.frozen,r.choices.timestamped);
});
test('no future-label leakage: changes to undelivered y do not alter earlier choices',()=>{
  const data=demo(), modified=structuredClone(data);
  const cutoff=12;
  for(let t=cutoff;t<modified.stream.length;t++)modified.stream[t].y ^= 1;
  const a=evaluate(data,{maxLag:8,seed:42}), b=evaluate(modified,{maxLag:8,seed:42});
  for(const method of Object.keys(a.choices)) assert.deepEqual(a.choices[method].slice(0,cutoff),b.choices[method].slice(0,cutoff));
});
test('feedback accounting is exact',()=>{
  const r=evaluate(demo(),{maxLag:10,drop:.35});
  assert.equal(r.deliveries.delivered+r.deliveries.notYetDelivered+r.deliveries.lost,40);
});
test('no changes scenario reports null transition metric',()=>{
  const r=benchmark({trials:3,segments:[{n:60,p:.03} ]});
  assert.equal(r.first30Pct,null);
});
test('invalid schedules rejected',()=>{
  assert.throws(()=>schedule(demo().stream,{maxLag:-1}));
  assert.throws(()=>schedule(demo().stream,{drop:1.1}));
  assert.throws(()=>schedule(demo().stream,{dropout:'unknown'}));
});
test('all scores bounded and fixed seed reproducible under severe delay',()=>{
  const r=benchmark({trials:20,delivery:{maxLag:80,drop:.4}});
  assert.ok(Object.values(r.accuracyPct).every(v=>v>=0&&v<=100));
  assert.equal(r.feedback.delivered+r.feedback.lost+r.feedback.pendingAtEnd,20*540);
});
test('age weighting and arrival weighting agree under zero delay',()=>{
  const r=evaluate(demo(),{maxLag:0});
  assert.deepEqual(r.choices.arrivalWeighted,r.choices.timestamped);
});
test('counterexample: fast switches plus severe lag make timestamp weighting worse',()=>{
  const fast=Array.from({length:18},(_,i)=>({n:30,p:i%2?.97:.03}));
  const r=benchmark({trials:30,seed:20271019,segments:fast,delivery:{maxLag:80,drop:.4}});
  assert.ok(r.timestampVsArrivalWeighted.differencePctPoints < -2);
});
