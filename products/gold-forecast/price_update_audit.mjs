/**
 * Observational update-frequency diagnostic, NOT a source-authentication tool.
 * A dense weekday timestamp series can be monthly/weekly data forward-filled.
 * A real daily market series can also legitimately remain unchanged.
 * Flagged means "requires independent evidence", not "fraud proved".
 */
function dateOf(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(value))
    throw Error('UPDATE_INVALID_DATE');
  const day = value.slice(0,10);
  const ms = Date.parse(day + 'T00:00:00Z');
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0,10) !== day)
    throw Error('UPDATE_INVALID_DATE');
  return ms;
}
function isEarlyMonthSession(ms) {
  const d = new Date(ms), day = d.getUTCDate();
  let weekdays = 0;
  for (let n=1;n<=day;n++) {
    const w = new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),n)).getUTCDay();
    if (w!==0 && w!==6) weekdays++;
  }
  return weekdays <= 3;
}
export function auditPriceUpdateCadence(raw, {
  unchangedLogTolerance=1e-10,
  minUnchangedShare=0.8,
  minLongestUnchangedRun=10,
  minChanges=6,
  minEarlyMonthChangeShare=0.7
}={}) {
  if (!Array.isArray(raw) || raw.length<30) throw Error('UPDATE_INSUFFICIENT_ROWS');
  if (![unchangedLogTolerance,minUnchangedShare,minEarlyMonthChangeShare].every(Number.isFinite) ||
      unchangedLogTolerance<0 || minUnchangedShare<0 || minUnchangedShare>1 ||
      minEarlyMonthChangeShare<0 || minEarlyMonthChangeShare>1 ||
      !Number.isInteger(minLongestUnchangedRun) || minLongestUnchangedRun<1 ||
      !Number.isInteger(minChanges) || minChanges<1)
    throw Error('UPDATE_INVALID_POLICY');
  let previous=-Infinity, lastPrice=null, unchanged=0, run=0, maxRun=0;
  let changes=0, earlyMonthChanges=0, weekendRows=0;
  for (const row of raw) {
    const date=row?.date ?? row?.t;
    const ms=dateOf(date);
    const price=Number(row?.price ?? row?.close);
    if (!Number.isFinite(price) || price<=0) throw Error('UPDATE_INVALID_PRICE');
    if (ms<=previous) throw Error('UPDATE_UNSORTED_OR_DUPLICATE');
    previous=ms;
    const weekday=new Date(ms).getUTCDay();
    if (weekday===0 || weekday===6) weekendRows++;
    if (lastPrice!==null) {
      if (Math.abs(Math.log(price/lastPrice))<=unchangedLogTolerance) {
        unchanged++;run++;maxRun=Math.max(maxRun,run);
      } else {
        changes++;if(isEarlyMonthSession(ms))earlyMonthChanges++;
        run=0;
      }
    }
    lastPrice=price;
  }
  const unchangedShare=unchanged/(raw.length-1);
  const earlyMonthChangeShare=changes?earlyMonthChanges/changes:null;
  const suspicious=unchangedShare>=minUnchangedShare &&
    maxRun>=minLongestUnchangedRun && changes>=minChanges &&
    earlyMonthChangeShare>=minEarlyMonthChangeShare;
  return {
    rows:raw.length,weekendRows,unchangedShare,longestUnchangedRun:maxRun,
    changes,earlyMonthChanges,earlyMonthChangeShare,
    status:suspicious?'SUSPECTED_MONTHLY_FORWARD_FILL':
      (changes<minChanges && unchangedShare>=minUnchangedShare?'INCONCLUSIVE_FEW_UPDATES':'NO_MONTHLY_PATTERN_FLAG'),
    evidence:'OBSERVATIONAL_ONLY',
    warning:'Identical rows can be produced by genuine fixed prices and forward-filled monthly values; a no-flag result cannot authenticate sampling cadence or publication times.'
  };
}
/** Compose with the opt-in cadence gate. Rejection is a policy decision, not a proof of manipulation. */
export function auditIntegrity(raw, {strictMonthlyPattern=true,...options}={}) {
  const priceUpdates=auditPriceUpdateCadence(raw,options);
  if(strictMonthlyPattern && priceUpdates.status==='SUSPECTED_MONTHLY_FORWARD_FILL')
    throw Error('UPDATE_SUSPECTED_MONTHLY_FORWARD_FILL '+JSON.stringify(priceUpdates));
  return priceUpdates;
}
