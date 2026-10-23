/**
 * C369: receipt-only algebraic forecast-vs-persistence comparison.
 * No historical price is fetched, inferred, or fabricated.
 * A decision boundary is NOT a realized outcome or a skill estimate.
 */
export function receiptBoundary(receipt) {
  if (!receipt || ![1,7,30].includes(receipt.horizon) ||
      !Number.isFinite(receipt.point) || receipt.point <= 0 ||
      !Number.isFinite(receipt.baseline) || receipt.baseline <= 0 ||
      typeof receipt.originDate !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}$/.test(receipt.originDate) ||
      new Date(receipt.originDate + 'T00:00:00Z').toISOString().slice(0,10) !== receipt.originDate ||
      receipt.calendar !== 'observations' || receipt.targetDate !== null) {
    throw new Error('Expected valid positive receipt with irregular observed-close horizon');
  }
  const originMs = Date.parse(receipt.originDate + 'T00:00:00Z');
  const earliest = new Date(originMs + receipt.horizon * 86400000).toISOString().slice(0,10);
  const delta = receipt.point - receipt.baseline;
  if (delta === 0) {
    return {horizon:receipt.horizon, earliestPossibleTargetDate:earliest,
      actualTargetDate:'unknown', classification:'identical_to_persistence',
      threshold:null, modelBetterWhen:'never', baselineBetterWhen:'never',
      tieWhen:'all positive actual prices'};
  }
  const threshold = (receipt.point + receipt.baseline) / 2;
  return {horizon:receipt.horizon, earliestPossibleTargetDate:earliest,
    actualTargetDate:'unknown', classification:'conditional', threshold,
    modelBetterWhen:delta > 0 ? 'actual > threshold' : '0 < actual < threshold',
    baselineBetterWhen:delta > 0 ? '0 < actual < threshold' : 'actual > threshold',
    tieWhen:'actual = threshold'};
}

/** Positive-price-only exact comparator; intended as a test oracle. */
export function compareAtActual(receipt, actual) {
  if (!Number.isFinite(actual) || actual <= 0) throw new Error('Actual must be positive');
  const boundary=receiptBoundary(receipt);
  const modelError=Math.abs(receipt.point-actual);
  const baselineError=Math.abs(receipt.baseline-actual);
  const eps=1e-9*Math.max(1,modelError,baselineError);
  return {boundary,modelError,baselineError,
    winner:Math.abs(modelError-baselineError)<=eps?'tie':modelError<baselineError?'model':'baseline'};
}
