import test from "node:test";
import assert from "node:assert/strict";
import {auditDailyCadence,guardedForecast} from "../cadence_gate.mjs";

function weekdays(n){
  const out=[];
  for(let d=new Date("2024-01-01T00:00:00Z");out.length<n;d.setUTCDate(d.getUTCDate()+1)){
    if(d.getUTCDay()===0||d.getUTCDay()===6)continue;
    out.push({date:d.toISOString().slice(0,10),price:2200+out.length});
  }
  return out;
}
function monthly(n){
  return Array.from({length:n},(_,i)=>({
    date:new Date(Date.UTC(2010+Math.floor(i/12),i%12,1)).toISOString().slice(0,10),
    price:2200+i
  }));
}
test("accepts dense weekday closes and allows a guarded forecast",()=>{
  const data=weekdays(260),report=auditDailyCadence(data);
  assert.equal(report.weekdayCoverage,1);
  assert.equal(report.weekendObserved,0);
  assert.ok(guardedForecast(data,7).point>0);
});
test("rejects monthly prices masquerading as trading sessions",()=>{
  assert.throws(()=>auditDailyCadence(monthly(180)),/CADENCE_SPARSE_WEEKDAYS|CADENCE_LONG_GAP/);
  assert.throws(()=>guardedForecast(monthly(180),30),/CADENCE_/);
});
test("rejects weekend quotes and invalid rows rather than silently normalizing",()=>{
  const data=weekdays(260);
  assert.throws(()=>auditDailyCadence([...data,{date:"2025-01-04",price:2500}]),/CADENCE_WEEKEND_ROWS/);
  assert.throws(()=>auditDailyCadence([...data,{date:"invalid",price:2500}]),/CADENCE_MALFORMED_ROW/);
});
test("rejects stale history under a declared as-of policy",()=>{
  const data=weekdays(260);
  assert.throws(()=>auditDailyCadence(data,{asOf:"2026-10-10T00:00:00Z",maxAgeDays:7}),/CADENCE_STALE_HISTORY/);
});
