/**
 * Observed-volatility regime diagnostic, not a prediction or confidence interval.
 * Compares disjoint recent and earlier log-return windows using only known closes.
 * A future shock cannot be detected before it appears in the observations.
 */
export function assessVolatilityRegime(prices, {
  recentCloses = 20,
  referenceCloses = 80,
  elevatedRatio = 2.5,
  minReferenceStd = 1e-6,
} = {}) {
  if (!Number.isInteger(recentCloses) || recentCloses < 5 ||
      !Number.isInteger(referenceCloses) || referenceCloses < 20 ||
      !Number.isFinite(elevatedRatio) || elevatedRatio <= 1 ||
      !Number.isFinite(minReferenceStd) || minReferenceStd < 0) {
    throw new Error('Invalid volatility diagnostic settings');
  }
  if (!Array.isArray(prices) || prices.length < recentCloses + referenceCloses + 1) {
    throw new Error('Not enough historical closes for disjoint volatility windows');
  }
  if (prices.some(p => typeof p !== 'number' || !Number.isFinite(p) || p <= 0)) {
    throw new Error('Volatility diagnostic requires finite positive closes');
  }
  const tail = prices.slice(-(recentCloses + referenceCloses + 1));
  const returns = tail.slice(1).map((p, i) => Math.log(p / tail[i]));
  const reference = returns.slice(0, referenceCloses);
  const recent = returns.slice(referenceCloses);
  const sampleStd = xs => {
    const mean = xs.reduce((a, b) => a + b, 0) / xs.length;
    return Math.sqrt(xs.reduce((a, x) => a + (x - mean) ** 2, 0) / (xs.length - 1));
  };
  const referenceStd = sampleStd(reference);
  const recentStd = sampleStd(recent);
  const insufficient = referenceStd <= minReferenceStd;
  const ratio = insufficient ? null : recentStd / referenceStd;
  return {
    status: insufficient ? 'insufficient_reference_variation' : ratio >= elevatedRatio ? 'elevated_observed' : 'not_elevated_observed',
    ratio,
    referenceStdPct: 100 * referenceStd,
    recentStdPct: 100 * recentStd,
    referenceCloses,
    recentCloses,
    elevatedRatio,
    limitation: 'Only detects shifts already observed in closes. It cannot anticipate a future volatility shock or guarantee interval coverage.',
  };
}
