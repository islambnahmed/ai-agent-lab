// Audit frozen published real-provider summaries; never reconstruct raw prices or claim live skill.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const round=(x,n=2)=>Number(x.toFixed(n));
const expected=[1,7,30];
function summarize(report,source,key){
  const rows=report[key];
  if(!Array.isArray(rows)||rows.length!==3||expected.some(h=>!rows.some(r=>r.horizon===h)))
    throw Error(source+': expected exactly 1/7/30 observed-close horizons');
  if(!Number.isInteger(report.rows)||report.rows<1||typeof report.runAt!=='string')
    throw Error(source+': invalid provenance');
  return rows.map(r=>{
    const {horizon,model,audit,baseline,coverage,disjoint}=r;
    if(!audit||!baseline||!disjoint||!Array.isArray(disjoint.phases)||
      !Number.isInteger(audit.n)||audit.n<1||!Number.isFinite(audit.mae)||
      !Number.isFinite(baseline.mae)||baseline.mae<0||audit.mae<0||
      !Number.isFinite(coverage)||coverage<0||coverage>100||
      !Number.isInteger(disjoint.candidate?.n)||disjoint.candidate.n<1||
      disjoint.candidate.n>audit.n||!disjoint.phases.length||
      disjoint.phases.some(p=>!Number.isFinite(p.coverage)||p.coverage<0||p.coverage>100))
      throw Error(source+': invalid horizon '+horizon+' metrics');
    const phases=disjoint.phases.map(p=>p.coverage);
    const skill=baseline.mae===0?null:100*(1-audit.mae/baseline.mae);
    if(skill!==null&&Math.abs(skill-r.skillPct)>1e-6)
      throw Error(source+': skill mismatch for horizon '+horizon);
    return {source,horizon,selectedModel:model,auditN:audit.n,
      selectedMaeUsd:round(audit.mae),baselineMaeUsd:round(baseline.mae),
      selectedSkillVsBaselinePct:skill===null?null:round(skill),
      empiricalCoveragePct:round(coverage),coverageGapVsNominal80Pp:round(coverage-80),
      disjointWindows:disjoint.candidate.n,
      phaseCoverageRangePct:[round(Math.min(...phases)),round(Math.max(...phases))],
      selectedBeatBaseline:audit.mae<baseline.mae};
  }).sort((a,b)=>a.horizon-b.horizon);
}
export function auditEvidence(dealerReport,researchReport){
  const dealer=summarize(dealerReport,'Standard Bullion 1y','horizons');
  const research=summarize(researchReport,'HistData 2016-2026','priceBenchmarks');
  if(!Array.isArray(researchReport.ablation)||researchReport.ablation.length!==3)
    throw Error('Missing matched-origin macro ablation');
  const macro=researchReport.ablation.map(x=>{
    const a=x.audit;
    if(!a||!a.priceRidge||!a.macroRidge||!a.baseline||!Number.isInteger(a.n))
      throw Error('Incomplete matched-origin macro audit');
    return {horizon:x.horizon,matchedAuditN:a.n,
      macroSkillVsBaselinePct:round(a.macroSkillVsBaselinePct),
      macroSkillVsPriceRidgePct:round(a.macroSkillVsPriceRidgePct),
      macroBetterThanPriceRidge:a.macroRidge.mae<a.priceRidge.mae};
  }).sort((a,b)=>a.horizon-b.horizon);
  return {
    evidenceType:'frozen retrospective summaries, not fresh outcomes',
    auditAtUtc:'2026-10-19',
    sources:[
      {source:'Standard Bullion 1y',rows:dealerReport.rows,from:dealerReport.from,to:dealerReport.to,reportRunAt:dealerReport.runAt},
      {source:'HistData 2016-2026',rows:researchReport.rows,from:researchReport.from,to:researchReport.to,reportRunAt:researchReport.runAt}
    ],
    selectedForecasts:[...dealer,...research],matchedMacroAblation:macro,
    warnings:[
      'HistData nominal 80% bands covered 64.81%, 63.85%, 68.67% for h=1,7,30 in the frozen audit. Not guaranteed 80% coverage.',
      'All selected HistData models were persistence: no selected-model improvement over last close.',
      'Macro Ridge did not beat matched price-only Ridge at any horizon; audit results cannot justify post-hoc promotion.',
      'Overlapping h=7/30 targets and temporal dependence preclude naive independent-sample confidence claims.',
      'Dealer midpoints and HistData bid closes are distinct measurements; never pool or claim independent source authentication.',
      'No raw archive, original frozen vintage, or refreshed provider history was independently verified here; prospective receipts unscored.',
      'Legacy directionAccuracy for persistence is not a directional-skill measure; exclude it from decisions.'
    ],
    decision:'HOLD: no production promotion or predictive-accuracy claim'
  };
}
const direct=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(direct){
  const dir=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','reports');
  const dealer=JSON.parse(fs.readFileSync(path.join(dir,'readiness-20261012.json'),'utf8'));
  const research=JSON.parse(fs.readFileSync(path.join(dir,'research-benchmark-20261012.json'),'utf8'));
  console.log(JSON.stringify(auditEvidence(dealer,research),null,2));
}
