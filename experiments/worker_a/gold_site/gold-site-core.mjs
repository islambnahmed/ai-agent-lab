/** Worker A: explicit 75-minute persistence baseline, not an AI forecast claim. */
export const HORIZON_MS=75*60000;
export const MAX_QUOTE_AGE_MS=10*60000;
export const MAX_OUTCOME_LAG_MS=10*60000;
const iso=t=>new Date(t).toISOString();
function safeTime(s){
 if(typeof s!=='string'||!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/.test(s))throw Error('UTC timestamp required');
 const t=Date.parse(s);
 if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,19)!==s.slice(0,19))throw Error('Invalid UTC timestamp');
 return t;
}
export function normalizeQuote(raw,nowMs){
 if(!raw||raw.symbol!=='XAU'||raw.currency!=='USD')throw Error('Unexpected instrument');
 if(!Number.isFinite(raw.price)||raw.price<=0||raw.price>1000000)throw Error('Invalid price');
 if(!Number.isSafeInteger(nowMs))throw Error('Invalid capture clock');
 const updatedMs=safeTime(raw.updatedAt);
 if(updatedMs>nowMs+120000)throw Error('Provider timestamp ahead of local clock');
 return Object.freeze({price:raw.price,updatedAt:iso(updatedMs),updatedMs,capturedAt:iso(nowMs),capturedMs:nowMs,ageMs:nowMs-updatedMs,source:'gold-api.com',priceBasis:'indicative_unknown'});
}
export function createBaseline(quote,nowMs){
 if(!quote||!Number.isSafeInteger(nowMs)||nowMs!==quote.capturedMs)throw Error('Capture time mismatch');
 if(quote.updatedMs>nowMs)throw Error('Provider observation is not yet available');
 if(quote.ageMs>MAX_QUOTE_AGE_MS)throw Error('Quote is too stale for forecast');
 return Object.freeze({id:String(nowMs)+'-'+String(Math.round(quote.price*1000)),issuedAt:iso(nowMs),observedAt:quote.updatedAt,targetAt:iso(nowMs+HORIZON_MS),priceAtIssue:quote.price,prediction:quote.price,model:'persistence_v1',horizonMinutes:75,source:quote.source,status:'pending',outcome:null});
}
export function evaluatePending(forecast,quote){
 if(!forecast||forecast.status!=='pending')return forecast;
 const targetMs=safeTime(forecast.targetAt);
 if(quote.updatedMs<targetMs)return forecast;
 if(quote.updatedMs>targetMs+MAX_OUTCOME_LAG_MS)return Object.freeze({...forecast,status:'expired',outcome:null});
 if(quote.capturedMs<targetMs||quote.capturedMs<quote.updatedMs||quote.ageMs>MAX_QUOTE_AGE_MS)return forecast;
 return Object.freeze({...forecast,status:'evaluated',outcome:Object.freeze({price:quote.price,observedAt:quote.updatedAt,capturedAt:quote.capturedAt,absoluteError:Math.abs(quote.price-forecast.prediction),direction:'none',captureEvidence:'self-reported-browser-clock'})});
}
export function loadLedger(s){
 if(s==null)return [];
 const data=JSON.parse(s);
 if(!Array.isArray(data)||data.length>1000)throw Error('Invalid local ledger');
 return data.filter(x=>x&&typeof x.id==='string'&&typeof x.status==='string').slice(-100);
}
export function appendIfNew(ledger,forecast){
 if(ledger.some(x=>x.id===forecast.id))return ledger;
 return [...ledger,forecast].slice(-100);
}
