/**
 * Worker A: conservative, dependency-free paired forecast diagnostics.
 * Forecast rows are retrospective claims, NOT independently time-anchored.
 * No inference of market profitability or real-world predictive accuracy.
 */
import {parseProviderUtcTimestamp} from './quote-core.mjs';

const ensure = (condition, message) => { if (!condition) throw new Error(message); };
const positivePrice = (x, field) => {
  ensure(typeof x === 'number' && Number.isFinite(x) && x > 0 && x <= 1_000_000, `${field}: invalid price`);
  return x;
};
const average = xs => xs.reduce((sum, x) => sum + x, 0) / xs.length;

/** Exact, one-sided Binomial(n, 0.5) upper-tail P(X >= wins). Ties excluded. */
export function exactSignTail(wins, n) {
  ensure(Number.isSafeInteger(n) && n >= 1 && n <= 100_000, 'invalid decisive count');
  ensure(Number.isSafeInteger(wins) && wins >= 0 && wins <= n, 'invalid wins');
  const logFactorial = [0];
  for (let i = 1; i <= n; i++) logFactorial.push(logFactorial[i-1] + Math.log(i));
  const terms = [];
  const logTwo = Math.log(2);
  for (let k = wins; k <= n; k++) {
    terms.push(logFactorial[n] - logFactorial[k] - logFactorial[n-k] - n*logTwo);
  }
  let max = -Infinity;
  for (const t of terms) if (t > max) max = t;
  // Iteration avoids exceeding JS function-argument limits on long series.
  let sum = 0;
  for (const t of terms) sum += Math.exp(t - max);
  return Math.min(1, Math.exp(max) * sum);
}

/**
 * Select non-overlapping forecast windows using timing only (earliest finish).
 * This prevents double-counting overlapping targets, not serial dependence.
 */
export function pairedEvidence(forecasts, {minSelected = 30, minDecisive = 20, alpha = 0.05} = {}) {
  ensure(Array.isArray(forecasts), 'forecasts must be an array');
  ensure(Number.isSafeInteger(minSelected) && minSelected >= 1, 'invalid minSelected');
  ensure(Number.isSafeInteger(minDecisive) && minDecisive >= 1, 'invalid minDecisive');
  ensure(typeof alpha === 'number' && Number.isFinite(alpha) && alpha > 0 && alpha < 1, 'invalid alpha');

  const validated = forecasts.map((f, index) => {
    ensure(f && typeof f === 'object' && !Array.isArray(f), `forecast ${index}: invalid`);
    const issued = parseProviderUtcTimestamp(f.issuedAt);
    const target = parseProviderUtcTimestamp(f.targetAt);
    const captured = parseProviderUtcTimestamp(f.targetCapturedAt);
    ensure(issued < target && target <= captured, `forecast ${index}: invalid timeline`);
    const actual = positivePrice(f.actual, 'actual');
    const persistence = positivePrice(f.persistence, 'persistence');
    const drift = positivePrice(f.drift, 'drift');
    const persistenceError = Math.abs(actual - persistence);
    const driftError = Math.abs(actual - drift);
    // We recompute losses instead of trusting serialized scores.
    return {issued, target, captured, persistenceError, driftError};
  });
  validated.sort((a,b) => a.target - b.target || a.issued - b.issued);
  const seen = new Set();
  for (const f of validated) {
    const key = `${f.issued}/${f.target}`;
    ensure(!seen.has(key), 'duplicate forecast issue/target pair');
    seen.add(key);
  }
  const selected = [];
  let previousTarget = -Infinity;
  for (const f of validated) {
    if (f.issued >= previousTarget) {
      selected.push(f);
      previousTarget = f.target;
    }
  }
  let wins = 0, losses = 0, ties = 0;
  for (const f of selected) {
    if (f.driftError < f.persistenceError) wins++;
    else if (f.driftError > f.persistenceError) losses++;
    else ties++;
  }
  const decisive = wins + losses;
  const persistenceMAE = selected.length ? average(selected.map(f => f.persistenceError)) : null;
  const driftMAE = selected.length ? average(selected.map(f => f.driftError)) : null;
  const p = decisive ? exactSignTail(wins, decisive) : null;
  const sufficient = selected.length >= minSelected && decisive >= minDecisive;
  const flag = !sufficient ? 'insufficient_sample' :
    (driftMAE < persistenceMAE && p <= alpha ? 'candidate_drift_advantage' : 'no_demonstrated_drift_advantage');
  return Object.freeze({
    allCount:validated.length, selectedCount:selected.length,
    droppedOverlaps:validated.length - selected.length,
    wins, losses, ties, decisive,
    persistenceMAE, driftMAE,
    oneSidedSignP:p, alpha, minSelected, minDecisive, flag,
    caveat:'Exploratory paired diagnostic only. Non-overlap does not eliminate serial dependence, selection bias, retrospective capture claims, or model-selection bias. No real-market performance claim.'
  });
}
