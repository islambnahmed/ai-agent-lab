import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {issueReceipt,verifyReceipt,settleReceipt,hash} from '../journal.mjs';
import {prepareProviderHistory} from '../data.mjs';
import {checkReceiptCohort} from '../receipt-cohort.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'data',name+'.json'),'utf8'));
const manifest=read('fetch-manifest');
const asOf=manifest.history.receivedAt;
const prepared=prepareProviderHistory(read('history'),asOf);
const dir=path.join(root,'reports','prospective');fs.mkdirSync(dir,{recursive:true});
const vintages=path.join(root,'data','vintages');fs.mkdirSync(vintages,{recursive:true});
const command=process.argv[2];
if(command==='issue'){
  const horizons=[1,7,30];
  const filenames=horizons.map(h=>path.join(dir,prepared.latestDate+'-h'+h+'.json'));
  const existing=filenames.map(filename=>fs.existsSync(filename)?JSON.parse(fs.readFileSync(filename,'utf8')):null);
  const cohortState=checkReceiptCohort(existing,prepared.latestDate,verifyReceipt);
  if(cohortState==='complete'){
    for(const filename of filenames)console.log('Existing receipt preserved: '+path.basename(filename));
  }else{
    const files=['forecast.mjs','models.mjs','data.mjs','historical-integrity.mjs','calendar_contract.mjs',
      'journal.mjs','receipt-cohort.mjs','scripts/journal.mjs'];
    const dirty=execFileSync('git',['status','--porcelain','--',...files],{cwd:root,encoding:'utf8'});
    if(dirty.trim())throw Error('Commit implementation before issuing forecasts');
    const codeCommit=execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
    const issuedAt=new Date().toISOString();
    // Prepare all horizons before writing any receipt; never finish a partial
    // cohort from a subsequent snapshot after a crash or interrupted issuance.
    const receipts=horizons.map(h=>issueReceipt(prepared.series,h,
      {issuedAt,source:'Standard Bullion',codeCommit,sourceManifest:manifest.history}));
    checkReceiptCohort(receipts,prepared.latestDate,verifyReceipt);
    const vintagePath=path.join(vintages,receipts[0].historyHash+'.json');
    if(!fs.existsSync(vintagePath))fs.writeFileSync(vintagePath,JSON.stringify(prepared.series),{flag:'wx'});
    for(let i=0;i<receipts.length;i++){
      const receipt=receipts[i],filename=filenames[i];
      fs.writeFileSync(filename,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
      console.log(JSON.stringify({file:filename,id:receipt.id,targetDate:receipt.targetDate,point:receipt.point}));
    }
  }
}else if(command==='settle'){
  const outcomes=fs.readdirSync(dir).filter(f=>f.endsWith('.json')).map(f=>{
    const receipt=JSON.parse(fs.readFileSync(path.join(dir,f),'utf8'));
    try{
      const frozen=JSON.parse(fs.readFileSync(path.join(vintages,receipt.historyHash+'.json'),'utf8'));
      if(hash(frozen)!==receipt.historyHash)throw Error('Original local vintage corrupted');
      const frozenDates=new Map(frozen.map(r=>[r.date,r.price]));
      if(!prepared.series.some(r=>r.date===receipt.originDate))throw Error('Origin missing from refreshed source');
      for(const row of prepared.series)if(frozenDates.has(row.date)&&frozenDates.get(row.date)!==row.price)
        throw Error('Provider revised historical vintage: '+row.date);
      const appended=frozen.concat(prepared.series.filter(r=>r.date>receipt.originDate));
      return settleReceipt(receipt,appended,{asOf});
    }
    catch(e){return {id:receipt.id,status:'quarantined',error:e.message};}
  });
  // Keep horizons separate; never pool them to select a winner.
  const summaries=[1,7,30].map(h=>{
    const rows=outcomes.filter(r=>r.horizon===h&&r.status==='matured');
    const avg=key=>rows.length?rows.reduce((s,r)=>s+r[key],0)/rows.length:null;
    return {horizon:h,matured:rows.length,modelMae:avg('modelAbsError'),baselineMae:avg('baselineAbsError')};
  });
  const report={asOf,outcomes,summaries,caveat:'Descriptive prospective outcomes; receipt Git timestamps must precede target close'};
  const out=path.join(root,'runs');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'settlements.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
}else throw Error('Use: node scripts/journal.mjs issue|settle');
