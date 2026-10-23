import {cadenceAudit,legacyDailyAccept,makeDates} from './cadence_window.mjs';
import {writeFileSync} from 'node:fs';
// Seeded deterministic synthetic experiment, not real provider data.
let seed=3992026;
function rnd(){seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;}
function weekdayDates(){
  const dates=[];let day=Date.UTC(2025,0,1);
  while(dates.length<190){const d=new Date(day),w=d.getUTCDay();
    if(w!==0&&w!==6&&rnd()>=.04)dates.push(d.toISOString().slice(0,10));
    day+=86400000;
  }
  return dates;
}
function dailyDates(){const gaps=Array.from({length:190},()=>rnd()<.04?2:1);return makeDates('2025-01-01',gaps);}
function sparseTail(){const daily=150+Math.floor(rnd()*25),weekly=20+Math.floor(rnd()*15);
  return makeDates('2025-01-01',[...Array(daily).fill(1),...Array(weekly).fill(7)]);
}
function alternate(){const gaps=Array.from({length:190},(_,i)=>i%2?7:1);return makeDates('2025-01-01',gaps);}
const result={seed:3992026,trialsPerScenario:1000,scenarios:{}};
for(const [name,make] of Object.entries({weekdayLike:weekdayDates,dailyLike:dailyDates,weeklyTail:sparseTail,alternating:alternate})){
  let legacyAccept=0,local50Accept=0,local65Accept=0,hybridAccept=0,worst=1;
  for(let i=0;i<1000;i++){
    const dates=make();
    legacyAccept+=Number(legacyDailyAccept(dates));
    const a=cadenceAudit(dates,{minLocalDailyFraction:.5,maxLongGaps:20});
    const b=cadenceAudit(dates,{minLocalDailyFraction:.65,maxLongGaps:20});
    const c=cadenceAudit(dates);
    local50Accept+=Number(a.accepted);local65Accept+=Number(b.accepted);hybridAccept+=Number(c.accepted);
    worst=Math.min(worst,b.worstWindowDailyFraction);
  }
  result.scenarios[name]={legacyAccept,local50Accept,local65Accept,hybridAccept,minWorstWindowFraction:worst};
}
console.log(JSON.stringify(result,null,2));
if(process.argv.includes('--write'))writeFileSync(new URL('./results.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
