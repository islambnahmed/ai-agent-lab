import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSnapshot, FROZEN} from './evidence_snapshot.mjs';

const base = {asOf:'2026-10-30T12:00:00Z'};
const row = (date,price,capturedAt='2026-10-30T11:00:00Z') =>
  ({date,price,capturedAt,sourceId:FROZEN.sourceId,sourceSession:FROZEN.sourceSession});
const dates = ['2026-10-19','2026-10-20','2026-10-21','2026-10-22','2026-10-23','2026-10-26','2026-10-27'];
const seven = dates.map((date,i)=>row(date,4180+i));
const invalid = (patch,pattern)=>assert.throws(()=>buildSnapshot({...base,...patch}),pattern);

test('frozen anchor and predictions match published commit',()=>{
  assert.equal(FROZEN.anchorCommit,'609fc40a6233ea25ff1f6716a5bcc5df8c37f321');
  assert.equal(FROZEN.predictions[1],4176.897267384459);
  assert.equal(FROZEN.predictions[7],4168.677039660794);
  assert.equal(FROZEN.predictions[30],4154.572183780181);
});
test('no observations stays pending without pretending fresh provider data',()=>{
  const x=buildSnapshot(base);
  assert.deepEqual(x.forecasts.map(y=>y.status),['pending','pending','pending']);
  assert.equal(x.generatedAsOf,base.asOf);
});
test('supplied observation counts never establish ordinal target identity',()=>{
  const x=buildSnapshot({...base,observations:seven});
  assert.deepEqual(x.forecasts.map(f=>f.status),['sequence_unverified','sequence_unverified','pending']);
  assert.ok(x.forecasts.every(f=>!('targetDate' in f) && !('improvementUsd' in f)));
});
test('unverified sequence never emits matured scores even with capturedAt',()=>{
  const x=buildSnapshot({...base,observations:[row('2026-10-19',4180)]});
  assert.equal(x.schemaVersion,2);
  assert.equal(x.forecasts[0].status,'sequence_unverified');
  assert.equal(x.forecasts[0].challengerAbsoluteError,undefined);
  assert.equal(x.forecasts[1].status,'pending');
});
test('never output raw target price series',()=>{
  const x=buildSnapshot({...base,observations:seven});
  assert.equal('observations' in x,false);
  assert.equal('actual' in x.forecasts[0],false);
});
test('reject duplicates and unsorted rows',()=>{
  invalid({observations:[seven[1],seven[0]]},/unordered/);
  invalid({observations:[seven[0],seven[0]]},/unordered/);
});
test('reject origin-day and invalid calendar dates',()=>{
  invalid({observations:[row('2026-10-16',4180)]},/date/);
  invalid({observations:[row('2026-02-30',4180)]},/date/);
});
test('reject wrong source or session',()=>{
  invalid({sourceId:'other'},/Source/);
  invalid({sourceSession:'AM'},/Source/);
  invalid({observations:[{...seven[0],sourceSession:'AM'}]},/Source/);
});
test('reject missing, future, and pre-anchor capture timestamps',()=>{
  invalid({observations:[{...seven[0],capturedAt:undefined}]},/capture/);
  invalid({observations:[row('2026-10-19',4180,'2026-10-31T00:00:00Z')]},/capture/);
  invalid({observations:[row('2026-10-19',4180,'2026-10-16T21:25:00Z')]},/capture/);
  invalid({observations:[row('2026-10-19',4180,'2026-10-18T23:59:59Z')]},/capture/);
});
test('reject invalid numeric observations',()=>{
  for(const price of [NaN,Infinity,-1,0,'4180'])
    invalid({observations:[row('2026-10-19',price)]},/price/);
});
test('reject asOf missing timezone, malformed or before anchor',()=>{
  invalid({asOf:'2026-10-30T12:00:00'},/asOf/);
  invalid({asOf:'2026-10-16T21:26:00Z'},/predates/);
});
test('never promote self-reported publication metadata to verified',()=>{
  const forged={...seven[0],publishedAt:'2026-10-19T09:00:00Z',proof:'verified'};
  const x=buildSnapshot({...base,observations:[forged]});
  assert.equal(x.forecasts[0].status,'sequence_unverified');
});
test('dropping earlier provider observations cannot flip a scored conclusion',()=>{
  const full=[row('2026-10-19',4100),row('2026-10-20',4200),row('2026-10-21',4300)];
  const a=buildSnapshot({...base,observations:full});
  const b=buildSnapshot({...base,observations:[full[2]]});
  for(const snapshot of [a,b]) {
    assert.ok(snapshot.forecasts.every(f=>f.status!=='matured_timing_unverified'));
    assert.ok(snapshot.forecasts.every(f=>f.improvementUsd===undefined && f.targetDate===undefined));
  }
});
