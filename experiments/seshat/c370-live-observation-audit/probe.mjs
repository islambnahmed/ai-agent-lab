/** Read-only live source probe. Never settles a receipt or writes provider data. */
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {prepareProviderHistory} from '../../../products/gold-forecast/data.mjs';
import {verifyReceipt} from '../../../products/gold-forecast/journal.mjs';

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export function auditPayload(receipt,payload,asOf,{rawSha256=null}={}){
  verifyReceipt(receipt);
  if(receipt.horizon!==7 || receipt.calendar!=='observations' || receipt.targetDate!==null)
    throw Error('Only pinned 7-observation receipt supported');
  const prepared=prepareProviderHistory(payload,asOf);
  const series=prepared.series;
  const originIndex=series.findIndex(row=>row.date===receipt.originDate);
  const base={status:'inconclusive',receiptId:receipt.id,asOf,source:receipt.source,
    sourceUrl:receipt.sourceManifest.url,attribution:payload.attribution,
    rawSha256,originDate:receipt.originDate,originClosePinned:receipt.originClose,
    historyHashPinned:receipt.historyHash,providerLatestDate:prepared.latestDate,
    observationCount:series.length,calendar:prepared.calendar,
    caveat:'Current mutable provider feed; NOT a verified original vintage or independent publication-time proof.'};
  if(originIndex<0)return {...base,reason:'origin_not_in_current_window'};
  const origin=series[originIndex];
  const targetIndex=originIndex+receipt.horizon;
  if(origin.price!==receipt.originClose)return {...base,reason:'origin_close_mismatch',originCloseNow:origin.price};
  if(targetIndex>=series.length)return {...base,status:'pending',reason:'insufficient_future_observations',
    futureObservationCount:series.length-originIndex-1};
  const target=series[targetIndex];
  if(target.date>=new Date(asOf).toISOString().slice(0,10))return {...base,status:'pending',reason:'target_utc_day_incomplete',targetDate:target.date};
  const modelAbsError=Math.abs(receipt.point-target.price);
  const baselineAbsError=Math.abs(receipt.baseline-target.price);
  return {...base,status:'tentative_current_vintage',originCloseNow:origin.price,
    futureObservationCount:series.length-originIndex-1,targetDate:target.date,
    targetCloseNow:target.price,modelAbsError,baselineAbsError,
    winner:modelAbsError<baselineAbsError?'model':modelAbsError>baselineAbsError?'baseline':'tie',
    observationIndexAfterOrigin:receipt.horizon};
}

async function main(){
  const dir=dirname(fileURLToPath(import.meta.url));
  const receipt=JSON.parse(await readFile(resolve(dir,'../../../products/gold-forecast/reports/prospective/2026-10-11-h7.json'),'utf8'));
  const url=receipt.sourceManifest.url;
  if(new URL(url).origin!=='https://standardbullion.com')throw Error('Unexpected source origin');
  const res=await fetch(url,{signal:AbortSignal.timeout(30000),headers:{'Accept':'application/json'}});
  if(!res.ok)throw Error('Provider HTTP '+res.status);
  const bytes=Buffer.from(await res.arrayBuffer());
  if(bytes.length===0||bytes.length>5_000_000)throw Error('Empty or oversized source response');
  const receivedAt=new Date().toISOString();
  const payload=JSON.parse(bytes.toString('utf8'));
  const result=auditPayload(receipt,payload,receivedAt,{rawSha256:sha256(bytes)});
  console.log(JSON.stringify({...result,receivedAt},null,2));
  if(result.status==='inconclusive')process.exitCode=2;
}
if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  main().catch(e=>{console.error('SOURCE_PROBE_FAILED:',e.message);process.exitCode=2;});
}
