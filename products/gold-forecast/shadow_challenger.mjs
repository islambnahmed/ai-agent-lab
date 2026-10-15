// Worker A prospective shadow challenger v1. Research-only; no trade signal.
// Frozen ex-ante formula. No model selection or audit-based tuning.
import {createHash} from 'node:crypto';

export const SHADOW_VERSION = 'worker-a-shadow-trend-v1';
export const HORIZONS = Object.freeze([1, 7, 30]);
const DAY_MS = 86400000;
const sha = x => createHash('sha256').update(JSON.stringify(x)).digest('hex');
const isoDay = d => /^\d{4}-\d{2}-\d{2}$/.test(d) && !Number.isNaN(Date.parse(d+'T00:00:00Z')) &&
  new Date(d+'T00:00:00Z').toISOString().slice(0,10) === d;

function validateHistory(series, minRows=42) {
  if (!Array.isArray(series) || series.length < minRows) throw Error('Insufficient observed closes');
  let previous = '';
  for (const row of series) {
    if (!row || !isoDay(row.date) || row.date <= previous ||
        typeof row.price !== 'number' || !Number.isFinite(row.price) || row.price <= 0)
      throw Error('Invalid or unordered observed closes');
    previous = row.date;
  }
}
function validAsOf(asOf) {
  if (typeof asOf !== 'string' || !/^\d{4}-\d{2}-\d{2}T/.test(asOf) ||
      !/(Z|[+-]\d{2}:\d{2})$/.test(asOf) || !Number.isFinite(Date.parse(asOf)))
    throw Error('asOf must be an explicit offset-aware ISO timestamp');
  return Date.parse(asOf);
}
function validSource(source) {
  if (typeof source !== 'string' || !source.trim() || source.length > 160)
    throw Error('A named observed-close source is required');
}

// The entire history must be visible at issue time. Returns one non-adaptive
// challenger against persistence; its 20-return drift is capped at 0.5% per
// observation and scaled by sqrt(h) rather than h to limit extrapolation.
export function issueShadow(series, horizon, {asOf, source}={}) {
  validateHistory(series);
  validSource(source);
  if (!HORIZONS.includes(horizon)) throw Error('Unsupported horizon');
  const now = validAsOf(asOf);
  const origin = series.at(-1);
  const ageDays = (now - Date.parse(origin.date+'T00:00:00Z')) / DAY_MS;
  if (ageDays < 0 || ageDays > 8) throw Error('Stale or future-dated observed close');
  const prices = series.slice(-21).map(r => r.price);
  const drift = prices.slice(1).reduce((sum,p,i)=>sum+Math.log(p/prices[i]),0)/20;
  const boundedDrift = Math.max(-0.005,Math.min(0.005,drift));
  const point = origin.price*Math.exp(0.5*boundedDrift*Math.sqrt(horizon));
  const record = {schemaVersion:1,version:SHADOW_VERSION,source,horizon,
    horizonUnit:'future observed provider closes',issuedAt:asOf,
    originDate:origin.date,originClose:origin.price,historyLength:series.length,
    historySha256:sha(series),baseline:origin.price,point};
  return {...record,receiptSha256:sha(record)};
}

// Never match a target by calendar arithmetic: observed-close horizons are
// ordinal. A revised historical prefix invalidates the receipt settlement.
export function settleShadow(receipt, series, {source}={}) {
  if (!receipt || receipt.version !== SHADOW_VERSION || receipt.schemaVersion !== 1 ||
      !HORIZONS.includes(receipt.horizon) || !Number.isInteger(receipt.historyLength) ||
      receipt.historyLength < 42) throw Error('Unsupported shadow receipt');
  validSource(source);
  if (receipt.source !== source) throw Error('Source mismatch');
  const {receiptSha256,...unsigned} = receipt;
  if (receiptSha256 !== sha(unsigned)) throw Error('Modified shadow receipt');
  validateHistory(series,receipt.historyLength);
  const prefix = series.slice(0,receipt.historyLength);
  if (sha(prefix) !== receipt.historySha256 || prefix.at(-1).date !== receipt.originDate)
    throw Error('Historical prefix changed');
  const targetIndex = receipt.historyLength + receipt.horizon - 1;
  if (series.length <= targetIndex) return {status:'pending',observedSinceOrigin:series.length-receipt.historyLength,
    required:receipt.horizon};
  const actual = series[targetIndex];
  const baselineError = Math.abs(receipt.baseline-actual.price);
  const challengerError = Math.abs(receipt.point-actual.price);
  const predictedDirection = Math.sign(receipt.point-receipt.originClose);
  return {status:'matured',targetDate:actual.date,actual:actual.price,
    baselineAbsoluteError:baselineError,challengerAbsoluteError:challengerError,
    improvementUsd:baselineError-challengerError,
    directionCorrect:predictedDirection===0?null:predictedDirection===Math.sign(actual.price-receipt.originClose),
    interpretation:'One matured prospective observation; no statistical skill claim'};
}
