import test from 'node:test';
import assert from 'node:assert/strict';
import {auditDailyCadence,guardedForecast} from '../cadence_gate.mjs';

function weekdays(n,start='2025-01-01'){
  const d=new Date(start+'T12:00:00Z'),rows=[];
  while(rows.length<n){
    if(d.getUTCDay()!==0&&d.getUTCDay()!==6)
      rows.push({date:d.toISOString().slice(0,10),price:2500+rows.length*0.7});
    d.setUTCDate(d.getUTCDate()+1);
  }
  return rows;
}
test('valid 260-session history passes and supports a guarded 7-session forecast',()=>{
  const rows=weekdays(260),audit=auditDailyCadence(rows);
  assert.equal(audit.n,260);
  assert.equal(audit.weekendObserved,0);
  assert.equal(audit.weekdayCoverage,1);
  const result=guardedForecast(rows,7);
  assert.ok(result.point>0);
  assert.equal(result.cadence.n,260);
});
test('monthly observations must not masquerade as daily trading sessions',()=>{
  const rows=Array.from({length:18},(_,i)=>({date:new Date(Date.UTC(2024,i,1)).toISOString().slice(0,10),price:2500+i}));
  assert.throws(()=>auditDailyCadence(rows),/CADENCE_SPARSE_WEEKDAYS|CADENCE_LONG_GAP|CADENCE_WEEKEND_ROWS/);
});
test('missing runs and weekend rows fail closed',()=>{
  const rows=weekdays(260);
  assert.throws(()=>auditDailyCadence(rows.filter((_,i)=>i<110||i>116)),/CADENCE_LONG_GAP/);
  assert.throws(()=>auditDailyCadence([...rows,{date:'2025-01-04',price:2600}]),/CADENCE_WEEKEND_ROWS/);
});
test('invalid and stale source observations fail before normalization',()=>{
  const rows=weekdays(260);
  assert.throws(()=>auditDailyCadence([...rows,{date:'invalid',price:2600}]),/CADENCE_MALFORMED_ROW/);
  assert.throws(()=>auditDailyCadence(rows,{asOf:'2026-10-10T12:00:00Z',maxAgeDays:7}),/CADENCE_STALE_HISTORY/);
});
test('future observations cannot be accepted as history',()=>{
  const rows=weekdays(260,'2026-01-01');
  assert.throws(()=>auditDailyCadence(rows,{asOf:'2026-01-01T00:00:00Z'}),/CADENCE_FUTURE_OBSERVATION/);
});
