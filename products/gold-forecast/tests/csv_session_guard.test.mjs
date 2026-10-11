import test from 'node:test';
import assert from 'node:assert/strict';
import {parseSessionCsv} from '../csv_session_guard.mjs';
const nowMs=Date.parse('2026-10-11T12:00:00Z');
function days(n,weekdaysOnly=false) {
  const rows=[];
  for(let ms=Date.UTC(2025,0,1);rows.length<n;ms+=86400000){
    const d=new Date(ms);
    if(!weekdaysOnly||![0,6].includes(d.getUTCDay()))rows.push(d.toISOString().slice(0,10));
  }
  return rows;
}
const csv=dates=>'date,price\n'+dates.map((d,i)=>d+','+(3000+i)).join('\n');
test('calendar rows are not all sessions',()=>{
  assert.throws(()=>parseSessionCsv(csv(days(237)),{nowMs}),/got 169 after excluding 68/);
});
test('weekday rows are accepted',()=>{
  const dates=days(237,true),r=parseSessionCsv(csv(dates),{nowMs});
  assert.deepEqual(r.series.map(x=>x.date),dates);
  assert.equal(r.weekendRowsExcluded,0);
});
test('weekend exclusion is counted',()=>{
  const r=parseSessionCsv(csv(days(360)),{nowMs});
  assert.equal(r.series.length,258);
  assert.equal(r.weekendRowsExcluded,102);
});
test('bad dates and duplicates are rejected',()=>{
  const dates=days(237,true);
  assert.throws(()=>parseSessionCsv(csv(dates).replace(dates[0],'2025-02-30'),{nowMs}),/invalid calendar date|strictly increasing/);
  assert.throws(()=>parseSessionCsv(csv([dates[0],...dates.slice(0,236)]),{nowMs}),/strictly increasing/);
});
test('minimum cannot be disabled',()=>{
  assert.throws(()=>parseSessionCsv(csv(days(360)),{nowMs,minSessions:0}),/Invalid minimum/);
});
