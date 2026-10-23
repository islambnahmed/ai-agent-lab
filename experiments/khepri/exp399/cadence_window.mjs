/**
 * Exp399: local-cadence audit for an ordered, unique ISO-date series.
 * Only tests claimed frequency; it cannot authenticate data, source, or closes.
 */
const DAY=86400000;
function dayMs(x){
  const d=typeof x==='string'?x:x?.date;
  if(typeof d!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(d))throw Error('Invalid ISO date');
  const ms=Date.parse(d+'T00:00:00Z');
  if(!Number.isFinite(ms)||new Date(ms).toISOString().slice(0,10)!==d)throw Error('Nonexistent date');
  return ms;
}
export function cadenceAudit(series,{windowSteps=20,minLocalDailyFraction=0.5,maxLongGaps=4,longGapDays=4}={}){
  if(!Array.isArray(series)||!Number.isInteger(windowSteps)||windowSteps<2||
     !(minLocalDailyFraction>0&&minLocalDailyFraction<=1)||
     !Number.isInteger(maxLongGaps)||maxLongGaps<0||!Number.isInteger(longGapDays)||longGapDays<2)
     throw Error('Invalid cadence options');
  if(series.length<windowSteps+1)throw Error('Insufficient cadence observations');
  const times=series.map(dayMs),gaps=[];
  for(let i=1;i<times.length;i++){
    const gap=(times[i]-times[i-1])/DAY;
    if(!Number.isInteger(gap)||gap<=0)throw Error('Unsorted or duplicate dates');
    gaps.push(gap);
  }
  const daily=gaps.map(g=>g===1?1:0);
  let count=daily.slice(0,windowSteps).reduce((a,b)=>a+b,0);
  let worst=count/windowSteps,worstStart=0;
  for(let start=1;start<=daily.length-windowSteps;start++){
    count+=daily[start+windowSteps-1]-daily[start-1];
    if(count/windowSteps<worst){worst=count/windowSteps;worstStart=start;}
  }
  const long=gaps.map(g=>g>=longGapDays?1:0);
  let longCount=long.slice(0,windowSteps).reduce((a,b)=>a+b,0);
  let worstLongCount=longCount;
  for(let start=1;start<=long.length-windowSteps;start++){
    longCount+=long[start+windowSteps-1]-long[start-1];
    worstLongCount=Math.max(worstLongCount,longCount);
  }
  const overall=daily.reduce((a,b)=>a+b,0)/daily.length;
  return {accepted:worst>=minLocalDailyFraction&&worstLongCount<=maxLongGaps,overallDailyFraction:overall,
    worstWindowDailyFraction:worst,worstWindowStart:worstStart,
    maxLongGapsInWindow:worstLongCount,maxLongGaps,longGapDays,
    windowSteps,threshold:minLocalDailyFraction,rows:series.length,
    caveat:'A cadence audit cannot verify source truth or completeness; legitimate closures can lower local density.'};
}
export function legacyDailyAccept(series){
  const times=series.map(dayMs);
  let daily=0;
  for(let i=1;i<times.length;i++){
    if(times[i]<=times[i-1])throw Error('Unsorted or duplicate dates');
    if(times[i]-times[i-1]===DAY)daily++;
  }
  return daily/(times.length-1)>=0.5;
}
export function makeDates(startISO,gaps){
  let ms=dayMs(startISO);const dates=[new Date(ms).toISOString().slice(0,10)];
  for(const gap of gaps){ms+=gap*DAY;dates.push(new Date(ms).toISOString().slice(0,10));}
  return dates;
}
