import {cadenceAudit,legacyDailyAccept,makeDates} from '../exp399/cadence_window.mjs';
import {weekdayCoverage} from './weekday_coverage.mjs';
import {writeFileSync} from 'node:fs';
let seed=4002026;
function rnd(){seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;}
const iso=t=>new Date(t).toISOString().slice(0,10);
function weekday({miss=.04,extraClosures=0}={}){
  let d=Date.UTC(2025,0,1);const a=[];let n=0;
  while(a.length<190){const w=new Date(d).getUTCDay();
    if(w!==0&&w!==6){n++;if((extraClosures===0||n%5>extraClosures)&&rnd()>=miss)a.push(iso(d));}
    d+=86400000;
  }
  return a;
}
const daily=()=>makeDates('2025-01-01',Array.from({length:190},()=>rnd()<.04?2:1));
const alternating13=()=>makeDates('2025-01-01',Array.from({length:190},(_,i)=>i%2?3:1));
const alternating17=()=>makeDates('2025-01-01',Array.from({length:190},(_,i)=>i%2?7:1));
const weeklyTail=()=>makeDates('2025-01-01',[...Array(165).fill(1),...Array(25).fill(7)]);
const scenarios={weekday4pct:()=>weekday(),daily4pct:daily,alternating13,alternating17,weeklyTail,
  legitimateThreeDayTradingWeek:()=>weekday({miss:0,extraClosures:2})};
const result={seed:4002026,trialsPerScenario:1000,scenarios:{}};
for(const [name,make] of Object.entries(scenarios)){
  const r={legacyAccept:0,exp399Accept:0,weekdayAccept:0,combinedAccept:0,
    maxMissingWeekdays:0};
  for(let i=0;i<1000;i++){
    const dates=make();const a=cadenceAudit(dates),b=weekdayCoverage(dates);
    r.legacyAccept+=Number(legacyDailyAccept(dates));
    r.exp399Accept+=Number(a.accepted);
    r.weekdayAccept+=Number(b.accepted);
    r.combinedAccept+=Number(a.accepted&&b.accepted);
    r.maxMissingWeekdays=Math.max(r.maxMissingWeekdays,b.maxMissingWeekdaysInWindow);
  }
  result.scenarios[name]=r;
}
console.log(JSON.stringify(result,null,2));
if(process.argv.includes('--write'))writeFileSync(new URL('./results.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
