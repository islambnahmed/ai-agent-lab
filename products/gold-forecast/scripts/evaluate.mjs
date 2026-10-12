import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {forecast,sample,metrics} from '../forecast.mjs';
import {prepareProviderHistory,validatedSpot,crossCheck} from '../data.mjs';
import {hash} from '../journal.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'data',name+'.json'),'utf8'));
const manifest=read('fetch-manifest');
const asOf=manifest.history.receivedAt;
const history=read('history'),prepared=prepareProviderHistory(history,asOf);
let sourceCheck;
try{sourceCheck=crossCheck(validatedSpot(read('spot'),Date.parse(manifest.spot.receivedAt)),read('crosscheck'),Date.parse(manifest.crosscheck.receivedAt));}
catch(e){sourceCheck={status:'unavailable_or_invalid',error:e.message};}
const started=Date.now();
const horizons=[1,7,30].map(h=>{
  const result=forecast(prepared.series,h,{asOf});
  const {series,...summary}=result;
  summary.exploratoryAuditByModel=result.candidates.map(c=>{
    const rows=sample(prepared.series,h,c.model,result.split.auditStart,prepared.series.length-h+1);
    const audit=metrics(rows);
    return {model:c.model,audit,skillPct:result.baseline.mae>0?100*(1-audit.mae/result.baseline.mae):null,
      interpretation:'Exploratory comparison only; cannot change the frozen selector using these outcomes'};
  });
  return summary;
});
const report={schemaVersion:1,runAt:new Date().toISOString(),asOf,codeCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),
  implementationHash:hash(['forecast.mjs','models.mjs','data.mjs','historical-integrity.mjs','calendar_contract.mjs'].map(f=>fs.readFileSync(path.join(root,f),'utf8'))),
  source:history.source,attribution:history.attribution,sourceManifest:manifest,historyHash:hash(prepared.series),
  rows:prepared.series.length,from:prepared.series[0].date,to:prepared.latestDate,calendar:prepared.calendar,
  sourceCheck,horizons,elapsedMs:Date.now()-started,
  limitations:['Current-vintage retrospective reconstruction, not historical point-in-time replay',
    'Audit period has been inspected by earlier versions; it is not a fresh blind validation of this new implementation',
    'Live cross-check does not validate historical prices or upstream independence',
    'Non-overlapping windows are not independent; no significance or market-edge claim',
    'No matured prospective receipts yet; performance after code changes requires future evaluation']};
const out=path.join(root,'reports','readiness-20261012.json');
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({file:out,rows:report.rows,calendar:report.calendar,sourceCheck,horizons:horizons.map(r=>({h:r.horizon,model:r.model,mae:r.audit.mae,baseline:r.baseline.mae,skillPct:r.skillPct,coverage:r.coverage,disjoint:r.disjoint.candidate.n})),elapsedMs:report.elapsedMs},null,2));
