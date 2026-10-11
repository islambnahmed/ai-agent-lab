/**
 * Read-only, dependency-free adapter for a publicly documented dealer quote.
 * Documentation: https://standardbullion.com/gold-price-api
 * Dealer bid/ask midpoint is NOT identical to independent XAU/USD spot.
 * Provider time and local capture time are not independently witnessed.
 */
import {createHash} from 'node:crypto';
import {parseProviderUtcTimestamp} from './quote-core.mjs';

export const DEALER_ENDPOINT = 'https://standardbullion.com/spot-prices.json';
export const DEALER_SOURCE = 'standardbullion.com';
export const DEALER_BASIS = 'dealer_mid';
const MAX_BYTES = 64 * 1024;
const TEN_MINUTES = 10 * 60_000;
const assert = (ok, reason) => {if (!ok) throw new Error(reason);};

export function normalizeDealerSnapshot(raw, capturedMs, {maxAgeMs = TEN_MINUTES} = {}) {
  assert(typeof raw === 'string' && Buffer.byteLength(raw, 'utf8') <= MAX_BYTES && raw.length > 0, 'Invalid snapshot size');
  assert(Number.isSafeInteger(capturedMs) && capturedMs >= 0, 'Invalid local capture clock');
  assert(Number.isSafeInteger(maxAgeMs) && maxAgeMs >= 0 && maxAgeMs <= 86_400_000, 'Invalid freshness limit');
  let input;
  try { input = JSON.parse(raw); } catch { throw new Error('Invalid JSON'); }
  assert(input && typeof input === 'object' && !Array.isArray(input), 'Invalid response');
  assert(input.source === 'Standard Bullion', 'Unexpected provider');
  assert(input.unit === 'USD per troy ounce', 'Unexpected unit');
  assert(typeof input.attribution === 'string' && input.attribution.includes('standardbullion.com'), 'Missing attribution');
  const updatedMs = parseProviderUtcTimestamp(input.updated);
  assert(updatedMs <= capturedMs, 'Provider timestamp is later than local capture');
  assert(Array.isArray(input.metals), 'Missing metals');
  const gold = input.metals.filter(x => x && x.symbol === 'XAU');
  assert(gold.length === 1, 'Missing or duplicate gold entry');
  const {bid, ask} = gold[0];
  assert(typeof bid === 'number' && Number.isFinite(bid) && bid > 0 && bid <= 1_000_000, 'Invalid gold bid');
  assert(typeof ask === 'number' && Number.isFinite(ask) && ask >= bid && ask <= 1_000_000, 'Invalid gold ask');
  const price = (bid + ask) / 2;
  assert((ask - bid) / price <= 0.1, 'Implausibly wide dealer spread');
  const ageMs = capturedMs - updatedMs;
  return Object.freeze({
    row: Object.freeze({updatedAt:input.updated, capturedAt:new Date(capturedMs).toISOString(), price,
      source:DEALER_SOURCE, priceBasis:DEALER_BASIS}),
    evidence: Object.freeze({endpoint:DEALER_ENDPOINT, sha256:createHash('sha256').update(raw, 'utf8').digest('hex'),
      bid, ask, spread:ask-bid, attribution:input.attribution, ageMs,
      freshness:ageMs <= maxAgeMs ? 'fresh_by_provider_timestamp' : 'stale',
      independentlyWitnessed:false, prospectiveForecastRegistered:false}),
  });
}

/** Caller must store raw bytes and first-seen evidence; this fetch is NOT durable logging. */
export async function fetchDealerSnapshot({fetchImpl = fetch, clock = Date.now, timeoutMs = 8000} = {}) {
  assert(Number.isSafeInteger(timeoutMs) && timeoutMs > 0 && timeoutMs <= 30_000, 'Invalid timeout');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(DEALER_ENDPOINT, {method:'GET', cache:'no-store',
      headers:{Accept:'application/json'}, signal:controller.signal});
    if (!response.ok) throw new Error(`Provider HTTP ${response.status}`);
    const raw = await response.text();
    return Object.freeze({...normalizeDealerSnapshot(raw, clock()), raw});
  } finally { clearTimeout(timeout); }
}
