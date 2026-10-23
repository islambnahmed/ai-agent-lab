/** Read-only live diagnostic. No new forecasts, settlement, or vendor payload redistribution. */
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {prepareProviderHistory} from '../../../products/gold-forecast/data.mjs';
import {verifyReceipt} from '../../../products/gold-forecast/journal.mjs';
import {createSuffixCommitment,auditLegacyFullHash} from './rolling_vintage.mjs';
const receiptPath='research/seshat/c374-prospective-receipts-20261023.json';
async function main(){
  const original=JSON.parse(fs.readFileSync(receiptPath,'utf8'));
  const url='https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y';
  const requestedAt=new Date().toISOString();
  const response=await fetch(url,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(30000)});
  if(!response.ok)throw Error('Provider HTTP '+response.status);
  const raw=Buffer.from(await response.arrayBuffer());
  if(!raw.length||raw.length>5_000_000)throw Error('Unexpected provider response size');
  const receivedAt=new Date().toISOString();
  const prepared=prepareProviderHistory(JSON.parse(raw.toString('utf8')),receivedAt);
  const originalReceipts=original.receipts.map(({receipt})=>{
    verifyReceipt(receipt);
    const legacy=auditLegacyFullHash(receipt,prepared.series);
    const originIndex=prepared.series.findIndex(r=>r.date===receipt.originDate);
    return {receiptId:receipt.id,horizon:receipt.horizon,originDate:receipt.originDate,
      status:legacy.status,observedAfterOrigin:originIndex<0?null:prepared.series.length-originIndex-1,
      eligibleToEvaluate:originIndex>=0&&prepared.series.length-originIndex-1>=receipt.horizon,
      caveat:legacy.caveat};
  });
  const commitment=createSuffixCommitment(prepared.series);
  const report={experiment:'seshat-c375-rolling-vintage-diagnostic',status:'read_only',
    runId:process.env.GITHUB_RUN_ID??null,codeCommit:process.env.GITHUB_SHA??null,
    requestedAt,receivedAt,provider:url,rawSha256:createHash('sha256').update(raw).digest('hex'),
    latestDate:prepared.latestDate,observations:prepared.series.length,
    originalReceipts,commitmentId:commitment.id,
    limitation:'Legacy digest mismatches are inconclusive; new suffix commitments prove only equality of observed overlap, not source vintage authenticity'};
  fs.writeFileSync('seshat-c375-derived-commitment.json',JSON.stringify({report,commitment},null,2)+'\n',{flag:'wx'});
  console.log('SESHAT_C375_REPORT_BEGIN');console.log(JSON.stringify(report,null,2));console.log('SESHAT_C375_REPORT_END');
}
main().catch(e=>{console.error('C375_DIAGNOSTIC_FAILED:',e.message);process.exitCode=2;});
