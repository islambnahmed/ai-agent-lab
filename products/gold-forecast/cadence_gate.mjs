/** Fail-closed observation-cadence gate for the gold forecast's session-based horizons.
 * Checks date structure, not source authenticity, quote availability, or price accuracy.
 */
import {normalize,forecast} from './forecast.mjs';

const DAY=86400000;
const dayMs=date=>Date.parse(date+'T00:00:00Z');
const isWeekday=ms=>{const w=new Date(ms).getUTCDay();return w!==0&&w!==6};

export function auditDailyCadence(raw,{
  minWeekdayCoverage=0.90,
  maxMissingWeekdayRun=5,
  maxWeekendShare=0,
  asOf=null,
  maxAgeDays=null,
}={}){
  if(!Array.isArray(raw)||raw.length===0)throw Error('CADENCE_INVALID_SERIES');
  if(!(minWeekdayCoverage>0&&minWeekdayCoverage<=1)||
     !(maxWeekendShare>=0&&maxWeekendShare<=1)||
     !Number.isInteger(maxMissingWeekdayRun)||maxMissingWeekdayRun<0)
    throw Error('CADENCE_INVALID_POLICY');
  // Unlike normalize(), reject malformed observations rather than silently dropping them.
  for(const row of raw){
    const ts=Date.parse(row?.t??row?.date);
    const price=Number(row?.price??row?.close);
    if(!Number.isFinite(ts)||!Number.isFinite(price)||price<=0)
      throw Error('CADENCE_MALFORMED_ROW');
  }
  const series=normalize(raw);
  const days=series.map(p=>dayMs(p.date));
  const known=new Set(days);
  let weekdayTotal=0,weekdayObserved=0,weekendObserved=0;
  let missingRun=0,longestMissingWeekdayRun=0;
  for(let ms=days[0];ms<=days.at(-1);ms+=DAY){
    if(isWeekday(ms)){
      weekdayTotal++;
      if(known.has(ms)){weekdayObserved++;missingRun=0}
      else{missingRun++;longestMissingWeekdayRun=Math.max(longestMissingWeekdayRun,missingRun)}
    }else if(known.has(ms))weekendObserved++;
  }
  const weekdayCoverage=weekdayObserved/weekdayTotal;
  const weekendShare=weekendObserved/series.length;
  const diagnostics={n:series.length,first:series[0].date,last:series.at(-1).date,
    weekdayCoverage,weekendShare,longestMissingWeekdayRun,
    weekdayObserved,weekdayTotal,weekendObserved};
  if(weekdayCoverage<minWeekdayCoverage)throw Error('CADENCE_SPARSE_WEEKDAYS '+JSON.stringify(diagnostics));
  if(longestMissingWeekdayRun>maxMissingWeekdayRun)throw Error('CADENCE_LONG_GAP '+JSON.stringify(diagnostics));
  if(weekendShare>maxWeekendShare)throw Error('CADENCE_WEEKEND_ROWS '+JSON.stringify(diagnostics));
  if(asOf!==null){
    const now=Date.parse(asOf);
    if(!Number.isFinite(now))throw Error('CADENCE_INVALID_ASOF');
    if(days.at(-1)>now)throw Error('CADENCE_FUTURE_OBSERVATION '+JSON.stringify(diagnostics));
    if(maxAgeDays!==null){
      if(!Number.isFinite(maxAgeDays)||maxAgeDays<0)throw Error('CADENCE_INVALID_AGE_POLICY');
      if(now-days.at(-1)>maxAgeDays*DAY)throw Error('CADENCE_STALE_HISTORY '+JSON.stringify(diagnostics));
    }
  }
  return diagnostics;
}

/** Opt-in wrapper: base forecast unchanged; refuses unverified session cadence. */
export function guardedForecast(raw,h=7,policy={}){
  const cadence=auditDailyCadence(raw,policy);
  return {...forecast(raw,h),cadence};
}
