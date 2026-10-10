/**
 * Worker A: dependency-free indicative XAU/USD quote adapter.
 * Docs: https://gold-api.com/llms.txt
 * Terms: https://gold-api.com/terms
 * Not a daily closing price, settlement price, or forecast evaluation source.
 */
export const ENDPOINT = 'https://api.gold-api.com/price/XAU';
export const REFRESH_MS = 60_000;
export const FRESH_MS = 10 * 60_000;

/** Reject calendar rollovers that Date.parse silently normalizes (e.g. February 30). */
export function parseProviderUtcTimestamp(value) {
  if (typeof value !== 'string') throw new Error('Missing UTC timestamp');
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?Z$/.exec(value);
  if (!m) throw new Error('Missing UTC timestamp');
  const [, year, month, day, hour, minute, second] = m;
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error('Invalid UTC timestamp');
  const d = new Date(parsed);
  if (d.getUTCFullYear() !== Number(year) || d.getUTCMonth() + 1 !== Number(month) ||
      d.getUTCDate() !== Number(day) || d.getUTCHours() !== Number(hour) ||
      d.getUTCMinutes() !== Number(minute) || d.getUTCSeconds() !== Number(second)) {
    throw new Error('Invalid UTC calendar timestamp');
  }
  return parsed;
}

export function normalizeQuote(input, nowMs = Date.now()) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Invalid response object');
  if (input.symbol !== 'XAU' || input.currency !== 'USD') throw new Error('Unexpected instrument or currency');
  if (typeof input.price !== 'number' || !Number.isFinite(input.price) || input.price <= 0 || input.price > 1_000_000) {
    throw new Error('Invalid price');
  }
  if (!Number.isFinite(nowMs)) throw new Error('Invalid observation clock');
  const timestampMs = parseProviderUtcTimestamp(input.updatedAt);
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
