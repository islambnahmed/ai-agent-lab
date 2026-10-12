import test from 'node:test';
import assert from 'node:assert/strict';
import {fingerprintHistory,appendForecast,appendSettlement,verifyLedger,scoreLedger} from '../prospective_ledger.mjs';
import {forecast} from '../forecast.mjs';

const history=[{date:'2026-10-08',price:4000},{date:'2026-10-09',price:4020}];
const base={recordedAt:'2026-10-09T21:00:00Z',originDate:'2026-10-09',horizon:1,
  sourceId:'fixture',model:'persistence',originPrice:4020,point:4020,lower:3980,upper:4060,
  historyFingerprint:fingerprintHistory('fixture',history)};
const obs=[{date:'2026-10-11',price:4060},{date:'2026-10-12',price:4090}];
const settle=(ledger,rows=obs.slice(0,1),at='2026-10-11T23:00:00Z')=>
  appendSettlement(ledger,{recordedAt:at,forecastHash:ledger[0].hash,sourceId:'fixture',observations:rows});

test('frozen forecast is append-only and score is paired with persistence baseline',()=>{
  const original=[];
  let ledger=appendForecast(original,base);
  assert.equal(original.length,0);
  assert.equal(verifyLedger(ledger).forecasts,1);
  assert.equal(scoreLedger(ledger).byHorizon[1].mae,null);
  ledger=settle(ledger);
  assert.equal(verifyLedger(ledger).settlements,1);
  assert.equal(scoreLedger(ledger).byHorizon[1].baselineMae,40);
  assert.equal(scoreLedger(ledger).byHorizon[1].intervalCoveragePct,100);
  assert.throws(()=>settle(ledger),/Duplicate settlement/);
});
test('hash chain rejects silent editing and reordering',()=>{
  const ledger=appendForecast([],base);
  assert.throws(()=>verifyLedger([{...ledger[0],point:5000}]),/contents changed/);
  assert.throws(()=>verifyLedger([{...ledger[0],prevHash:'fake'}]),/Broken sequence/);
});
test('hindsight forecasts cannot settle observations that predate issue date',()=>{
  const late=appendForecast([],{...base,recordedAt:'2026-10-12T12:00:00Z'});
  assert.throws(()=>settle(late,obs.slice(0,1),'2026-10-12T23:00:00Z'),/recorded after the first target/);
});
test('source and model strings cannot collide via delimiter injection',()=>{
  const first=appendForecast([],{...base,sourceId:'a|b',model:'c'});
  const second=appendForecast(first,{...base,sourceId:'a',model:'b|c'});
  assert.equal(verifyLedger(second).forecasts,2);
});
test('calendar, nonfinite values, duplicate origins and session ordering are checked',()=>{
  assert.throws(()=>fingerprintHistory('x',[{date:'2026-02-30',price:2}]),/Invalid calendar/);
  assert.throws(()=>appendForecast([],{...base,point:Infinity}),/Invalid forecast price/);
  const ledger=appendForecast([],base);
  assert.throws(()=>appendForecast(ledger,base),/Duplicate forecast/);
  assert.throws(()=>settle(ledger,[obs[1],obs[0]]),/chronological/);
  assert.throws(()=>settle(ledger,obs),/exactly horizon/);
  assert.throws(()=>settle(ledger,obs.slice(0,1),'2026-10-10T23:00:00Z'),/before target/);
});
test('caller mutation cannot alter stored settlement rows',()=>{
  const ledger=appendForecast([],base),rows=[{date:'2026-10-11',price:4001}];
  const done=settle(ledger,rows);
  rows[0].price=99999;
  assert.equal(scoreLedger(done).results[0].actual,4001);
});
test('30-session target requires 30 observed sessions; weekends are not guessed',()=>{
  const ledger=appendForecast([],{...base,horizon:30});
  assert.throws(()=>settle(ledger),/exactly horizon/);
});
test('forecast engine can issue a frozen synthetic fixture without claiming live skill',()=>{
  const rows=Array.from({length:260},(_,i)=>({
    date:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),
    price:2500+i*0.5+Math.sin(i)
  }));
  const r=forecast(rows,7),last=rows.at(-1);
  const l=appendForecast([],{recordedAt:last.date+'T23:00:00Z',originDate:last.date,horizon:7,
    sourceId:'synthetic-test',model:r.model,originPrice:last.price,point:r.point,
    lower:r.lower,upper:r.upper,historyFingerprint:fingerprintHistory('synthetic-test',rows)});
  assert.equal(verifyLedger(l).forecasts,1);
  assert.equal(scoreLedger(l).unsettled,1);
});
