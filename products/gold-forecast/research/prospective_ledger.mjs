/** Prospective, session-indexed forecast receipts; no network, accounts, or secrets.
 * Hashes detect accidental changes but DO NOT prove when a forecast was issued.
 * Anchor the receipt in an externally timestamped Git commit before outcomes exist.
 */
import {createHash} from 'node:crypto';
import {predict, MODEL_NAMES} from '../forecast.mjs';

const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const dateRE = /^\d{4}-\d{2}-\d{2}$/;
function dateNumber(day) {
  if (typeof day !== 'string' || !dateRE.test(day)) throw Error('Invalid ISO date');
  const d = new Date(day+'T12:00:00Z');
  if (!Number.isFinite(d.valueOf()) || d.toISOString().slice(0,10) !== day) throw Error('Invalid calendar date');
  return d.valueOf();
}
export function validateSeries(series) {
  if (!Array.isArray(series) || series.length < 1) throw Error('Empty series');
  let last = -Infinity;
  return series.map(row => {
    if (!row || typeof row !== 'object' || Array.isArray(row)) throw Error('Invalid row');
    const date = row.date, ts = dateNumber(date), price = row.price;
    if (ts <= last) throw Error('Dates must be strictly increasing; no duplicates');
    if (typeof price !== 'number' || !Number.isFinite(price) || price <= 0) throw Error('Invalid price');
    last = ts;
    return {date, price};
  });
}
function parseIssuedAt(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(value)) throw Error('issuedAt must be UTC ISO timestamp');
  const ts = Date.parse(value);
  if (!Number.isFinite(ts) || new Date(ts).toISOString().slice(0,10) !== value.slice(0,10)) throw Error('Invalid issue time');
  return ts;
}
function payload(receipt) {
  const {version,issuedAt,source,horizon,model,modelRevision,originDate,originClose,historyLength,historyHash,point,baseline} = receipt;
  return {version,issuedAt,source,horizon,model,modelRevision,originDate,originClose,historyLength,historyHash,point,baseline};
}
export function issue({series,horizon,model,modelRevision,issuedAt,source}) {
  const rows=validateSeries(series);
  if (rows.length < 42) throw Error('Need at least 42 observed sessions');
  if (![1,7,30].includes(horizon)) throw Error('Unsupported horizon');
  if (!Object.hasOwn(MODEL_NAMES,model)) throw Error('Unknown model');
  if (typeof modelRevision !== 'string' || !/^[0-9a-f]{40}$/.test(modelRevision)) throw Error('Pinned 40-hex model blob revision required');
  if (typeof source !== 'string' || !/^[a-zA-Z0-9._:-]{1,120}$/.test(source)) throw Error('Source ID required');
  const ts=parseIssuedAt(issuedAt), origin=rows.at(-1);
  // Date-only daily closes have no trustworthy publication timestamp.
  // Require the next UTC calendar day; provider publication must still be verified.
  if (origin.date >= issuedAt.slice(0,10)) throw Error('Daily close must predate issue UTC day (no same-day lookahead)');
  const prices=rows.map(r=>r.price);
  const record={version:1,issuedAt,source,horizon,model,modelRevision,originDate:origin.date,
    originClose:origin.price,historyLength:rows.length,historyHash:hash(rows),
    point:predict(prices,horizon,model),baseline:predict(prices,horizon,'persistence')};
  return {...record,id:hash(record)};
}
export function verifyReceipt(receipt) {
  if (!receipt || typeof receipt!=='object' || Array.isArray(receipt)) throw Error('Invalid receipt');
  if (receipt.version!==1 || receipt.id!==hash(payload(receipt))) throw Error('Receipt integrity mismatch');
  if (!Number.isInteger(receipt.historyLength) || receipt.historyLength<42 || ![1,7,30].includes(receipt.horizon)) throw Error('Invalid receipt metadata');
  if (!Object.hasOwn(MODEL_NAMES,receipt.model)) throw Error('Unknown receipt model');
  parseIssuedAt(receipt.issuedAt); dateNumber(receipt.originDate);
  if (receipt.originDate >= receipt.issuedAt.slice(0,10)) throw Error('Receipt origin must predate issue UTC day');
  if (typeof receipt.modelRevision!=='string' || !/^[0-9a-f]{40}$/.test(receipt.modelRevision)) throw Error('Invalid model revision');
  if (!Number.isFinite(receipt.point) || receipt.point<=0 || !Number.isFinite(receipt.baseline) || receipt.baseline<=0) throw Error('Invalid receipt prediction');
  return true;
}
export function settle(receipt,observedSeries) {
  verifyReceipt(receipt);
  const rows=validateSeries(observedSeries);
  if (rows.length<receipt.historyLength) throw Error('Original history missing');
  // Receipts can use a rolling history window. Locate its dated origin in the
  // supplied full market series instead of assuming the window begins at row 0.
  // Strict date ordering (validateSeries) makes the origin unambiguous.
  const originIndex=rows.findIndex(row=>row.date===receipt.originDate);
  if (originIndex<0 || originIndex+1<receipt.historyLength)
    throw Error('Original history missing or origin date absent');
  const prefix=rows.slice(originIndex+1-receipt.historyLength,originIndex+1);
  if (hash(prefix)!==receipt.historyHash) throw Error('Historical vintage changed: cannot silently settle');
  const available=rows.length-originIndex-1;
  // Conservative chronology gate: a receipt dated on/after the first future
  // session is not prospective. A Git commit anchor is still required to prove it.
  if (available>0 && receipt.issuedAt.slice(0,10)>=rows[originIndex+1].date)
    throw Error('Receipt issued after first subsequent session');
  if (available<receipt.horizon) return {id:receipt.id,status:'pending',remainingSessions:receipt.horizon-available};
  const target=rows[originIndex+receipt.horizon];
  const modelAbsError=Math.abs(receipt.point-target.price), baselineAbsError=Math.abs(receipt.baseline-target.price);
  return {id:receipt.id,status:'matured',targetDate:target.date,actual:target.price,
    modelAbsError,baselineAbsError,absoluteErrorImprovement:baselineAbsError-modelAbsError};
}
export function summarize(settlements) {
  if (!Array.isArray(settlements)) throw Error('Invalid settlements');
  const matured=settlements.filter(r=>r?.status==='matured');
  const pending=settlements.filter(r=>r?.status==='pending').length;
  if (matured.length===0) return {matured:0,pending,maeModel:null,maeBaseline:null,relativeGain:null,
    caveat:'Descriptive only; overlapping outcomes and multiple-horizon selection require separate inference.'};
  const mean = key => matured.reduce((s,r)=>s+r[key],0)/matured.length;
  const maeModel=mean('modelAbsError'),maeBaseline=mean('baselineAbsError');
  return {matured:matured.length,pending,maeModel,maeBaseline,
    relativeGain:maeBaseline>0?(maeBaseline-maeModel)/maeBaseline:null,
    caveat:'Descriptive only; overlapping outcomes and multiple-horizon selection require separate inference.'};
}
