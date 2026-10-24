import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {issueReceipt,settleReceipt,hash,parseVerifiedHistorySnapshot,appendVerifiedVintage} from '../journal.mjs';
import {prepareProviderHistory} from '../data.mjs';
import {preserveFirstObservedTarget} from '../settlement-observations.mjs';
import {gateSettlement,summarizeSettlements} from '../settlement-eligibility.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'data',name+'.json'),'utf8'));
const manifest=read('fetch-manifest');
const asOf=manifest.history.receivedAt;
const historyBytes=fs.readFileSync(path.join(root,'data','history.json'));
const prepared=prepareProviderHistory(parseVerifiedHistorySnapshot(historyBytes,manifest.history),asOf);
const dir=path.join(root,'reports','prospective');fs.mkdirSync(dir,{recursive:true});
const vintages=path.join(root,'data','vintages');fs.mkdirSync(vintages,{recursive:true});
const firstObserved=path.join(root,'data','settlement-observations');
const command=process.argv[2];
if(command==='issue'){
  const files=['forecast.mjs','models.mjs','data.mjs','historical-integrity.mjs','calendar_contract.mjs','journal.mjs',
    'scripts/journal.mjs','scripts/fetch_data.py','settlement-observations.mjs',
    'settlement-eligibility.mjs','package.json'];
  const dirty=execFileSync('git',['status','--porcelain','--',...files],{cwd:root,encoding:'utf8'});
  if(dirty.trim())throw Error('Commit implementation before issuing forecasts');
  const codeCommit=execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
  const issuedAt=new Date().toISOString();
  for(const h of [1,7,30]){
    const filename=path.join(dir,prepared.latestDate+'-h'+h+'.json');
    if(fs.existsSync(filename)){console.log('Existing receipt preserved: '+path.basename(filename));continue;}
    const receipt=issueReceipt(prepared.series,h,{issuedAt,source:'Standard Bullion',codeCommit,sourceManifest:manifest.history});
    const vintagePath=path.join(vintages,receipt.historyHash+'.json');
    if(!fs.existsSync(vintagePath))fs.writeFileSync(vintagePath,JSON.stringify(prepared.series),{flag:'wx'});
    fs.writeFileSync(filename,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
    console.log(JSON.stringify({file:filename,id:receipt.id,targetDate:receipt.targetDate,point:receipt.point}));
  }
}else if(command==='settle'){
  const outcomes=fs.readdirSync(dir).filter(f=>f.endsWith('.json')).map(f=>{
    const receipt=JSON.parse(fs.readFileSync(path.join(dir,f),'utf8'));
    try{
      const frozen=JSON.parse(fs.readFileSync(path.join(vintages,receipt.historyHash+'.json'),'utf8'));
      if(hash(frozen)!==receipt.historyHash)throw Error('Original local vintage corrupted');
      const appended=appendVerifiedVintage(frozen,prepared.series,receipt.originDate);
      const outcome=settleReceipt(receipt,appended,{asOf});
      // Preserve raw arithmetic maturity first, then downgrade unverified timing.
      const guarded=preserveFirstObservedTarget(outcome,{directory:firstObserved,
        observedAt:new Date().toISOString(),sourceDigest:manifest.history.storedSha256});
      return gateSettlement(guarded);
    }
    catch(e){return {id:receipt.id,horizon:receipt.horizon,status:'quarantined',error:e.message};}
  });
  // No authenticated publication-before-close evidence yet: headline MAE stays null.
  const summaries=summarizeSettlements(outcomes);
  const report={asOf,outcomes,summaries,
    timingPolicy:'fail_closed_no_independent_publication_before_close_verifier',
    caveat:'Local first-seen target checks are mutable, not trusted publication timestamps. '
      +'All arithmetic maturities are provisional until independent GitHub publication '
      +'and provider close times are verified.'};
  const out=path.join(root,'runs');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'settlements.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
}else throw Error('Use: node scripts/journal.mjs issue|settle');
