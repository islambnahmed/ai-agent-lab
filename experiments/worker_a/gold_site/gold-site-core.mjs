/** Dependency-free, intentionally modest XAU/USD forecast *baseline* demo.
 * No AI skill claim. Client clock, quote provider, and localStorage are untrusted.
 */
export const HORIZON_MS = 75 * 60_000;
export const MAX_QUOTE_AGE_MS = 10 * 60_000;
export const MAX_OUTCOME_LAG_MS = 10 * 60_000;
export const MAX_ISSUE_DELAY_MS = 15_000;
export const MAX_LEDGER_ENTRIES = 1000;
const iso = ms => new Date(ms).toISOString();
const safeTime = value => {
  if (typeof value !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?Z$/.test(value)) throw new Error('UTC timestamp required');
  const t = Date.parse(value);
  if (!Number.isFinite(t) || new Date(t).toISOString().slice(0,19) !== value.slice(0,19)) throw new Error('Invalid UTC timestamp');
  return t;
};
export function normalizeQuote(raw, nowMs) {
  if (!raw || raw.symbol !== 'XAU' || raw.currency !== 'USD') throw new Error('Unexpected instrument');
  if (!Number.isFinite(raw.price) || raw.price <= 0 || raw.price > 1_000_000) throw new Error('Invalid price');
  if (!Number.isSafeInteger(nowMs)) throw new Error('Invalid capture clock');
  const updatedMs = safeTime(raw.updatedAt);
  if (updatedMs > nowMs + 120_000) throw new Error('Provider timestamp ahead of local clock');
  return Object.freeze({price:raw.price, updatedAt:iso(updatedMs), updatedMs, capturedAt:iso(nowMs), capturedMs:nowMs,
    ageMs:nowMs-updatedMs, source:'gold-api.com', priceBasis:'indicative_unknown'});
}
/** Issue time is the actual registration click, not the earlier quote-fetch time.
 * Refuse delayed registrations and recheck freshness at issuance.
 */
export function createBaseline(quote, issueMs) {
  if (!quote || !Number.isSafeInteger(issueMs) || !Number.isSafeInteger(quote.capturedMs)) throw new Error('Invalid issuance clock');
  const issueDelayMs=issueMs-quote.capturedMs;
  if (issueDelayMs<0 || issueDelayMs>MAX_ISSUE_DELAY_MS) throw new Error('Issue time outside quote capture window');
  if (!Number.isSafeInteger(quote.updatedMs) || quote.updatedMs>issueMs) throw new Error('Provider observation is not yet available');
  const quoteAgeAtIssueMs=issueMs-quote.updatedMs;
  if (quoteAgeAtIssueMs>MAX_QUOTE_AGE_MS) throw new Error('Quote is too stale for forecast');
  const targetMs=issueMs+HORIZON_MS;
  return Object.freeze({id:`${issueMs}-${Math.round(quote.price*1000)}`, issuedAt:iso(issueMs),
    observedAt:quote.updatedAt,quoteCapturedAt:quote.capturedAt,issueDelayMs,quoteAgeAtIssueMs,
    targetAt:iso(targetMs), priceAtIssue:quote.price, prediction:quote.price,
    model:'persistence_v1', horizonMinutes:75, source:quote.source,
    status:'pending', outcome:null});
}
export function evaluatePending(forecast, quote) {
  if (!forecast || forecast.status !== 'pending') return forecast;
  const targetMs = safeTime(forecast.targetAt);
  if (quote.capturedMs > targetMs + MAX_OUTCOME_LAG_MS) return Object.freeze({...forecast,status:'expired',outcome:null});
  if (quote.updatedMs < targetMs) return forecast;
  if (quote.updatedMs > targetMs + MAX_OUTCOME_LAG_MS) return Object.freeze({...forecast,status:'expired',outcome:null});
  if (quote.capturedMs < targetMs || quote.capturedMs < quote.updatedMs || quote.ageMs > MAX_QUOTE_AGE_MS) return forecast;
  return Object.freeze({...forecast,status:'evaluated',outcome:Object.freeze({
    price:quote.price, observedAt:quote.updatedAt, capturedAt:quote.capturedAt,
    absoluteError:Math.abs(quote.price-forecast.prediction),
    direction:'none', captureEvidence:'self-reported-browser-clock',
  })});
}
/** Fail closed on malformed history instead of silently deleting rows or
 * letting an invalid pending target crash the next refresh. The controller
 * must preserve the original localStorage bytes when this throws.
 */
function validLedgerEntry(x) {
  if (!x || typeof x!=='object' || Array.isArray(x) ||
      typeof x.id!=='string' || !x.id ||
      !['pending','evaluated','expired'].includes(x.status) ||
      typeof x.source!=='string' || !x.source ||
      typeof x.model!=='string' || !x.model ||
      !Number.isFinite(x.prediction) || x.prediction<=0 ||
      !Number.isFinite(x.priceAtIssue) || x.priceAtIssue<=0 ||
      !Number.isSafeInteger(x.horizonMinutes) || x.horizonMinutes<=0) return false;
  try {
    const issued=safeTime(x.issuedAt), target=safeTime(x.targetAt), observed=safeTime(x.observedAt);
    if (target-issued!==x.horizonMinutes*60_000 || observed>issued) return false;
    if (x.status==='evaluated') {
      const o=x.outcome;
      if (!o || typeof o!=='object' || !Number.isFinite(o.price) || o.price<=0 ||
          !Number.isFinite(o.absoluteError) || o.absoluteError<0 ||
          Math.abs(o.absoluteError-Math.abs(o.price-x.prediction))>1e-6) return false;
      const outcomeObserved=safeTime(o.observedAt), outcomeCaptured=safeTime(o.capturedAt);
      if (outcomeObserved<target || outcomeObserved>target+MAX_OUTCOME_LAG_MS ||
          outcomeCaptured<outcomeObserved || outcomeCaptured>target+MAX_OUTCOME_LAG_MS ||
          outcomeCaptured-outcomeObserved>MAX_QUOTE_AGE_MS) return false;
    } else if (x.outcome!=null) return false;
    return true;
  } catch {return false;}
}
export function loadLedger(storageText) {
  if (storageText == null) return [];
  let data;
  try {data=JSON.parse(storageText);} catch {throw new Error('Invalid local ledger');}
  if (!Array.isArray(data) || data.length>MAX_LEDGER_ENTRIES || !data.every(validLedgerEntry)) throw new Error('Invalid local ledger');
  const ids=new Set(), observations=new Set();
  for (const entry of data) {
    // Preserve original bytes rather than silently discarding duplicate history.
    const observationKey=JSON.stringify([entry.source,entry.observedAt,entry.model,entry.horizonMinutes]);
    if (ids.has(entry.id) || observations.has(observationKey)) throw new Error('Invalid local ledger');
    ids.add(entry.id); observations.add(observationKey);
  }
  return data;
}
/** One registered forecast per provider observation per model/horizon.
 * Multiple clicks (or re-fetching the same provider timestamp) must not
 * inflate the apparent evaluation sample size.
 */
export function hasObservation(ledger, forecast) {
  return ledger.some(x=>x.id===forecast.id ||
    (x.source===forecast.source && x.observedAt===forecast.observedAt &&
     x.model===forecast.model && x.horizonMinutes===forecast.horizonMinutes));
}
export function appendIfNew(ledger, forecast) {
  if (hasObservation(ledger, forecast)) return ledger;
  if (ledger.length>=MAX_LEDGER_ENTRIES) throw new Error('Ledger capacity reached; export existing history before adding forecasts');
  return [...ledger,forecast];
}
