/**
 * C368 experimental bridge: exact raw snapshot -> prospective settlement ->
 * write-once outcome candidate. No provider authenticity or publication proof.
 * This module never writes or downloads anything.
 */
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
import {prepareProviderHistory} from '../../../products/gold-forecast/data.mjs';
import {hash,settleReceipt,verifyReceipt} from '../../../products/gold-forecast/journal.mjs';
import {makeOutcomeLock} from '../c366-outcome-lock/outcome_lock.mjs';

const MAX_BYTES=5_000_000;
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const digest=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);

/**
 * All inputs are supplied by caller; an `anchorAt` string is not itself a
 * trusted GitHub timestamp. The caller must independently verify that anchor.
 * `originalVintage` is the exact locally retained forecast-time normalized
 * series; without it, rolling feeds cannot prove the original prefix.
 */
export function verifyAndPrepareOutcome({receipt,rawBytes,parsedHistory,manifest,originalVintage,anchorAt,observedAt}){
  verifyReceipt(receipt);
  if(!Buffer.isBuffer(rawBytes)||!rawBytes.length||rawBytes.length>MAX_BYTES)
    throw Error('Missing or oversized exact raw snapshot');
  if(!manifest||manifest.status!=='fetched'||manifest.httpStatus!==200||
     manifest.url!==receipt.sourceManifest?.url||!digest(manifest.rawSha256))
    throw Error('Snapshot manifest does not match receipt source');
  if(sha256(rawBytes)!==manifest.rawSha256)throw Error('Raw snapshot SHA-256 mismatch');
  let original;
  try{original=JSON.parse(rawBytes.toString('utf8'));}
  catch{throw Error('Raw snapshot is not valid JSON');}
  if(!isDeepStrictEqual(original,parsedHistory))throw Error('Parsed history differs from hashed raw snapshot');
  // This validates source shape, freshness, daily granularity, and excludes
  // provisional current-day closes. It does NOT authenticate the upstream feed.
  const prepared=prepareProviderHistory(original,manifest.receivedAt);
  if(!Array.isArray(originalVintage)||originalVintage.length!==receipt.historyLength||
     hash(originalVintage)!==receipt.historyHash||originalVintage.at(-1)?.date!==receipt.originDate)
    throw Error('Original issue-time vintage unavailable or inconsistent');
  const byDate=new Map(originalVintage.map(row=>[row.date,row.price]));
  if(byDate.size!==originalVintage.length)throw Error('Duplicate original vintage dates');
  if(!prepared.series.some(row=>row.date===receipt.originDate))
    throw Error('Origin absent from refreshed source: cannot audit overlap');
  for(const row of prepared.series){
    if(byDate.has(row.date)&&byDate.get(row.date)!==row.price)
      throw Error('Historical vintage revised: '+row.date);
  }
  const appended=originalVintage.concat(prepared.series.filter(row=>row.date>receipt.originDate));
  const outcome=settleReceipt(receipt,appended,{asOf:manifest.receivedAt});
  if(outcome.status!=='matured')return {status:'pending',outcome};
  // The outcome is computed from the same authenticated-to-local-bytes series
  // whose hash is embedded in the resulting evidence record.
  const lock=makeOutcomeLock(receipt,outcome,{anchorAt,observedAt,manifest});
  return {status:'ready_to_lock',outcome,lock,
    caveat:'Local byte integrity only; caller must independently verify GitHub anchor and provider publication provenance'};
}
