/**
 * Worker A: leakage-aware, dependency-free walk-forward comparison of two
 * fixed forecasting baselines. No live market connection, no trading advice.
 *
 * A row is {updatedAt, capturedAt, price} with strict UTC timestamps.
 * updatedAt = provider observation time; capturedAt = first known capture time.
 * The provided capture times are claims, not independently authenticated.
 */
import {parseProviderUtcTimestamp} from './quote-core.mjs';

const HOUR = 3_600_000;
const DAY = 24 * HOUR;
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const avg = values => values.reduce((sum, x) => sum + x, 0) / values.length;

export function validateObservations(rows) {
  assert(Array.isArray(rows) && rows.length >= 2, 'At least two observations required');
  let previousUpdated = -Infinity;
  return rows.map((row, i) => {
    assert(row && typeof row === 'object' && !Array.isArray(row), `row ${i}: invalid object`);
    const updatedMs = parseProviderUtcTimestamp(row.updatedAt);
    const capturedMs = parseProviderUtcTimestamp(row.capturedAt);
    assert(updatedMs > previousUpdated, `row ${i}: observation timestamps must be strictly increasing`);
    assert(capturedMs >= updatedMs, `row ${i}: captured before provider observation`);
    assert(typeof row.price === 'number' && Number.isFinite(row.price) && row.price > 0 && row.price <= 1_000_000,
      `row ${i}: invalid price`);
    previousUpdated = updatedMs;
    return Object.freeze({updatedMs, capturedMs, price:row.price, updatedAt:row.updatedAt, capturedAt:row.capturedAt});
  });
}

/** The drift baseline uses ONLY observations available at issue time. */
export function fixedBaselines(known, horizonMs, trendLookback = 3) {
  assert(Array.isArray(known) && known.length > 0, 'No known observations');
  assert(Number.isSafeInteger(horizonMs) && horizonMs > 0 && horizonMs <= 30 * DAY, 'Invalid horizon');
  assert(Number.isSafeInteger(trendLookback) && trendLookback >= 2 && trendLookback <= 100, 'Invalid lookback');
  const last = known.at(-1);
  const prior = known.slice(-trendLookback);
  let drift = last.price;
  if (prior.length >= 2) {
    const first = prior[0];
    const elapsed = last.updatedMs - first.updatedMs;
    assert(elapsed > 0, 'History not ordered');
    drift = Math.max(Number.EPSILON, last.price + (last.price - first.price) / elapsed * horizonMs);
  }
  return Object.freeze({persistence:last.price, drift});
}

export function walkForwardBenchmark(rows, {
  horizonMs = HOUR, minHistory = 3, trendLookback = 3, maxQuoteAgeMs = HOUR,
} = {}) {
  assert(Number.isSafeInteger(horizonMs) && horizonMs > 0 && horizonMs <= 30 * DAY, 'Invalid horizon');
  assert(Number.isSafeInteger(minHistory) && minHistory >= 2 && minHistory <= 1000, 'Invalid minimum history');
  assert(Number.isSafeInteger(trendLookback) && trendLookback >= 2 && trendLookback <= minHistory, 'Invalid trend lookback');
  assert(Number.isSafeInteger(maxQuoteAgeMs) && maxQuoteAgeMs >= 0 && maxQuoteAgeMs <= 30 * DAY, 'Invalid quote age');
  const data = validateObservations(rows);
  const byUpdated = new Map(data.map(row => [row.updatedMs, row]));
  const forecasts = [];
  const skipped = {warmup:0, stale:0, targetMissing:0, targetNotFuture:0, duplicateAnchor:0};

  for (const anchor of data) {
    // As-of filter excludes even historically earlier quotes that arrived late.
    const known = data.filter(row => row.updatedMs <= anchor.capturedMs && row.capturedMs <= anchor.capturedMs);
    if (known.length < minHistory) { skipped.warmup++; continue; }
    const last = known.at(-1);
    if (last !== anchor) { skipped.duplicateAnchor++; continue; }
    if (anchor.capturedMs - last.updatedMs > maxQuoteAgeMs) { skipped.stale++; continue; }
    const targetMs = last.updatedMs + horizonMs;
    const target = byUpdated.get(targetMs);
    if (!target) { skipped.targetMissing++; continue; }
    if (target.updatedMs <= anchor.capturedMs || target.capturedMs <= anchor.capturedMs) {
      skipped.targetNotFuture++;
      continue;
    }
    const prediction = fixedBaselines(known, horizonMs, trendLookback);
    forecasts.push(Object.freeze({
      issuedAt:anchor.capturedAt, targetAt:target.updatedAt,
      trainingThrough:last.updatedAt, trainingCount:known.length,
      targetCapturedAt:target.capturedAt, actual:target.price,
      ...prediction,
      persistenceAbsoluteError:Math.abs(prediction.persistence - target.price),
      driftAbsoluteError:Math.abs(prediction.drift - target.price),
    }));
  }
  const summary = forecasts.length ? Object.freeze({
    count:forecasts.length,
    persistenceMAE:avg(forecasts.map(x=>x.persistenceAbsoluteError)),
    driftMAE:avg(forecasts.map(x=>x.driftAbsoluteError)),
    persistenceRMSE:Math.sqrt(avg(forecasts.map(x=>x.persistenceAbsoluteError ** 2))),
    driftRMSE:Math.sqrt(avg(forecasts.map(x=>x.driftAbsoluteError ** 2))),
    driftStrictWinRate:forecasts.filter(x=>x.driftAbsoluteError < x.persistenceAbsoluteError).length / forecasts.length,
  }) : Object.freeze({count:0, persistenceMAE:null, driftMAE:null, persistenceRMSE:null, driftRMSE:null, driftStrictWinRate:null});
  return Object.freeze({
    instrument:'Synthetic or supplied XAU/USD indicative spot (USD per troy ounce)',
    horizonMs, minHistory, trendLookback, maxQuoteAgeMs,
    summary, skipped:Object.freeze(skipped), forecasts:Object.freeze(forecasts),
    caveat:'Historical capturedAt is untrusted without independent as-of evidence. No proof of prospective forecast registration or future performance.',
  });
}
