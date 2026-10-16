/**
 * Descriptive scoring of externally VERIFIED prospective forecast/outcome pairs.
 * This module DOES NOT verify receipts, timestamps, market-source equivalence,
 * or independence. Only supply pairs after those checks have been completed.
 * No model selection or automatic promotion is performed here.
 */
const HORIZONS = new Set([1, 7, 30]);
const finite = x => typeof x === 'number' && Number.isFinite(x);
const avg = xs => xs.reduce((s, x) => s + x, 0) / xs.length;

export function intervalScore(actual, lower, upper, alpha = 0.2) {
  if (![actual, lower, upper, alpha].every(finite) || actual <= 0 || lower < 0 ||
      upper < lower || alpha <= 0 || alpha >= 1) {
    throw new Error('Invalid interval score inputs');
  }
  const width = upper - lower;
  return width + (actual < lower ? 2 * (lower - actual) / alpha : 0) +
    (actual > upper ? 2 * (actual - upper) / alpha : 0);
}

/**
 * Required row fields: id, horizon, actual, point, baselinePoint, lower, upper.
 * Rows MUST be independently matched to the same provider/close definition,
 * frozen prediction and subsequent published outcome before being passed here.
 */
export function scoreCohort(rows, { alpha = 0.2, horizon } = {}) {
  if (!Array.isArray(rows) || !rows.length || !finite(alpha) || alpha <= 0 || alpha >= 1 ||
      !HORIZONS.has(horizon)) throw new Error('Invalid cohort or scoring configuration');
  const ids = new Set();
  for (const row of rows) {
    if (!row || typeof row.id !== 'string' || !row.id.trim() || ids.has(row.id) ||
        row.horizon !== horizon || ![row.actual, row.point, row.baselinePoint,
          row.lower, row.upper].every(finite) || row.actual <= 0 ||
        row.point <= 0 || row.baselinePoint <= 0 || row.lower < 0 || row.upper < row.lower) {
      throw new Error('Invalid, duplicate, or mismatched prospective row');
    }
    ids.add(row.id);
  }
  const hits = rows.filter(r => r.actual >= r.lower && r.actual <= r.upper).length;
  const below = rows.filter(r => r.actual < r.lower).length;
  const above = rows.filter(r => r.actual > r.upper).length;
  const modelMae = avg(rows.map(r => Math.abs(r.point - r.actual)));
  const baselineMae = avg(rows.map(r => Math.abs(r.baselinePoint - r.actual)));
  return {
    horizon, n: rows.length, nominalCoveragePct: 100 * (1 - alpha),
    coveragePct: 100 * hits / rows.length, below, above,
    meanWidthUsd: avg(rows.map(r => r.upper - r.lower)),
    meanWidthPctOfActual: 100 * avg(rows.map(r => (r.upper - r.lower) / r.actual)),
    meanIntervalScoreUsd: avg(rows.map(r => intervalScore(r.actual, r.lower, r.upper, alpha))),
    modelMaeUsd: modelMae, baselineMaeUsd: baselineMae,
    pairedMaeDifferenceUsd: modelMae - baselineMae,
    pointSkillPct: baselineMae === 0 ? null : 100 * (1 - modelMae / baselineMae),
    interpretation: 'Descriptive only; overlapping targets and temporal dependence invalidate iid uncertainty assumptions',
    provenance: 'NOT verified by scorer; caller must independently authenticate receipt, anchor, timestamps and matching provider close'
  };
}

/** Refuse to pool distinct horizons: they answer different questions. */
export function scoreByHorizon(rows, { alpha = 0.2 } = {}) {
  if (!Array.isArray(rows) || !rows.length) throw new Error('No prospective rows');
  const ids = new Set();
  for (const row of rows) {
    if (!row || typeof row.id !== 'string' || ids.has(row.id) || !HORIZONS.has(row.horizon))
      throw new Error('Duplicate receipt or unsupported horizon');
    ids.add(row.id);
  }
  return [1, 7, 30].filter(h => rows.some(r => r.horizon === h))
    .map(h => scoreCohort(rows.filter(r => r.horizon === h), { alpha, horizon: h }));
}
