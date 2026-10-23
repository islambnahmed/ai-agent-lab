import test from 'node:test';
import assert from 'node:assert/strict';
import {weekdayCoverage,missingSessionsBetween} from './weekday_coverage.mjs';
import {cadenceAudit,makeDates} from '../exp399/cadence_window.mjs';
const DAY=86400000;
const t=s=>Date.parse(s+'T00:00:00Z');
const iso=x=>new Date(x).toISOString().slice(0,10);
const audit=g=>weekdayCoverage(makeDates('2025-01-01',g));
const slow=(a,b,weekend)=>{let n=0;for(let x=a+DAY;x<b;x+=DAY)if(!weekend.includes(new Date(x).getUTCDay()))n++;return n;};
test('closed-form missing-session counter matches exhaustive slow oracle for 2000 random intervals',()=>{
  let seed=400;const rnd=()=>((seed=(1664525*seed+1013904223)>>>0)/4294967296);
  for(let i=0;i<2000;i++){
    const start=t('1999-01-01')+Math.floor(rnd()*25000)*DAY;
    const end=start+(1+Math.floor(rnd()*150))*DAY;
    const weekend=i%2?[0,6]:[5,6];
    assert.equal(missingSessionsBetween(start,end,weekend),slow(start,end,weekend));
  }
});
test('weekend-only gaps are not counted as missing weekdays',()=>{
  assert.equal(missingSessionsBetween(t('2025-01-03'),t('2025-01-06')) ,0);
  assert.equal(missingSessionsBetween(t('2025-01-02'),t('2025-01-06')) ,1);
});
test('different market calendar (Friday/Saturday weekend) transfers',()=>{
  assert.equal(missingSessionsBetween(t('2025-01-02'),t('2025-01-05'),[5,6]),0);
  assert.equal(missingSessionsBetween(t('2025-01-02'),t('2025-01-05'),[0,6]),1);
});
test('exp399 hybrid misses alternating one/three-day downsampling; new audit flags it',()=>{
  const d=makeDates('2025-01-01',Array.from({length:190},(_,i)=>i%2?3:1));
  assert.equal(cadenceAudit(d).accepted,true);
  assert.equal(weekdayCoverage(d).accepted,false);
});
test('normal weekday dates pass without missing weekdays',()=>{
  const d=[];for(let x=t('2025-01-01');d.length<190;x+=DAY)if(![0,6].includes(new Date(x).getUTCDay()))d.push(iso(x));
  assert.equal(weekdayCoverage(d).maxMissingWeekdaysInWindow,0);
});
test('legitimate three-day trading week is flagged (known false positive)',()=>{
  const d=[];for(let x=t('2025-01-01');d.length<190;x+=DAY)if([1,2,3].includes(new Date(x).getUTCDay()))d.push(iso(x));
  assert.equal(weekdayCoverage(d).accepted,false);
});
test('all-daily observations pass',()=>assert.equal(audit(Array(200).fill(1)).accepted,true));
test('reject invalid date, ordering, insufficient observations and weekend configuration',()=>{
  assert.throws(()=>weekdayCoverage(['2025-02-30',...makeDates('2025-03-01',Array(20).fill(1))]),/Invalid calendar/);
  assert.throws(()=>weekdayCoverage(makeDates('2025-01-01',Array(20).fill(1)).reverse()),/Unsorted/);
  assert.throws(()=>weekdayCoverage(['2025-01-01']),/Insufficient/);
  assert.throws(()=>weekdayCoverage(makeDates('2025-01-01',Array(20).fill(1)),{weekendDays:[6,6]}),/Invalid options/);
});
test('worst window includes final possible window',()=>{
  const d=makeDates('2025-01-01',[...Array(100).fill(1),...Array(20).fill(3)]);
  assert.equal(weekdayCoverage(d).worstWindowStart,100);
});
