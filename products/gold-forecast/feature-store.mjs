// Point-in-time exogenous input contract. Historical observation date is not
// publication time. Current snapshots cannot be backfilled into past origins.
import {parseInstant} from './historical-integrity.mjs';
import {isDeepStrictEqual} from 'node:util';
export function availableFeatures(records,originAt,{maxAgeDays=30}={}){
  const origin=parseInstant(originAt),best=new Map(),seen=new Map();
  if(!Number.isFinite(maxAgeDays)||maxAgeDays<0)throw Error('Invalid feature age limit');
  for(const row of records){
    if(typeof row?.feature!=='string'||typeof row.source!=='string'||typeof row.vintage!=='string'||!Number.isFinite(row.value))throw Error('Invalid feature record');
    const observed=parseInstant(row.observedAt),available=parseInstant(row.availableAt);
    if(available<observed)throw Error('Feature available before observation');
    if(observed>origin||available>origin)continue;
    // Audit every eligible same-instant vintage, even if a newer revision wins.
    // Otherwise a later revision can hide an earlier conflict, and identical
    // values from different sources can silently change provenance by row order.
    const key=JSON.stringify([row.feature,observed,available]);
    // Two differently formatted timestamps can denote the same instant.
    // Compare and emit canonical UTC instants without weakening source/vintage checks.
    const canonicalRow={...row,observedAt:new Date(observed).toISOString(),availableAt:new Date(available).toISOString()};
    const prior=seen.get(key);
    if(prior&&!isDeepStrictEqual(prior,canonicalRow))throw Error('Conflicting same-vintage feature provenance');
    if(!prior)seen.set(key,canonicalRow);
    const old=best.get(row.feature);
    if(!old||observed>old.observed||observed===old.observed&&available>old.available)best.set(row.feature,{row:canonicalRow,observed,available});
    // Equal-key conflicts are checked independently of which revision wins.
  }
  return Object.fromEntries([...best].map(([key,{row,observed}])=>[key,{...row,ageDays:(origin-observed)/86400000,stale:origin-observed>maxAgeDays*86400000}]));
}
