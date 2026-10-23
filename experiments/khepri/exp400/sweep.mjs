import {cadenceAudit,makeDates} from '../exp399/cadence_window.mjs';
import {weekdayCoverage} from './weekday_coverage.mjs';
let seed=4002026;const rnd=()=>((seed=(1664525*seed+1013904223)>>>0)/4294967296);
const iso=t=>new Date(t).toISOString().slice(0,10);
function weekday(){let d=Date.UTC(2025,0,1);const a=[];while(a.length<190){const w=new Date(d).getUTCDay();if(w!==0&&w!==6&&rnd()>=.04)a.push(iso(d));d+=86400000;}return a;}
function daily(){return makeDates('2025-01-01',Array.from({length:190},()=>rnd()<.04?2:1));}
const cases={weekday:[],daily:[],alternating13:[],alternating17:[],weeklyTail:[]};
for(let i=0;i<1000;i++){
  cases.weekday.push(weekday());cases.daily.push(daily());
  cases.alternating13.push(makeDates('2025-01-01',Array.from({length:190},(_,j)=>j%2?3:1)));
  cases.alternating17.push(makeDates('2025-01-01',Array.from({length:190},(_,j)=>j%2?7:1)));
  cases.weeklyTail.push(makeDates('2025-01-01',[...Array(165).fill(1),...Array(25).fill(7)]));
}
const output={seed:4002026,counts:{}};
for(const [name,arr] of Object.entries(cases)){
  const maxMiss=arr.map(a=>weekdayCoverage(a,{maxMissingWeekdays:999}).maxMissingWeekdaysInWindow);
  output.counts[name]={exp399Accept:arr.filter(a=>cadenceAudit(a).accepted).length,
    thresholds:Object.fromEntries([4,5,6,7,8,10,12,14].map(t=>[t,maxMiss.filter(n=>n<=t).length])),
    min:Math.min(...maxMiss),max:Math.max(...maxMiss)};
}
console.log(JSON.stringify(output,null,2));
