/**
 * Conservative descriptive summary of prospective gold settlements.
 * This does not authenticate issuance timestamps, vintages or predictive skill.
 * Never pool horizons or silently treat quarantines as successes.
 */
const HORIZONS=[1,7,30];
const mean=(rows,key)=>rows.reduce((s,r)=>s+r[key],0)/rows.length;

export function summarizeProspective(outcomes){
  if(!Array.isArray(outcomes))throw Error('Outcomes must be an array');
  const seen=new Set();
  const buckets=new Map(HORIZONS.map(h=>[h,{matured:[],pending:0,quarantined:0}]));
  let unattributedQuarantined=0;
  for(const o of outcomes){
    if(!o||typeof o!=='object'||Array.isArray(o))throw Error('Invalid outcome');
    if(typeof o.id!=='string'||!o.id)throw Error('Outcome ID required');
    if(seen.has(o.id))throw Error('Duplicate prospective outcome ID: '+o.id);
    seen.add(o.id);
    if(!['matured','pending','quarantined'].includes(o.status))throw Error('Unknown outcome status');
    if(!HORIZONS.includes(o.horizon)){
      if(o.status==='quarantined'&&o.horizon==null){unattributedQuarantined++;continue;}
      throw Error('Invalid or missing outcome horizon');
    }
    const bucket=buckets.get(o.horizon);
    if(o.status==='matured'){
      if(!Number.isFinite(o.modelAbsError)||o.modelAbsError<0||
         !Number.isFinite(o.baselineAbsError)||o.baselineAbsError<0||
         typeof o.covered!=='boolean')throw Error('Invalid matured outcome metrics');
      bucket.matured.push(o);
    }else bucket[o.status]++;
  }
  const summaries=HORIZONS.map(horizon=>{
    const {matured:rows,pending,quarantined}=buckets.get(horizon),n=rows.length;
    const modelMae=n?mean(rows,'modelAbsError'):null;
    const baselineMae=n?mean(rows,'baselineAbsError'):null;
    return {horizon,matured:n,pending,quarantined,modelMae,baselineMae,
      empiricalCoveragePct:n?100*rows.filter(r=>r.covered).length/n:null,
      relativeMaeSkillPct:n&&baselineMae>0?100*(1-modelMae/baselineMae):null,
      status:n?'descriptive_only':'no_matured_outcomes'};
  });
  return {schemaVersion:1,totalOutcomes:outcomes.length,unattributedQuarantined,
    summaries,evidenceStatus:'not_verified_for_promotion',
    caveat:'Descriptive only. Horizons remain separate; windows may overlap. Git issuance anchors, source vintages, uncertainty and prospective skill require independent verification.'};
}
