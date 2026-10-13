/**
 * Directional forecast audit with explicit abstention semantics.
 * A forecast equal to the origin price is a NO-DIRECTION forecast, not a wrong bet.
 * Conditional hit rate must always be read alongside participation/coverage.
 * All prices must be positive finite numbers; no model selection happens here.
 */
export function directionalAudit(rows, {epsilon = 0} = {}) {
  if (!Array.isArray(rows) || rows.length === 0) throw new Error('Nonempty rows required');
  if (!Number.isFinite(epsilon) || epsilon < 0 || epsilon >= 1) throw new Error('Invalid epsilon');
  const classes = [-1, 0, 1];
  const confusion = Object.fromEntries(classes.map(p => [String(p), Object.fromEntries(classes.map(a => [String(a), 0]))]));
  let committed = 0, hits = 0, exact = 0, absError = 0;
  let actualUp = 0, actualDown = 0, actualFlat = 0;
  for (const row of rows) {
    const {originClose, point, actual} = row ?? {};
    if (![originClose, point, actual].every(x => typeof x === 'number' && Number.isFinite(x) && x > 0)) {
      throw new Error('Invalid price triple');
    }
    const direction = x => x > originClose * (1 + epsilon) ? 1 : x < originClose * (1 - epsilon) ? -1 : 0;
    const predicted = direction(point), realized = direction(actual);
    confusion[String(predicted)][String(realized)]++;
    if (realized === 1) actualUp++; else if (realized === -1) actualDown++; else actualFlat++;
    if (predicted !== 0) { committed++; if (predicted === realized) hits++; }
    if (predicted === realized) exact++;
    absError += Math.abs(point - actual);
  }
  const n = rows.length;
  return {
    n, epsilon, mae: absError / n,
    participationPct: 100 * committed / n,
    conditionalHitPct: committed ? 100 * hits / committed : null,
    threeClassExactPct: 100 * exact / n,
    committed, abstained: n - committed, hits,
    actual: {up: actualUp, down: actualDown, flat: actualFlat},
    confusion
  };
}

/** Same origins and outcomes, evaluated without any hindsight selection. */
export function auditComparators(rows, {epsilon = 0} = {}) {
  const base = rows.map(r => ({...r, point: r.originClose}));
  return {
    candidate: directionalAudit(rows, {epsilon}),
    persistence: directionalAudit(base, {epsilon})
  };
}
