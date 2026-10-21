// Research-only candidate: JSON provenance equality and byte-stable selection.
// Not a production replacement; keep raw vendor bytes separately if needed.
import {parseInstant} from './historical-integrity.mjs';

export function canonicalJson(value) {
  const ancestors=new WeakSet();
  function encode(x) {
    if(x===null)return 'n';
    if(typeof x==='string')return 's'+JSON.stringify(x);
    if(typeof x==='boolean')return x?'b1':'b0';
    if(typeof x==='number'){
      if(!Number.isFinite(x))throw Error('Non-finite feature metadata');
      return Object.is(x,-0)?'d-0':'d'+JSON.stringify(x);
    }
    if(typeof x!=='object')throw Error('Non-JSON feature metadata');
    if(ancestors.has(x))throw Error('Cyclic feature metadata');
    const proto=Object.getPrototypeOf(x);
    if(!Array.isArray(x)&&proto!==Object.prototype&&proto!==null)throw Error('Non-plain feature metadata');
    ancestors.add(x);
    let out;
    if(Array.isArray(x)){
      if(Object.keys(x).length!==x.length)throw Error('Sparse or augmented feature metadata array');
      out='a['+x.map(encode).join(',')+']';
    }else{
      out='o{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+encode(x[k])).join(',')+'}';
    }
    ancestors.delete(x);
    return out;
  }
  return encode(value);
}
function canonicalClone(x){
  if(Array.isArray(x))return x.map(canonicalClone);
  if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonicalClone(x[k])]));
  return x;
}
export function availableFeatures(records,originAt,{maxAgeDays=30}={}){
  const origin=parseInstant(originAt),best=new Map(),seen=new Map();
  if(!Array.isArray(records)||!Number.isFinite(maxAgeDays)||maxAgeDays<0)throw Error('Invalid feature input or age limit');
  for(const row of records){
    if(!row||typeof row!=='object'||Array.isArray(row)||typeof row.feature!=='string'||
       typeof row.source!=='string'||typeof row.vintage!=='string'||!Number.isFinite(row.value))
      throw Error('Invalid feature record');
    const observed=parseInstant(row.observedAt),available=parseInstant(row.availableAt);
    if(available<observed)throw Error('Feature available before observation');
    if(observed>origin||available>origin)continue;
    const fingerprint=canonicalJson(row);
    const key=JSON.stringify([row.feature,observed,available]);
    const prior=seen.get(key);
    if(prior!==undefined&&prior!==fingerprint)throw Error('Conflicting same-vintage feature content or provenance');
    seen.set(key,fingerprint);
    const old=best.get(row.feature);
    if(!old||observed>old.observed||observed===old.observed&&available>old.available)
      best.set(row.feature,{row:canonicalClone(row),observed,available});
  }
  return Object.fromEntries([...best].sort(([a],[b])=>a<b?-1:a>b?1:0).map(([key,{row,observed}])=>
    [key,{...row,ageDays:(origin-observed)/86400000,stale:origin-observed>maxAgeDays*86400000}]));
}
