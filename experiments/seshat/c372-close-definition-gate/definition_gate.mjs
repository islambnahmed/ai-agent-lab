/** Source-definition gate: avoid false historical-close cross-source certification. */
const REQUIRED = ['instrument','unit','date','closeMethod','clockBasis'];
export function assessComparison(primary,secondary,{maxDifferenceUsd=5}={}) {
  for(const [label,row] of [['primary',primary],['secondary',secondary]]) {
    if(!row || !Number.isFinite(row.price) || row.price<=0) throw Error(`${label}: positive finite price required`);
    if(typeof row.source!=='string'||!row.source.trim())throw Error(`${label}: source required`);
  }
  if(primary.source===secondary.source)return {status:'not_independent',reason:'same_named_source'};
  const missing=REQUIRED.filter(key=>!primary[key]||!secondary[key]);
  if(missing.length)return {status:'not_comparable',reason:'missing_close_definition',missing};
  const mismatches=REQUIRED.filter(key=>primary[key]!==secondary[key]);
  if(mismatches.length)return {status:'not_comparable',reason:'different_close_definitions',mismatches};
  if(!primary.releaseEvidence || !secondary.releaseEvidence)return {status:'not_certified',reason:'missing_independent_release_evidence'};
  const delta=Math.abs(primary.price-secondary.price);
  return {status:delta<=maxDifferenceUsd?'consistent_by_threshold':'divergent_by_threshold',deltaUsd:delta,
    caveat:'Agreement does not establish upstream independence or immutable vintage; inspect release evidence.'};
}
export function evaluatePriceCandidates({point,baseline,observations}) {
  if(!Number.isFinite(point)||!Number.isFinite(baseline)||point<=0||baseline<=0)throw Error('Bad predictions');
  if(!Array.isArray(observations)||observations.length===0)throw Error('Observations required');
  const threshold=(point+baseline)/2;
  return {threshold,rankings:observations.map(o=>{
    if(!Number.isFinite(o.price)||o.price<=0)throw Error('Bad observation');
    const modelError=Math.abs(point-o.price),baselineError=Math.abs(baseline-o.price);
    return {source:o.source,date:o.date,modelError,baselineError,
      winner:modelError<baselineError?'model':modelError>baselineError?'baseline':'tie'};
  }),caveat:'Sensitivity check only: non-equivalent closes cannot certify a forecast settlement.'};
}
