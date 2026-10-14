// Point-in-time exogenous input contract. Historical observation date is not
// publication time. Current snapshots cannot be backfilled into past origins.
import {parseInstant} from './historical-integrity.mjs';
export function availableFeatures(records,originAt,{maxAgeDays=30}={}){
  const origin=parseInstant(originAt),best=new Map();
  if(!Number.isFinite(maxAgeDays)||maxAgeDays<0)throw Error('Invalid feature age limit');
  for(const row of records){
    if(typeof row?.feature!=='string'||typeof row.source!=='string'||typeof row.vintage!=='string'||!Number.isFinite(row.value))throw Error('Invalid feature record');
    const observed=parseInstant(row.observedAt),available=parseInstant(row.availableAt);
    if(available<observed)throw Error('Feature available before observation');
    // ALFRED vintage IDs denote an as-of calendar day, not an opaque revision
    // number. Monthly snapshots may not be used before that UTC day ends.
    // Other providers may use opaque vintage identifiers, so only enforce
    // this source-specific contract for ALFRED records.
    if(row.source.startsWith('ALFRED:')){
      if(!/^\d{4}-\d{2}-\d{2}$/.test(row.vintage))throw Error('Invalid ALFRED vintage day');
      const dayStart=Date.parse(row.vintage+'T00:00:00Z');
      if(!Number.isFinite(dayStart)||new Date(dayStart).toISOString().slice(0,10)!==row.vintage)
        throw Error('Invalid ALFRED vintage calendar date');
      const vintageEnd=dayStart+86400000-1;
      if(observed>vintageEnd)throw Error('ALFRED observation postdates vintage');
      if(available<vintageEnd)throw Error('ALFRED vintage backdated before end of UTC day');
    }
    if(observed>origin||available>origin)continue;
    const old=best.get(row.feature);
    if(!old||observed>old.observed||observed===old.observed&&available>old.available)best.set(row.feature,{row,observed,available});
    else if(observed===old.observed&&available===old.available&&row.value!==old.row.value)throw Error('Conflicting same-vintage feature');
  }
  return Object.fromEntries([...best].map(([key,{row,observed}])=>[key,{...row,ageDays:(origin-observed)/86400000,stale:origin-observed>maxAgeDays*86400000}]));
}
