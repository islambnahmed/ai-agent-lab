/** Expected-session coverage audit for ISO-date observations.
 * O(n) in observations: each gap uses at most 6 day-of-week checks.
 * Calendar assumption is explicit; holidays and closures are unknown.
 */
const DAY=86400000;
const stamp=s=>{
  const d=typeof s==='string'?s:s?.date;
  if(typeof d!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(d))throw Error('Invalid ISO date');
  const t=Date.parse(d+'T00:00:00Z');
  if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==d)throw Error('Invalid calendar date');
  return t;
};
export function missingSessionsBetween(start,end,weekendDays=[0,6]){
  if(!(end>start)||((end-start)%DAY)!==0)throw Error('Invalid interval');
  const weekend=new Set(weekendDays);
  const missing=(end-start)/DAY-1;
  let count=Math.floor(missing/7)*(7-weekend.size);
  for(let i=1;i<=missing%7;i++)if(!weekend.has(new Date(start+i*DAY).getUTCDay()))count++;
  return count;
}
export function weekdayCoverage(dates,{windowSteps=20,maxMissingWeekdays=7,weekendDays=[0,6]}={}){
  if(!Array.isArray(dates)||!Number.isInteger(windowSteps)||windowSteps<2||
     !Number.isInteger(maxMissingWeekdays)||maxMissingWeekdays<0||
     !Array.isArray(weekendDays)||weekendDays.length>=7||
     weekendDays.some(d=>!Number.isInteger(d)||d<0||d>6)||
     new Set(weekendDays).size!==weekendDays.length)
    throw Error('Invalid options');
  if(dates.length<windowSteps+1)throw Error('Insufficient observations');
  const t=dates.map(stamp),missed=[];
  for(let i=1;i<t.length;i++){
    if(t[i]<=t[i-1])throw Error('Unsorted or duplicate dates');
    missed.push(missingSessionsBetween(t[i-1],t[i],weekendDays));
  }
  let count=missed.slice(0,windowSteps).reduce((a,b)=>a+b,0),worst=count,worstStart=0;
  for(let start=1;start<=missed.length-windowSteps;start++){
    count+=missed[start+windowSteps-1]-missed[start-1];
    if(count>worst){worst=count;worstStart=start;}
  }
  return {accepted:worst<=maxMissingWeekdays,maxMissingWeekdaysInWindow:worst,
    worstWindowStart:worstStart,windowSteps,maxMissingWeekdays,weekendDays,
    totalMissingWeekdays:missed.reduce((a,b)=>a+b,0),
    caveat:'Unverified calendar proxy. Legitimate closures may trigger; cannot prove data authenticity.'};
}
