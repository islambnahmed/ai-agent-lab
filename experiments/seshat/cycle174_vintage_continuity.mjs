/**
 * Seshat 174: evidence-only commitment for provider rolling histories.
 * This module never settles forecasts and never claims source authenticity.
 * Commit the commitment file to Git before the outcome is known.
 */
import {createHash} from 'node:crypto';
const digest = x => createHash('sha256').update(JSON.stringify(x)).digest('hex');
const DAY = /^\d{4}-\d{2}-\d{2}$/;
function dateValid(d) {
  return typeof d === 'string' && DAY.test(d) &&
    Number.isFinite(Date.parse(d+'T00:00:00Z')) &&
    new Date(Date.parse(d+'T00:00:00Z')).toISOString().slice(0,10) === d;
}
function validateRows(rows) {
  if (!Array.isArray(rows) || !rows.length || rows.length > 10000) throw Error('Expected nonempty bounded rows');
  let previous='';
  for (const row of rows) {
    if (!row || !dateValid(row.date) || typeof row.price !== 'number' || !Number.isFinite(row.price) || row.price <= 0)
      throw Error('Invalid date or price');
    if (row.date <= previous) throw Error('Rows must be sorted with unique dates');
    previous = row.date;
  }
}
function validateReceipt(receipt) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) throw Error('Missing receipt');
  const {id,...payload}=receipt;
  if (typeof id !== 'string' || digest(payload) !== id ||
      !/^[0-9a-f]{64}$/.test(receipt.historyHash) ||
      !Number.isInteger(receipt.historyLength) || receipt.historyLength < 1)
    throw Error('Receipt integrity failed');
}
export function makeContinuityCommitment(receipt, originalSeries) {
  validateReceipt(receipt); validateRows(originalSeries);
  if (originalSeries.length !== receipt.historyLength || digest(originalSeries) !== receipt.historyHash)
    throw Error('Original series does not match anchored receipt');
  if (originalSeries.at(-1).date !== receipt.originDate || originalSeries.at(-1).price !== receipt.originClose)
    throw Error('Origin does not match receipt');
  const leaves=originalSeries.map(({date,price})=>({date,sha256:digest([date,price])}));
  const body={schemaVersion:1,receiptId:receipt.id,historyHash:receipt.historyHash,
    rowCount:originalSeries.length,firstDate:originalSeries[0].date,lastDate:originalSeries.at(-1).date,
    leaves};
  return {...body,root:digest(body)};
}
export function auditContinuity(receipt, currentSeries, commitment, {minOverlap=5}={}) {
  validateReceipt(receipt);validateRows(currentSeries);
  if (!Number.isInteger(minOverlap) || minOverlap < 1) throw Error('Invalid overlap threshold');
  if (!commitment) return {status:'unverifiable_without_original_vintage',overlap:0,
    reason:'A receipt historyHash is not a substitute for the original 324-row series or precommitted row digests'};
  if (!commitment || typeof commitment !== 'object' || Array.isArray(commitment)) throw Error('Invalid commitment');
  const {root,...body}=commitment;
  if (digest(body) !== root || commitment.schemaVersion !== 1 ||
      commitment.receiptId !== receipt.id || commitment.historyHash !== receipt.historyHash ||
      commitment.rowCount !== receipt.historyLength ||
      !Array.isArray(commitment.leaves) || commitment.leaves.length !== receipt.historyLength)
    throw Error('Commitment integrity mismatch');
  let previous='';
  for (const leaf of commitment.leaves) {
    if (!dateValid(leaf?.date) || leaf.date <= previous || !/^[0-9a-f]{64}$/.test(leaf.sha256))
      throw Error('Invalid commitment leaf');
    previous=leaf.date;
  }
  if (commitment.firstDate !== commitment.leaves[0].date ||
      commitment.lastDate !== commitment.leaves.at(-1).date ||
      commitment.lastDate !== receipt.originDate) throw Error('Commitment origin mismatch');
  const known=new Map(commitment.leaves.map(x=>[x.date,x.sha256]));
  let overlap=0, revisions=[];
  for (const row of currentSeries) {
    if (!known.has(row.date)) continue;
    overlap++;
    if (known.get(row.date)!==digest([row.date,row.price])) revisions.push(row.date);
  }
  const missing=commitment.rowCount-overlap;
  if (revisions.length) return {status:'quarantined_revision',overlap,missing,revisions};
  if (overlap < minOverlap) return {status:'insufficient_overlap',overlap,missing,
    reason:'Too little shared evidence to establish continuity'};
  return {status:missing===0?'full_row_match':'partial_row_match',overlap,missing,
    caveat:'Matches a precommitted digest only; not proof of source independence, publication time, or forecast skill'};
}
