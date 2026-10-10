/**
 * Worker A — independent UTC-day-block robustness screen for paired XAU/USD
 * forecast comparisons. This is an exploratory diagnostic, not proof of
 * independence, pre-registration, provider truth, or trading performance.
 * All timestamps and capture claims are untrusted input.
 */
import {parseProviderUtcTimestamp} from './quote-core.mjs';
import {exactSignTail} from './paired-evidence.mjs';

const requireThat = (ok, message) => { if (!ok) throw new Error(message); };
const validPrice = (value, field) => {
  requireThat(typeof value === 'number' && Number.isFinite(value) && value > 0 && value <= 1_000_000,
    `${field}: invalid price`);
  return value;
};
const mean = (xs) => xs.reduce((sum, x) => sum + x, 0) / xs.length;

/**
 * Collapses non-overlapping forecasts into UTC-day blocks BEFORE counting
 * wins/losses. A single lucky regime of 100 hourly wins on four days cannot
 * masquerade as 100 independent directional wins.
 *
 * Selection depends on times only (not prices or wins), avoiding outcome-
 * driven choice of rows. Day blocks may still be serially dependent.
 */
export function dailyBlockEvidence(forecasts, {
  minSelected = 30, minDays = 20, minDecisiveDays = 15,
  minRelativeMaeImprovement = 0.01, alpha = 0.05,
} = {}) {
  requireThat(Array.isArray(forecasts), 'forecasts must be an array');
  requireThat(Number.isSafeInteger(minSelected) && minSelected >= 1, 'invalid minSelected');
  requireThat(Number.isSafeInteger(minDays) && minDays >= 1, 'invalid minDays');
  requireThat(Number.isSafeInteger(minDecisiveDays) && minDecisiveDays >= 1, 'invalid minDecisiveDays');
  requireThat(typeof minRelativeMaeImprovement === 'number' && Number.isFinite(minRelativeMaeImprovement) &&
    minRelativeMaeImprovement >= 0 && minRelativeMaeImprovement < 1, 'invalid minRelativeMaeImprovement');
  requireThat(typeof alpha === 'number' && Number.isFinite(alpha) && alpha > 0 && alpha < 1, 'invalid alpha');

  const rows = forecasts.map((row, index) => {
    requireThat(row && typeof row === 'object' && !Array.isArray(row), `row ${index}: invalid object`);
    const issued = parseProviderUtcTimestamp(row.issuedAt);
    const target = parseProviderUtcTimestamp(row.targetAt);
    const captured = parseProviderUtcTimestamp(row.targetCapturedAt);
    requireThat(issued < target && target <= captured, `row ${index}: invalid timeline`);
    const actual = validPrice(row.actual, 'actual');
    const persistence = validPrice(row.persistence, 'persistence');
    const drift = validPrice(row.drift, 'drift');
    return {issued, target, pError:Math.abs(actual-persistence), dError:Math.abs(actual-drift)};
  });
  rows.sort((a,b)=>a.target-b.target || a.issued-b.issued);
  const pairs = new Set();
  for (const row of rows) {
    const key = `${row.issued}/${row.target}`;
    requireThat(!pairs.has(key), 'duplicate issue/target pair');
    pairs.add(key);
  }

  const selected = [];
  let previousTarget = -Infinity;
  for (const row of rows) {
    if (row.issued >= previousTarget) {
      selected.push(row);
      previousTarget = row.target;
    }
  }

  const blocks = new Map();
  for (const row of selected) {
    const day = new Date(row.target).toISOString().slice(0,10);
    if (!blocks.has(day)) blocks.set(day, {count:0, pLoss:0, dLoss:0});
    const b = blocks.get(day);
    b.count++;
    b.pLoss += row.pError;
    b.dLoss += row.dError;
  }

  let dayWins=0, dayLosses=0, dayTies=0;
  for (const b of blocks.values()) {
    // Compare daily MEAN losses to avoid giving busy days greater vote weight.
    const delta = b.pLoss / b.count - b.dLoss / b.count;
    if (delta > 0) dayWins++;
    else if (delta < 0) dayLosses++;
    else dayTies++;
  }
  const decisiveDays = dayWins + dayLosses;
  const pMae = selected.length ? mean(selected.map(r=>r.pError)) : null;
  const dMae = selected.length ? mean(selected.map(r=>r.dError)) : null;
  const relativeMaeImprovement = pMae === null || pMae === 0 ? null : (pMae-dMae)/pMae;
  const p = decisiveDays ? exactSignTail(dayWins, decisiveDays) : null;
  const sufficient = selected.length >= minSelected && blocks.size >= minDays && decisiveDays >= minDecisiveDays;
  const flag = !sufficient ? 'insufficient_temporal_coverage' :
    (relativeMaeImprovement !== null && relativeMaeImprovement >= minRelativeMaeImprovement &&
      dMae < pMae && p <= alpha ? 'candidate_block_robust_advantage' : 'no_demonstrated_block_advantage');

  return Object.freeze({
    allCount:rows.length, selectedCount:selected.length, droppedOverlaps:rows.length-selected.length,
    utcDays:blocks.size, dayWins, dayLosses, dayTies, decisiveDays,
    persistenceMAE:pMae, driftMAE:dMae, relativeMaeImprovement,
    oneSidedDaySignP:p, alpha, minSelected, minDays, minDecisiveDays,
    minRelativeMaeImprovement, flag,
    caveat:'Exploratory robustness screen only. UTC-day blocks may remain serially dependent; no independently anchored timestamps, prospective registration, real-market validation, multiple-testing correction, or trading claim.'
  });
}
