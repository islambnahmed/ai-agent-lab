/** Pure, time-parameterized lease check for ALREADY VALIDATED feed metadata. */
const MINUTE=60_000, DAY=86_400_000;
export function evaluateDisplayLease({quoteUpdated=null,historyLatestDate=null,nowMs=Date.now(),spotMaxAgeMinutes=15,historyMaxAgeDays=7}={}) {
  if(!Number.isFinite(nowMs)||!Number.isFinite(spotMaxAgeMinutes)||spotMaxAgeMinutes<=0||
     !Number.isFinite(historyMaxAgeDays)||historyMaxAgeDays<=0) throw Error("Invalid lease configuration");
  const quoteMs=typeof quoteUpdated==="string"?Date.parse(quoteUpdated):NaN;
  const dateOk=typeof historyLatestDate==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(historyLatestDate);
  const histStart=dateOk?Date.parse(historyLatestDate+"T00:00:00Z"):NaN;
  const histEnd=dateOk?Date.parse(historyLatestDate+"T23:59:59Z"):NaN;
  const quoteValid=Number.isFinite(quoteMs)&&quoteMs<=nowMs+120_000&&nowMs-quoteMs<=spotMaxAgeMinutes*MINUTE;
  const historyValid=Number.isFinite(histStart)&&Number.isFinite(histEnd)&&
    new Date(histStart).toISOString().slice(0,10)===historyLatestDate&&
    histStart<=nowMs+120_000&&nowMs-histEnd<=historyMaxAgeDays*DAY;
  const state=quoteValid&&historyValid?"live":historyValid?"history-only":quoteValid?"spot-only":"unavailable";
  return {state,quoteValid,historyValid};
}
