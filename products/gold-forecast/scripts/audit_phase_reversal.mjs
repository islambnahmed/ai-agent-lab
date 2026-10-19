// Recompute phase-by-phase Ridge vs persistence skill from a frozen research report.
// Descriptive retrospective evidence only; never select/promote from the audit split.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const horizons=[1,7,30];
const round=x=>Math.round(x*10000)/10000;
function metrics(row,label){
  const base=row?.baseline, ridge=row?.priceRidge;
  for(const [name,x] of [['baseline',base],['priceRidge',ridge]]){
    if(!x||!Number.isInteger(x.n)||x.n<1||!Number.isFinite(x.mae)||x.mae<=0||!Number.isFinite(x.rmse)||x.rmse<=0)
      throw Error(`${label}: invalid ${name} metrics`);
  }
  if(base.n!==ridge.n||base.n!==row.n)throw Error(`${label}: unmatched sample counts`);
  return {n:row.n,baselineMae:round(base.mae),ridgeMae:round(ridge.mae),
    maeSkillPct:round(100*(1-ridge.mae/base.mae)),
    rmseSkillPct:round(100*(1-ridge.rmse/base.rmse))};
}
export function auditPhaseReversal(report){
  if(!report||!Array.isArray(report.ablation)||report.ablation.length!==3)
    throw Error('Expected 3 matched-origin ablation horizons');
  const seen=new Set();
  const result=report.ablation.map(item=>{
    const h=item.horizon;
    if(!horizons.includes(h)||seen.has(h))throw Error('Missing/duplicate/unsupported horizon');
    seen.add(h);
    const phases={selection:metrics(item.selection,`h${h} selection`),
      calibration:metrics(item.calibrationPeriod,`h${h} calibration`),
      audit:metrics(item.audit,`h${h} audit`),
      disjoint:metrics(item.disjoint,`h${h} disjoint`)};
    if(phases.disjoint.n>phases.audit.n)throw Error('Disjoint count exceeds audit count');
    return {horizon:h,phases,
      reversal:phases.selection.maeSkillPct<0&&phases.calibration.maeSkillPct<0&&phases.audit.maeSkillPct>0,
      disjointSameDirection:Math.sign(phases.disjoint.maeSkillPct)===Math.sign(phases.audit.maeSkillPct),
      auditMaeRmseAgree:Math.sign(phases.audit.maeSkillPct)===Math.sign(phases.audit.rmseSkillPct)};
  }).sort((a,b)=>a.horizon-b.horizon);
  return {source:report.source,reportRunAt:report.runAt,reportHistoryHash:report.historyHash,
    evidence:'inspected retrospective ablation; not an independently held-out experiment',
    comparisons:result,
    caveats:[
      'Selection and calibration phases are not blind new evidence; audit phase has also been inspected.',
      'Disjoint windows reduce overlapping targets but are not independent; n alone is not a confidence interval.',
      'The data are HistData XAU/USD bid closes, not necessarily a dealer spot midpoint.',
      'Do not promote Ridge using the retrospective audit reversal; require prospectively committed outcomes.'
    ],decision:'HOLD'};
}
const direct=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(direct){
  const input=process.argv[2]??path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','reports','research-benchmark-20261012.json');
  console.log(JSON.stringify(auditPhaseReversal(JSON.parse(fs.readFileSync(input,'utf8'))),null,2));
}
