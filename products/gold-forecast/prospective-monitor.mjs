/**
 * Descriptive, prospective model-vs-persistence monitoring.
 * Only accepts matured, uniquely identified settlements from ONE horizon.
 * No independence, statistical significance, or automatic trading claim.
 */
const isDate = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
  !Number.isNaN(Date.parse(value)) && new Date(value + 'T00:00:00Z').toISOString().slice(0,10) === value;
const finiteNonnegative = value => typeof value === 'number' && Number.isFinite(value) && value >= 0;

export function monitorProspective(outcomes, horizon, options = {}) {
  const {minMatured = 12, window = 12, degradeRatio = 1.10, maxWinRate = 0.40} = options;
  if (![1, 7, 30].includes(horizon)) throw new RangeError('Unsupported horizon');
  if (!Array.isArray(outcomes)) throw new TypeError('Outcomes must be an array');
  if (!Number.isInteger(minMatured) || minMatured < 2 || !Number.isInteger(window) || window < minMatured ||
      !(degradeRatio > 1) || !Number.isFinite(degradeRatio) ||
      !Number.isFinite(maxWinRate) || maxWinRate < 0 || maxWinRate > 1) {
    throw new RangeError('Invalid monitoring policy');
  }
  const seenIds = new Set(), seenTargets = new Set();
  const rows = [];
  let pending = 0, quarantined = 0, unattributedQuarantines = 0;
  for (const row of outcomes) {
    if (!row || typeof row !== 'object' || typeof row.id !== 'string' || !row.id.trim())
      throw new TypeError('Every outcome needs a nonempty receipt id');
    if (seenIds.has(row.id)) throw new Error('Duplicate receipt id');
    seenIds.add(row.id);
    // Existing settlement CLI omits horizon on quarantined errors.
    if (row.status === 'quarantined' && row.horizon === undefined) {
      unattributedQuarantines++; continue;
    }
    if (row.horizon !== horizon) continue; // never pool horizons
    if (row.status === 'pending') { pending++; continue; }
    if (row.status === 'quarantined') { quarantined++; continue; }
    if (row.status !== 'matured') throw new Error('Unknown settlement status');
    if (!isDate(row.targetDate) || !finiteNonnegative(row.modelAbsError) ||
        !finiteNonnegative(row.baselineAbsError) || typeof row.covered !== 'boolean')
      throw new Error('Invalid matured settlement');
    if (seenTargets.has(row.targetDate)) throw new Error('Duplicate target date: requires a frozen sampling policy');
    seenTargets.add(row.targetDate);
    rows.push(row);
  }
  rows.sort((a,b)=>a.targetDate.localeCompare(b.targetDate));
  const recent = rows.slice(-window);
  const n = recent.length;
  const sum = key => recent.reduce((total, r) => total + r[key], 0);
  const modelMae = n ? sum('modelAbsError') / n : null;
  const baselineMae = n ? sum('baselineAbsError') / n : null;
  const ratio = baselineMae > 0 ? modelMae / baselineMae : null;
  const winRate = n ? recent.filter(r => r.modelAbsError < r.baselineAbsError).length / n : null;
  const coverage = n ? recent.filter(r => r.covered).length / n : null;
  const enough = n >= minMatured;
  const degraded = enough && ((ratio !== null && ratio >= degradeRatio && winRate <= maxWinRate) ||
    (baselineMae === 0 && modelMae > 0));
  return {
    horizon, status: !enough ? 'insufficient_prospective_outcomes' : degraded ? 'descriptive_degradation_flag' : 'no_degradation_flag',
    totalMatured: rows.length, evaluated: n, pending, quarantined, unattributedQuarantines,
    from: n ? recent[0].targetDate : null, to: n ? recent.at(-1).targetDate : null,
    modelMae, baselineMae, maeRatio: ratio, winRate, intervalCoverage: coverage,
    policy: {minMatured, window, degradeRatio, maxWinRate},
    caution: 'Descriptive alert only. Settlements and Git issuance anchors require separate verification; overlapping windows and market regimes invalidate naive independence assumptions. Never automatically switch models or claim trading skill.'
  };
}
