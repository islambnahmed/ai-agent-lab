import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {prepareHistory,UNIT} from '../data.mjs';
import {features} from '../models.mjs';
import {availableFeatures} from '../feature-store.mjs';
import {fitRidgeAt} from '../research-model.mjs';
import {forecast,metrics} from '../forecast.mjs';
import {hash} from '../journal.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'data',name+'.json'),'utf8'));
const input=read('histdata'),macro=read('macro-vintages'),manifest=JSON.parse(fs.readFileSync(path.join(root,'reports/source-research-20261012.json')));
if(input.metal!=='XAU'||input.unit!==UNIT||input.grain!=='daily'||!input.priceKind?.includes('bid'))throw Error('Wrong research price contract');
const prepared=prepareHistory(input.points,{asOf:input.receivedAt}),series=prepared.series,prices=series.map(r=>r.price),n=prices.length;
const keys=['real_yield_10y_pct','nominal_yield_10y_pct','broad_dollar_index','us_cpi_yoy_pct','effective_fed_funds_pct'];
const macroVectors=[],priceVectors=[];const missing={};
for(let i=0;i<n;i++){
  const origin=series[i].date+'T23:59:59.999Z',context=availableFeatures(macro,origin,{maxAgeDays:120});
  const absent=keys.filter(k=>!context[k]||context[k].stale);
  for(const key of absent)missing[key]=(missing[key]??0)+1;
  if(i<60||absent.length){macroVectors.push(null);priceVectors.push(null);continue;}
  const price=features(prices,i);priceVectors.push(price);macroVectors.push([...price,...keys.map(k=>context[k].value)]);
}
const selectionEnd=Math.floor(.6*n),auditStart=Math.floor(.8*n);
function score(rows){
  if(!rows.length)return null;
  const base=metrics(rows.map(r=>({...r,point:r.originClose}))),price=metrics(rows.map(r=>({...r,point:r.pricePoint}))),extended=metrics(rows);
  return {n:rows.length,from:rows[0].originDate,to:rows.at(-1).originDate,baseline:base,priceRidge:price,macroRidge:extended,
    macroSkillVsBaselinePct:100*(1-extended.mae/base.mae),macroSkillVsPriceRidgePct:100*(1-extended.mae/price.mae)};
}
const ablation=[1,7,30].map(h=>{
  const rows=[];
  for(let i=60;i+h<n;i++){
    const extended=fitRidgeAt(prices,macroVectors,i,h),price=fitRidgeAt(prices,priceVectors,i,h);
    if(!extended||!price)continue;
    rows.push({originIndex:i,originDate:series[i].date,originClose:prices[i],actual:prices[i+h],point:extended.point,pricePoint:price.point});
  }
  const audit=rows.filter(r=>r.originIndex>=auditStart);
  // Only describe the predeclared audit; never use its outcomes for selection.
  const disjoint=[];let next=-1;for(const r of audit)if(r.originIndex>=next){disjoint.push(r);next=r.originIndex+h;}
  return {horizon:h,selection:score(rows.filter(r=>r.originIndex<selectionEnd-h)),
    calibrationPeriod:score(rows.filter(r=>r.originIndex>=selectionEnd&&r.originIndex<auditStart-h)),audit:score(audit),disjoint:score(disjoint)};
});
const priceBenchmarks=[1,7,30].map(h=>{
  const {series:tail,...summary}=forecast(series,h,{asOf:input.receivedAt});return summary;
});
const report={schemaVersion:1,runAt:new Date().toISOString(),baseCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),
  implementationHash:hash(['models.mjs','research-model.mjs','feature-store.mjs','scripts/evaluate_research.mjs'].map(f=>fs.readFileSync(path.join(root,f),'utf8'))),
  source:input.source,measurement:input.priceKind,historyHash:hash(series),macroHash:hash(macro),rows:n,from:series[0].date,to:series.at(-1).date,
  calendar:prepared.calendar,dataWarnings:prepared.warnings,sourceManifest:'source-research-20261012.json',
  quarantinedDays:manifest.requests.flatMap(r=>r.quarantinedUtcDays??[]),
  macroContext:{features:keys,completeOrigins:macroVectors.filter(Boolean).length,missingOrStaleByFeature:missing,maxAgeDays:120,
    availability:'Monthly ALFRED as-of snapshots, usable only after conservative UTC end of vintage day'},
  fixedDesign:{window:400,penalty:20,split:{selectionEnd,auditStart},priceFeatureCount:5,macroFeatureCount:5,
    policy:'Identical eligible origins and matured training rows for price-only and price+macro ablations. No audit retuning or automatic promotion.'},
  priceBenchmarks,ablation,limitations:[...manifest.limitations,
    'Observed close horizons; omitted ambiguous days are not reconstructed',
    'Monthly vintage sampling understates daily information availability; it is not an exact release replay',
    'Price history is current-vintage research and no prospective macro-model receipts exist',
    'Audit inspected during this research; improvement here cannot establish future performance']};
fs.writeFileSync(path.join(root,'reports/research-benchmark-20261012.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({rows:n,from:report.from,to:report.to,quarantinedDays:report.quarantinedDays,macroContext:report.macroContext,
  prices:priceBenchmarks.map(r=>({h:r.horizon,model:r.model,skill:r.skillPct,disjoint:r.disjoint.candidate.n})),
  ablation:ablation.map(r=>({h:r.horizon,audit:r.audit,disjoint:r.disjoint?.n}))},null,2));
