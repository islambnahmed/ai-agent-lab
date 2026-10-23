import {createHash} from 'node:crypto';

/** A reference model for an idempotency *contract*, not a durable distributed ledger.
 * Stable intent identity is distinct from request payload and from execution authorization.
 */
function canonical(value, seen=new Set()) {
  if(value===null || typeof value==='string' || typeof value==='boolean') return JSON.stringify(value);
  if(typeof value==='number') {
    if(!Number.isFinite(value)) throw new TypeError('Non-finite number');
    return JSON.stringify(value);
  }
  if(Array.isArray(value)) {
    if(seen.has(value)) throw new TypeError('Cycle');
    if(Object.keys(value).length!==value.length || Array.from({length:value.length},(_,i)=>Object.hasOwn(value,i)).some(v=>!v)) throw new TypeError('Sparse or decorated array');
    seen.add(value);
    const out='['+value.map(x=>canonical(x,seen)).join(',')+']';
    seen.delete(value); return out;
  }
  if(typeof value!=='object'||Object.getPrototypeOf(value)!==Object.prototype) throw new TypeError('JSON plain object required');
  if(seen.has(value)) throw new TypeError('Cycle');
  if(Object.getOwnPropertySymbols(value).length)throw new TypeError('Symbol keys unsupported');
  if(Object.values(Object.getOwnPropertyDescriptors(value)).some(d=>!Object.hasOwn(d,'value')))throw new TypeError('Accessors unsupported');
  seen.add(value);
  const keys=Object.keys(value).sort();
  const out='{'+keys.map(k=>{
    if(['__proto__','constructor','prototype'].includes(k)) throw new TypeError('Reserved key');
    return JSON.stringify(k)+':'+canonical(value[k],seen);
  }).join(',')+'}';
  seen.delete(value);return out;
}
const digest=v=>createHash('sha256').update(canonical(v),'utf8').digest('hex');
function requireId(s,label) {
  if(typeof s!=='string'||s.length<1||s.length>180||s.trim()!==s||/[\x00-\x1f]/.test(s))throw new TypeError('Invalid '+label);
  return s;
}
const operations=new Set(['gold.receipt.issue','gold.receipt.settle','seo.page.publish']);
export function intentKey({tenantId,operation,resourceId,intentId}) {
  for(const [key,val] of Object.entries({tenantId,operation,resourceId,intentId}))requireId(val,key);
  if(!operations.has(operation)) throw new TypeError('Unknown operation');
  return digest({v:1,tenantId,operation,resourceId,intentId});
}
export function payloadDigest(payload) {return digest(payload);}
export class ReferenceLedger {
  #entries=new Map();
  reserve(scope,payload) {
    const key=intentKey(scope), content=payloadDigest(payload);
    const existing=this.#entries.get(key);
    if(existing) {
      if(existing.content!==content)return {kind:'conflict',key};
      return {kind:'retry',key,existingStatus:existing.status};
    }
    this.#entries.set(key,{content,status:'reserved'});
    return {kind:'new',key};
  }
  markComplete(key) {
    const record=this.#entries.get(key);
    if(!record)throw new TypeError('Unknown reservation');
    record.status='complete';
  }
  get size(){return this.#entries.size;}
}
