import test from 'node:test';
import assert from 'node:assert/strict';
import {forecast} from '../forecast.mjs';
import {auditDailyCadence,guardedForecast} from '../cadence_gate.mjs';

function makeSeries(n,{start='2024-01-01',step='weekday',price=2400}={}){
  const rows=[];let d=Date.parse(start+'T00:00:00Z');
  while(rows.length<n){
    if(step==='calendar'||(step==='weekday'&&new Date(d).getUTCDay()!==0&&new Date(d).getUTCDay()!==6)||step==='monthly'){
      rows.push({date:new Date(d).toISOString().slice(0,10),price:price+rows.length*.4});
    }
    if(step==='monthly'){const x=new Date(d);x.setUTCMonth(x.getUTCMonth()+1);d=x.getTime()}
    else d+=86400000;
  }
  return rows;
}
const code=(f,pattern)=>assert.throws(f,pattern);
test('counterexample: base accepts monthly rows as 7-session forecast',()=>{
  const monthly=makeSeries(240,{step:'monthly'});
  const r=forecast(monthly,7);
  assert.equal(r.latest.date,monthly.at(-1).date);
  assert.ok(r.audit.n>=10);
  const lastOrigin=monthly.length-8;
  const elapsedDays=(Date.parse(monthly[lastOrigin+7].date)-Date.parse(monthly[lastOrigin].date))/86400000;
  assert.ok(elapsedDays>180,'7 observed rows actually span roughly seven months');
  code(()=>guardedForecast(monthly,7),/CADENCE_SPARSE_WEEKDAYS/);
});
test('genuine weekday sessions pass and forecasts remain numerically identical',()=>{
  const rows=makeSeries(300);
  const old=forecast(rows,7),now=guardedForecast(rows,7);
  assert.equal(old.point,now.point);
  assert.equal(old.audit.mae,now.audit.mae);
  assert.equal(now.cadence.weekdayCoverage,1);
});
test('calendar-day fixture with weekend rows is rejected',()=>{
  code(()=>guardedForecast(makeSeries(300,{step:'calendar'}),7),/CADENCE_WEEKEND_ROWS/);
});
test('even one weekend row is rejected in strict session mode',()=>{
  const rows=makeSeries(300);
  rows.push({date:'2025-02-01',price:2600});
  code(()=>guardedForecast(rows,7),/CADENCE_WEEKEND_ROWS/);
});
test('a 12-weekday gap is rejected even with otherwise dense history',()=>{
  const rows=makeSeries(330),cut=rows.slice(140,152);
  const withGap=rows.filter(x=>!cut.some(y=>x.date===y.date));
  code(()=>guardedForecast(withGap,7),/CADENCE_LONG_GAP/);
});
test('two isolated missing weekdays are tolerated',()=>{
  const rows=makeSeries(300).filter((_,i)=>i!==45&&i!==176);
  const d=auditDailyCadence(rows);
  assert.ok(d.weekdayCoverage>.99);
});
test('future observation is blocked with explicit asOf',()=>{
  const rows=makeSeries(300,{start:'2025-01-01'});
  code(()=>guardedForecast(rows,1,{asOf:'2025-01-01T12:00:00Z'}),/CADENCE_FUTURE_OBSERVATION/);
});
test('stale observation is blocked when maxAgeDays requested',()=>{
  const rows=makeSeries(300,{start:'2024-01-01'});
  code(()=>guardedForecast(rows,1,{asOf:'2026-10-09T12:00:00Z',maxAgeDays:7}),/CADENCE_STALE_HISTORY/);
});
test('malformed rows fail closed instead of silently disappearing',()=>{
  const rows=makeSeries(300);rows[30]={date:'garbage',price:'NaN'};
  code(()=>guardedForecast(rows,7),/CADENCE_MALFORMED_ROW/);
});
test('transfer: weekday FX-style data also passes (calendar-structure only)',()=>{
  const fx=makeSeries(260,{price:1.1});
  assert.equal(auditDailyCadence(fx).weekdayCoverage,1);
});
test('the audit is deterministic and does not mutate input',()=>{
  const rows=makeSeries(260),snapshot=JSON.stringify(rows);
  assert.deepEqual(auditDailyCadence(rows),auditDailyCadence(rows));
  assert.equal(JSON.stringify(rows),snapshot);
});
