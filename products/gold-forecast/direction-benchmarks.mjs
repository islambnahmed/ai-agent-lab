import {directionMetrics} from './direction-metrics.mjs';

const rate = (hits, n) => n ? 100 * hits / n : null;

/**
 * Compare directional calls to two fixed, outcome-independent naive rules.
 * Always-up and always-down are both reported: do not choose one using audit outcomes.
 * On-called-subset baselines use EXACTLY the origins on which the model called.
 * This is descriptive, not a prospective edge/significance test.
 */
export function directionBenchmark(rows, {horizon=1, disjoint=false}={}) {
  if (!Number.isInteger(horizon) || horizon < 1 || horizon > 30) throw Error('Invalid horizon');
  // Validate the entire input, even observations later excluded by disjoint sampling.
  directionMetrics(rows);
  if (disjoint) {
    let previous = -1;
    for (const r of rows) {
      if (!Number.isSafeInteger(r.originIndex) || r.originIndex < 0 || r.originIndex <= previous)
        throw Error('Disjoint audit needs strictly increasing, nonnegative originIndex');
      previous = r.originIndex;
    }
  }
  const selected = [];
  let nextAllowed = -1;
  for (const r of rows) {
    if (disjoint && r.originIndex < nextAllowed) continue;
    selected.push(r);
    if (disjoint) nextAllowed = r.originIndex + horizon;
  }
  const model = directionMetrics(selected);
  let up = 0, down = 0, flat = 0, called = 0, modelHits = 0, upCalled = 0, downCalled = 0;
  for (const r of selected) {
    const actual = Math.sign(r.actual - r.originClose);
    const prediction = Math.sign(r.point - r.originClose);
    if (actual > 0) up++;
    else if (actual < 0) down++;
    else flat++;
    if (prediction !== 0) {
      called++;
      if (prediction === actual) modelHits++;
      if (actual > 0) upCalled++;
      if (actual < 0) downCalled++;
    }
  }
  const n = selected.length;
  return {
    n, horizon, sampling: disjoint ? 'nonoverlapping-origin-windows' : 'all-audit-origins',
    outcomeCounts: {up, down, flat},
    model,
    fixedBaselines: {
      alwaysUp: {calls:n, hitRatePct:rate(up,n)},
      alwaysDown: {calls:n, hitRatePct:rate(down,n)}
    },
    matchedCalls: {
      n:called,
      modelHitRatePct:rate(modelHits,called),
      alwaysUpHitRatePct:rate(upCalled,called),
      alwaysDownHitRatePct:rate(downCalled,called),
      deltaVsAlwaysUpPctPoints: called ? rate(modelHits,called)-rate(upCalled,called) : null,
      deltaVsAlwaysDownPctPoints: called ? rate(modelHits,called)-rate(downCalled,called) : null
    },
    caveat: 'Descriptive retrospective audit only. Both fixed baselines are reported without hindsight selection. Flat outcomes are misses for directional calls. Nonoverlapping target windows need not be statistically independent. Prospective skill remains unproven.'
  };
}
