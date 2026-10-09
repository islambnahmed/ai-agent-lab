/**
 * Worker A: dependency-free indicative XAU/USD quote adapter.
 * Docs: https://gold-api.com/llms.txt
 * Terms: https://gold-api.com/terms
 * Not a daily closing price, settlement price, or forecast evaluation source.
 */
export const ENDPOINT = 'https://api.gold-api.com/price/XAU';
export const REFRESH_MS = 60_000;
export const FRESH_MS = 10 * 60_000;

export function normalizeQuote(input, nowMs = Date.now()) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Invalid response object');
  if (input.symbol !== 'XAU' || input.currency !== 'USD') throw new Error('Unexpected instrument or currency');
  if (typeof input.price !== 'number' || !Number.isFinite(input.price) || input.price <= 0 || input.price > 1_000_000) {
    throw new Error('Invalid price');
  }
  if (typeof input.updatedAt !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(input.updatedAt)) {
    throw new Error('Missing UTC timestamp');
  }
  const timestampMs = Date.parse(input.updatedAt);
  if (!Number.isFinite(timestampMs)) throw new Error('Invalid UTC timestamp');
  const ageMs = nowMs - timestampMs;
  if (ageMs < -120_000) throw new Error('Provider timestamp is in the future');
  return Object.freeze({
    price: input.price,
    updatedAt: input.updatedAt,
    ageMs: Math.max(0, ageMs),
    isFresh: ageMs <= FRESH_MS,
    source: 'gold-api.com',
    instrument: 'XAU/USD indicative spot'
  });
}

export async function fetchQuote({fetchImpl = fetch, nowMs = Date.now(), timeoutMs = 8000} = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(ENDPOINT, {
      method: 'GET',
      signal: controller.signal,
      headers: {Accept: 'application/json'}
    });
    if (!response.ok) throw new Error(`Provider HTTP ${response.status}`);
    return normalizeQuote(await response.json(), nowMs);
  } finally {
    clearTimeout(timeout);
  }
}

export function quoteLabel(quote) {
  return quote.isFresh ? 'سعر استرشادي حديث' : 'آخر سعر متاح — قديم أو السوق مغلق';
}
