// Validates observation cadence at the ingestion boundary, before normalization.
// A valid session cadence does not authenticate the source or guarantee price accuracy.
import {normalize} from './forecast.mjs';
import {auditDailyCadence} from './cadence_gate.mjs';

export function prepareGoldSeries(raw,{mode='csv',asOf=new Date().toISOString(),maxAgeDays=7,minLength=165}={}){
  if(!['live','csv','demo'].includes(mode))throw Error('SOURCE_INVALID_MODE');
  const policy=mode==='live'?{asOf,maxAgeDays}:{};
  const cadence=auditDailyCadence(raw,policy);
  const series=normalize(raw);
  if(series.length<minLength)throw Error('SOURCE_INSUFFICIENT_SESSIONS');
  if(mode==='live'){
    const asOfDay=new Date(asOf).toISOString().slice(0,10);
    // A current-day price must not be treated as a completed daily close.
    if(series.at(-1).date>=asOfDay)throw Error('SOURCE_UNFINALIZED_DAILY_CLOSE');
  }
  return {series,cadence};
}
