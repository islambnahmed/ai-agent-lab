/**
 * Khepri 153: calendar/horizon semantics audit. No external I/O or market claims.
 * Expects chronologically sorted, unique ISO dates. It deliberately does not
 * silently drop weekend observations: doing so could erase valid vendor data.
 */
const DAY_MS = 86400000;
function parseISO(date) {
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new TypeError(`invalid ISO date: ${date}`);
  const ms = Date.parse(date + 'T00:00:00Z');
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 10) !== date) throw new TypeError(`nonexistent ISO date: ${date}`);
  return ms;
}
const weekday = ms => {const d=new Date(ms).getUTCDay();return d!==0&&d!==6;};
export function targetDate(originDate, horizon, calendar='weekdays') {
  if (!Number.isInteger(horizon) || horizon<1 || horizon>365) throw new RangeError('invalid horizon');
  if (!['weekdays','daily'].includes(calendar)) throw new RangeError('invalid calendar');
  let ms=parseISO(originDate), count=0;
  while(count<horizon) {ms+=DAY_MS;if(calendar==='daily'||weekday(ms))count++;}
  return new Date(ms).toISOString().slice(0,10);
}
export function auditCalendar(rows,horizon,{calendar='weekdays',warmup=42,maxExamples=5}={}) {
  if(!Array.isArray(rows)||rows.length===0)throw new TypeError('nonempty rows required');
  if(!Number.isInteger(warmup)||warmup<1)throw new RangeError('invalid warmup');
  if(!Number.isInteger(maxExamples)||maxExamples<0)throw new RangeError('invalid maxExamples');
  targetDate('2024-01-01',horizon,calendar);
  const dates=rows.map(row=>typeof row==='string'?row:row?.date);
  const ms=dates.map(parseISO);
  for(let i=1;i<ms.length;i++)if(ms[i]<=ms[i-1])throw new RangeError('dates must be strictly increasing and unique');
  const weekends=dates.filter((_,i)=>!weekday(ms[i]));
  const missingExpected=[];
  for(let i=1;i<dates.length;i++){
    const expected=targetDate(dates[i-1],1,calendar);
    if(expected!==dates[i])missingExpected.push({after:dates[i-1],observed:dates[i],expected});
  }
  let tested=0,mismatches=0,early=0,late=0;
  const examples=[];
  for(let origin=warmup;origin+horizon-1<dates.length;origin++){
    const expected=targetDate(dates[origin-1],horizon,calendar);
    const observed=dates[origin+horizon-1];
    tested++;
    if(expected!==observed){mismatches++;if(observed<expected)early++;else late++;
      if(examples.length<maxExamples)examples.push({origin:dates[origin-1],horizon,expected,observed,direction:observed<expected?'early':'late'});
    }
  }
  return {calendar,horizon,rows:dates.length,tested,matched:tested-mismatches,mismatches,early,late,
    weekendRows:weekends.length,unexpectedGaps:missingExpected.length,
    gapExamples:missingExpected.slice(0,maxExamples),examples,
    integrityStatus:(calendar==='weekdays'&&weekends.length>0)||missingExpected.length>0?'calendar_anomaly':'no_observed_calendar_anomaly',
    status:tested===0?'insufficient_evidence':mismatches?'horizon_label_mismatch':'observed_alignment_only',
    caution:'Calendar agreement does not prove market holidays, provider timestamps, or future data availability.'};
}
