/** Worker A: hidden-regime streaming benchmark. Synthetic only, no external dependencies. */
import {pathToFileURL} from 'node:url';
const rngFor=seed=>{let a=seed>>>0;return ()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};};
const best=a=>a.reduce((k,v,i)=>v<a[k]?i:k,0);
const loss=(c,x,y)=>Number((x[c>>1]^(c&1))!==y);
const predict=(c,x)=>x[c>>1]^(c&1);
export function sequence(seed,{family='binary',segments=[{n:180,p:.03},{n:180,p:.97},{n:180,p:.03}]}={}){
  const rand=rngFor(seed),order=family==='binary'?[0,1,2]:family==='tokenized'?[3,1,0,2]:null;
  const mask=family==='binary'?[0,0,0]:family==='tokenized'?[1,1,0,1]:null;
  if(!order||!segments.length||segments.some(s=>!Number.isInteger(s.n)||s.n<1||s.p<0||s.p>1))throw Error('Invalid scenario');
  const sample=p=>{const y=+(rand()<.5),raw=[y^+(rand()<.22),y^+(rand()<p),+(rand()<.5),+(rand()<.5)];return {x:order.map((j,i)=>raw[j]^mask[i]),y};};
  const train=Array.from({length:80},()=>sample(segments[0].p)),stream=[],boundaries=[];
  for(const [i,s] of segments.entries()){if(i)boundaries.push(stream.length);for(let j=0;j<s.n;j++)stream.push(sample(s.p));}
  return {train,stream,boundaries};
}
export function run(seed,opts={}){
  const {train,stream,boundaries}=sequence(seed,opts),d=train[0].x.length,m=2*d;
  const totals=new Float64Array(m),ema=new Float64Array(m),decay=2**(-1/16);
  for(const row of train)for(let c=0;c<m;c++){const e=loss(c,row.x,row.y);totals[c]+=e;ema[c]=decay*ema[c]+e;}
  const frozen=best(totals),errors={frozen:[],discounted:[]};
  const detectorHistory=[],alarms=[];let lastAlarm=-Infinity;
  for(const [t,row] of stream.entries()){
    errors.frozen.push(loss(frozen,row.x,row.y));errors.discounted.push(loss(best(ema),row.x,row.y));
    const v=Uint8Array.from({length:m},(_,c)=>loss(c,row.x,row.y));
    for(let c=0;c<m;c++)ema[c]=decay*ema[c]+v[c];
    detectorHistory.push(v);if(detectorHistory.length>48)detectorHistory.shift();
    if(detectorHistory.length===48&&t-lastAlarm>32){
      let diff=0;for(let c=0;c<m;c++){let a=0,b=0;for(let i=0;i<24;i++)a+=detectorHistory[i][c];for(let i=24;i<48;i++)b+=detectorHistory[i][c];diff=Math.max(diff,Math.abs(a-b)/24);}
      if(diff>=.55){alarms.push(t);lastAlarm=t;}
    }
  }
  const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
  const accuracy=Object.fromEntries(Object.entries(errors).map(([k,v])=>[k,1-mean(v)]));
  const first30=Object.fromEntries(Object.entries(errors).map(([k,v])=>[k,boundaries.length?1-mean(boundaries.flatMap(b=>v.slice(b,b+30))):null]));
  const pending=new Set(boundaries),delays=[],falseAlarms=[];
  for(const t of alarms){const b=[...pending].find(b=>t>=b&&t<=b+48);if(b===undefined)falseAlarms.push(t);else{delays.push(t-b);pending.delete(b);}}
  return {accuracy,first30,changes:boundaries.length,delays,falseAlarms,missed:pending.size,alarms,
    memoryBytes:{frozen:8*m,discounted:8*m,detectorPayload:48*m}};
}
export function benchmark({trials=200,seed=20261119,opts={}}={}){
  const runs=Array.from({length:trials},(_,i)=>run(seed+i,opts)),avg=a=>a.reduce((x,y)=>x+y,0)/a.length;
  const accuracyPct={},first30Pct={};for(const name of ['frozen','discounted']){
    accuracyPct[name]=+(100*avg(runs.map(r=>r.accuracy[name]))).toFixed(2);
    first30Pct[name]=runs[0].changes?+(100*avg(runs.map(r=>r.first30[name]))).toFixed(2):null;
  }
  const changes=runs.reduce((a,r)=>a+r.changes,0),delays=runs.flatMap(r=>r.delays);
  return {trials,accuracyPct,first30Pct,detector:{changes,detected:delays.length,recallPct:changes?+(100*delays.length/changes).toFixed(2):null,
    meanDelay:delays.length?+avg(delays).toFixed(2):null,falseAlarms:runs.reduce((a,r)=>a+r.falseAlarms.length,0)},memoryPayloadBytes:runs[0].memoryBytes};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const scenarios={stationary:{segments:[{n:540,p:.03}]},abruptReturn:{},transfer:{family:'tokenized'},subtle:{segments:[{n:180,p:.03},{n:360,p:.35}]}};
  console.log(JSON.stringify(Object.fromEntries(Object.entries(scenarios).map(([k,opts])=>[k,benchmark({opts})])),null,2));
}
