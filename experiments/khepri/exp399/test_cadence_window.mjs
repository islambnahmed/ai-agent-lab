import test from 'node:test';
import assert from 'node:assert/strict';
import {cadenceAudit,legacyDailyAccept,makeDates} from './cadence_window.mjs';
const audit=g=>cadenceAudit(makeDates('2025-01-01',g));
test('one-year daily-then-weekly feed passes legacy global ratio but fails local audit',()=>{
  const gaps=[...Array(164).fill(1),...Array(28).fill(7)];
  const dates=makeDates('2025-01-01',gaps);
  assert.equal(dates.length,193);
  assert.equal(legacyDailyAccept(dates),true);
  const r=cadenceAudit(dates);
  assert.equal(r.accepted,false);assert.equal(r.worstWindowDailyFraction,0);
  assert.ok(r.overallDailyFraction>.8);
  assert.equal(gaps.reduce((a,b)=>a+b,0),360);
});
test('continuous calendar daily series accepted',()=>{
  const r=audit(Array(200).fill(1));assert.equal(r.accepted,true);assert.equal(r.worstWindowDailyFraction,1);
});
test('regular weekday market sessions accepted',()=>{
  const dates=[];for(let i=0;i<365;i++){
    const d=new Date(Date.UTC(2025,0,1+i));if(d.getUTCDay()!==0&&d.getUTCDay()!==6)dates.push(d.toISOString().slice(0,10));
  }
  const r=cadenceAudit(dates);assert.equal(r.accepted,true);assert.ok(r.worstWindowDailyFraction>=.75);
});
test('small isolated holidays tolerated',()=>{
  const gaps=[...Array(150).fill(1),2,...Array(150).fill(1),3,...Array(50).fill(1)];
  assert.equal(audit(gaps).accepted,true);
});
test('alternating 1 and 7 day feed shows global heuristic weakness',()=>{
  const dates=makeDates('2025-01-01',Array.from({length:180},(_,i)=>i%2===0?1:7));
  assert.equal(legacyDailyAccept(dates),true);
  assert.equal(cadenceAudit(dates).accepted,false);
});
test('hybrid long-gap audit catches six weekly gaps while pure density test misses them',()=>{
  const gaps=[...Array(160).fill(1),...Array(6).fill(7)];
  assert.equal(audit(gaps).accepted,false);
  assert.equal(cadenceAudit(makeDates('2025-01-01',gaps),{maxLongGaps:20}).accepted,true);
});
test('reject invalid dates, unordered rows and options',()=>{
  assert.throws(()=>cadenceAudit(['2025-02-30',...makeDates('2025-03-01',Array(20).fill(1))]),/Nonexistent/);
  assert.throws(()=>cadenceAudit(makeDates('2025-01-01',Array(21).fill(1)).reverse()),/Unsorted/);
  assert.throws(()=>cadenceAudit(makeDates('2025-01-01',Array(21).fill(1)),{windowSteps:0}),/options/);
});
test('sliding window includes last possible window',()=>{
  const r=audit([...Array(100).fill(1),...Array(20).fill(7)]);
  assert.equal(r.worstWindowStart,100);assert.equal(r.worstWindowDailyFraction,0);
});
