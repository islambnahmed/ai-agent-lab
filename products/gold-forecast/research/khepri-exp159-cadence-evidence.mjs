/** Khepri exp159: separate annual cadence screening from verified minute-level absence.
 *  No assumed market hours, no invented missing bars, no future data.
 */
export function weekdaysUTC(year) {
  if (!Number.isInteger(year) || year < 1970 || year > 2100) throw Error('bad year');
  let n = 0;
  for (let d = Date.UTC(year,0,1); d < Date.UTC(year+1,0,1); d+=86400000) {
    const dow = new Date(d).getUTCDay();
    if (dow >= 1 && dow <= 5) n++;
  }
  return n;
}
const median = arr => { const s=[...arr].sort((a,b)=>a-b);const i=Math.floor(s.length/2);return s.length%2?s[i]:(s[i-1]+s[i])/2; };
export function annualScreen(records,{lowRatio=0.92}={}) {
  if(!Array.isArray(records)||records.length<4||!Number.isFinite(lowRatio)||lowRatio<=0||lowRatio>=1) throw Error('bad input');
  const years=new Set();
  for (const r of records) {
    if(years.has(r.year)) throw Error('duplicate year');years.add(r.year);
    if(!Number.isSafeInteger(r.minuteRows)||r.minuteRows<=0||!Number.isSafeInteger(r.gapsOverOneMinute)||r.gapsOverOneMinute<0) throw Error('invalid counts');
    weekdaysUTC(r.year);
  }
  return records.map(r=>{
    const weekdays=weekdaysUTC(r.year),rowsPerWeekday=r.minuteRows/weekdays;
    const peerMedianDensity=median(records.filter(p=>p.year!==r.year).map(p=>p.minuteRows/weekdaysUTC(p.year)));
    const relativeDensity=rowsPerWeekday/peerMedianDensity;
    return {year:r.year,minuteRows:r.minuteRows,gapsOverOneMinute:r.gapsOverOneMinute,weekdays,rowsPerWeekday,peerMedianDensity,relativeDensity,deficitPct:100*(1-relativeDensity),screenFlag:relativeDensity<lowRatio,conclusion:'screening_only_raw_timestamps_and_authoritative_session_schedule_required'};
  });
}
const minuteMs = iso => {
  if(typeof iso!=='string'||!/^\\d{4}-\\d\\d-\\d\\dT\\d\\d:\\d\\d:00(?:\\.000)?Z$/.test(iso))throw Error('timestamps must be UTC minute ISO');
  const t=Date.parse(iso);if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,16)!==iso.slice(0,16))throw Error('invalid timestamp');return t;
};
const asSortedUnique = xs => {
  if(!Array.isArray(xs))throw Error('array required');
  const ts=xs.map(minuteMs).sort((a,b)=>a-b);
  for(let i=1;i<ts.length;i++)if(ts[i]===ts[i-1])throw Error('duplicate minute');
  return ts;
};
/** The caller MUST provide independently justified expected session minutes. */
export function sessionCoverage(observed,expected) {
  if(expected===undefined||expected===null) return {status:'indeterminate_without_session_calendar'};
  const obs=asSortedUnique(observed),exp=asSortedUnique(expected);
  if(!exp.length)throw Error('empty expected schedule');
  const expSet=new Set(exp),obsSet=new Set(obs);
  if(obs.some(t=>!expSet.has(t)))throw Error('observed outside expected schedule: calendar mismatch');
  const missing=exp.filter(t=>!obsSet.has(t));
  let longestRun=0,run=0,last=-Infinity;const byUtcDay={};
  for(const t of missing){run=t-last===60000?run+1:1;longestRun=Math.max(longestRun,run);last=t;const day=new Date(t).toISOString().slice(0,10);byUtcDay[day]=(byUtcDay[day]||0)+1;}
  return {status:'verified_against_supplied_schedule',expected:exp.length,observed:obs.length,missing:missing.length,coveragePct:100*obs.length/exp.length,longestConsecutiveMissingMinutes:longestRun,missingByUtcDay:byUtcDay};
}
