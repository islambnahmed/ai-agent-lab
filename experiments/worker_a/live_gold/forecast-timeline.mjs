/**
 * Worker A: leakage-resistant, replayable evaluation of indicative XAU/USD forecasts.
 * No network access. Never treat indicative spot as an official close or settlement.
 */
import {normalizeQuote, parseProviderUtcTimestamp} from './quote-core.mjs';

const HOUR_MS = 60 * 60_000;
const DEFAULT_MAX_OBSERVATION_LAG_MS = 5 * 60_000;

function stamp(s, field) {
  try { return parseProviderUtcTimestamp(s); }
  catch { throw new Error(`${field}: invalid UTC timestamp`); }
}
function ensure(condition, message) {
  if (!condition) throw new Error(message);
}
function money(n, field) {
  ensure(typeof n === 'number' && Number.isFinite(n) && n > 0 && n <= 1_000_000, `${field}: invalid USD price`);
  return n;
}
function quoteEvidence(input, field) {
  ensure(input && typeof input === 'object' && !Array.isArray(input), `${field}: missing quote`);
  const capturedMs = stamp(input.capturedAt, `${field}.capturedAt`);
  const providerMs = stamp(input.updatedAt, `${field}.updatedAt`);
  ensure(providerMs <= capturedMs, `${field}: provider timestamp later than capture`);
  // Reuse the same instrument/price checks as the live quote adapter.
  const normalized = normalizeQuote(input, capturedMs);
  return {capturedMs, providerMs, price:normalized.price};
}

/**
 * Evaluate a precommitted forecast against a later captured quote.
 * A 'verified' result only means timeline evidence is internally consistent.
 * It does NOT independently authenticate the provider or establish a market close.
 */
export function evaluateForecastTimeline(forecast, observation = null, {maxObservationLagMs = DEFAULT_MAX_OBSERVATION_LAG_MS} = {}) {
  ensure(forecast && typeof forecast === 'object' && !Array.isArray(forecast), 'forecast: invalid object');
  ensure(Number.isSafeInteger(maxObservationLagMs) && maxObservationLagMs >= 0 && maxObservationLagMs <= HOUR_MS, 'maxObservationLagMs: invalid');
  const createdMs = stamp(forecast.createdAt, 'forecast.createdAt');
  const targetMs = stamp(forecast.targetAt, 'forecast.targetAt');
  const trainedMs = stamp(forecast.trainedThrough, 'forecast.trainedThrough');
  const predicted = money(forecast.predictedUsd, 'forecast.predictedUsd');
  ensure(trainedMs <= createdMs, 'lookahead: training cutoff after forecast creation');
  ensure(targetMs > createdMs, 'lookahead: target must be after forecast creation');
  const input = quoteEvidence(forecast.inputQuote, 'forecast.inputQuote');
  ensure(input.capturedMs <= createdMs, 'lookahead: input captured after forecast creation');
  ensure(input.providerMs <= createdMs, 'lookahead: input updated after forecast creation');
  if (observation === null) {
    return Object.freeze({status:'pending', reason:'missing_evaluation_quote', targetAt:forecast.targetAt});
  }
  const actual = quoteEvidence(observation, 'observation');
  ensure(actual.providerMs >= targetMs, 'lookahead: observation predates target');
  ensure(actual.providerMs - targetMs <= maxObservationLagMs, 'observation: too far after target');
  ensure(actual.capturedMs >= targetMs, 'observation: captured before target');
  ensure(actual.capturedMs >= createdMs, 'observation: captured before forecast');
  return Object.freeze({
    status:'verified',
    instrument:'XAU/USD indicative spot',
    targetAt:forecast.targetAt,
    predictedUsd:predicted,
    observedUsd:actual.price,
    absoluteErrorUsd:Math.abs(predicted-actual.price),
    absolutePercentageError:Math.abs(predicted-actual.price)/actual.price*100,
    observationLagMs:actual.providerMs-targetMs,
    warning:'Timeline checks only; provider truth, independent timestamp anchoring, and official settlement are not verified.'
  });
}
