import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {issueReceipt,settleReceipt} from '../journal.mjs';
import {reconcileVintage} from '../vintage-reconcile.mjs';
import {prepareProviderHistory} from '../data.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'data',name+'.json'),'utf8'));
const manifest=read('fetch-manifest');
const asOf=manifest.history.receivedAt;
const prepared=prepareProviderHistory(read('history'),asOf);
const dir=path.join(root,'reports','prospective');fs.mkdirSync(dir,{recursive:true});
const vintages=path.join(root,'data','vintages');fs.mkdirSync(vintages,{recursive:true});
const command=process.argv[2];
if(command==='issue'){
  const files=['forecast.mjs','models.mjs','data.mjs','historical-integrity.mjs','calendar_contract.mjs','journal.mjs'];
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
      let frozen=null;
      try{
        frozen=JSON.parse(fs.readFileSync(path.join(vintages,receipt.historyHash+'.json'),'utf8'));
      }catch(e){
        if(e.code!=='ENOENT')throw e; // malformed or inaccessible snapshots must not be ignored
      }
      // Missing local cache is not an automatic failure when the current source
      // reproduces the original signed receipt history exactly.
      const reconciled=reconcileVintage(receipt,prepared.series,frozen);
      return settleReceipt(receipt,reconciled,{asOf});
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
