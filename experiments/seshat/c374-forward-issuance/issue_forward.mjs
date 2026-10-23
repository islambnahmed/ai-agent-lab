/** Read-only forward-only issuance. Logs derived data, never vendor raw feed. */
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {prepareProviderHistory} from '../../../products/gold-forecast/data.mjs';
import {issueReceipt,verifyReceipt} from '../../../products/gold-forecast/journal.mjs';
import {prospectiveEligibility} from './eligibility.mjs';
async function main() {
  const codeCommit=process.env.GITHUB_SHA;
  if(!/^[a-f0-9]{40}$/.test(codeCommit??''))throw Error('GITHUB_SHA required for code-pinned receipt');
  const url='https://standardbullion.com/api/v1/market/history?metal=XAU&range=1y';
  const requestedAt=new Date().toISOString();
  const response=await fetch(url,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(30000)});
  if(!response.ok)throw Error('Provider HTTP '+response.status);
  const raw=Buffer.from(await response.arrayBuffer());
  if(!raw.length||raw.length>5_000_000)throw Error('Unexpected response size');
  const receivedAt=new Date().toISOString();
  const sourceManifest={url,requestedAt,receivedAt,httpStatus:response.status,
    rawSha256:createHash('sha256').update(raw).digest('hex'),status:'fetched'};
  const prepared=prepareProviderHistory(JSON.parse(raw.toString('utf8')),receivedAt);
  const issuedAt=new Date().toISOString(),receipts=[],blocked=[];
  for(const h of [1,7,30]){
    const gate=prospectiveEligibility({originDate:prepared.latestDate,issuedAt,horizon:h});
    if(!gate.eligible){blocked.push(gate);continue;}
    const receipt=issueReceipt(prepared.series,h,{issuedAt,source:'Standard Bullion',codeCommit,sourceManifest});
    verifyReceipt(receipt);
    receipts.push({gate,receipt});
  }
  const report={experiment:'seshat-c374-forward-issuance',
    status:receipts.length?'provisional_forward_receipts':'no_eligible_receipts',
    githubRunId:process.env.GITHUB_RUN_ID??null,codeCommit,issuedAt,sourceManifest,
    observations:prepared.series.length,latestCompletedObservation:prepared.latestDate,
    cadence:prepared.calendar,receipts,blocked,
    evaluationPolicy:{
      precommit:'first successful GitHub Actions issuance per originDate/horizon only; no cherry-picking later runs',
      target:'h-th strictly later unique UTC-dated provider close; no other calendar or vendor substitution',
      settlement:'pending until h new observations and same-definition independent review; quarantine if original history unavailable',
      benchmark:'unchanged origin close; paired absolute error; no skill claim from one forecast'},
    limitations:['Provider close semantics and historical publication times unverified',
      'No licensed raw history archived; original historical prefix may be unrecoverable',
      'GitHub Actions timestamps prove script execution, not provider publication',
      'Prospective eligibility assumes at most one close per UTC date',
      'No certified settlement, predictive skill, statistical significance or trading advice']};
  fs.writeFileSync('seshat-c374-forward-receipts.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log('SESHAT_C374_RECEIPT_BEGIN');
  console.log(JSON.stringify(report,null,2));
  console.log('SESHAT_C374_RECEIPT_END');
  if(!receipts.length)process.exitCode=3;
}
main().catch(error=>{console.error('C374_FORWARD_ISSUANCE_FAILED:',error.message);process.exitCode=2;});
