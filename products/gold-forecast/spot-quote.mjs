/** Fail-closed dealer quote validation. A valid quote is not proof of source authenticity. */
const ZONED=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?:Z|[+-]\d{2}:\d{2})$/;
function price(value,label){
  if(typeof value!=='number' && (typeof value!=='string'|| !/^\d+(?:\.\d+)?$/.test(value.trim())))throw Error('Invalid '+label);
  const n=Number(value);
  if(!Number.isFinite(n)||n<=0)throw Error('Invalid '+label);
  return n;
}
export function validateSpotQuote(payload,asOf,{maxAgeMs=86400000,futureToleranceMs=120000}={}){
  const now=Date.parse(asOf);
  if(typeof asOf!=='string'||!ZONED.test(asOf)||!Number.isFinite(now))throw Error('Explicit asOf timestamp required');
  if(!Number.isSafeInteger(maxAgeMs)||maxAgeMs<0||!Number.isSafeInteger(futureToleranceMs)||futureToleranceMs<0)throw Error('Invalid quote gate options');
  if(!payload||!Array.isArray(payload.metals))throw Error('Invalid spot payload');
  const matches=payload.metals.filter(m=>m?.symbol==='XAU');
  if(matches.length!==1)throw Error('Expected exactly one XAU quote');
  const ask=price(matches[0].ask,'ask'),bid=price(matches[0].bid,'bid');
  if(ask<bid)throw Error('Crossed quote: ask below bid');
  const updated=payload.updated;
  if(typeof updated!=='string'||!ZONED.test(updated))throw Error('Quote timestamp must include timezone');
  const timestamp=Date.parse(updated);
  if(!Number.isFinite(timestamp))throw Error('Invalid quote timestamp');
  const ageMs=now-timestamp;
  if(ageMs>maxAgeMs)throw Error('Stale spot quote');
  if(ageMs< -futureToleranceMs)throw Error('Future-dated spot quote');
  return {ask,bid,updated,ageMs};
}
