/**
 * Keystone Cycle 121: fail-closed, duplicate-aware Gold Lab settlement reporting.
 * Descriptive maturity is not proof of prospective forecasting skill.
 * Does not authenticate timestamps, source vintages, or caller-provided flags.
 */
export const HORIZONS=Object.freeze([1,7,30]);
const ISO=/^\d{4}-\d{2}-\d{2}$/;
function validDate(date){
  if(typeof date!=='string'||!ISO.test(date))return false;
  const ms=Date.parse(date+'T00:00:00Z');
  return Number.isFinite(ms)&&new Date(ms).toISOString().slice(0,10)===date;
}
function validMatured(row){
  return row&&typeof row==='object'&&!Array.isArray(row)&&
    HORIZONS.includes(row.horizon)&&row.status==='matured'&&
    validDate(row.targetDate)&&Number.isFinite(row.actual)&&row.actual>0&&
    Number.isFinite(row.modelAbsError)&&row.modelAbsError>=0&&
    Number.isFinite(row.baselineAbsError)&&row.baselineAbsError>=0&&
    typeof row.id==='string'&&row.id.trim().length>0;
}
function summarize(rows){
  return HORIZONS.map(h=>{
    const subset=rows.filter(r=>r.horizon===h),n=subset.length;
    return {horizon:h,matured:n,
      modelMae:n?subset.reduce((s,r)=>s+r.modelAbsError,0)/n:null,
      baselineMae:n?subset.reduce((s,r)=>s+r.baselineAbsError,0)/n:null};
  });
}
// Outcome inputs originate from JSON; reject cyclic/non-JSON duplicate groups.
function canonical(value){
  if(value===null||typeof value!=='object')return JSON.stringify(value);
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
}
export function auditSettlements(outcomes){
  if(!Array.isArray(outcomes))throw new TypeError('Settlement outcomes must be an array');
  const byId=new Map(),duplicateIndices=[],conflictingIndices=[],conflictingIds=[],invalidIdentity=[];
  for(let i=0;i<outcomes.length;i++){
    const r=outcomes[i];
    if(!r||typeof r!=='object'||Array.isArray(r)||typeof r.id!=='string'||!r.id.trim()){
      invalidIdentity.push(i);continue;
    }
    if(!byId.has(r.id))byId.set(r.id,[]);
    byId.get(r.id).push(i);
  }
  for(const [id,indices] of byId){
    if(indices.length<2)continue;
    let signatures;
    try{signatures=new Set(indices.map(i=>canonical(outcomes[i])))}
    catch{signatures=new Set(['invalid-non-json',...indices.map(String)])}
    if(signatures.size===1)duplicateIndices.push(...indices.slice(1));
    else{conflictingIds.push(id);conflictingIndices.push(...indices)}
  }
  const suppressed=new Set([...duplicateIndices,...conflictingIndices,...invalidIdentity]);
  const descriptive=[],invalid=[...invalidIdentity],pending=[],other=[],untrustedVerificationClaims=[];
  for(let i=0;i<outcomes.length;i++){
    const row=outcomes[i];
    if(row?.prospectiveVerified===true||row?.scoreEligible===true||row?.chronologyStatus==='verified')
      untrustedVerificationClaims.push(i);
    if(suppressed.has(i))continue;
    if(row.status==='pending'){pending.push(i);continue;}
    if(row.status!=='matured'){other.push(i);continue;}
    if(!validMatured(row)){invalid.push(i);continue;}
    descriptive.push(row);
  }
  return {
    schemaVersion:2,descriptive:summarize(descriptive),verified:summarize([]),
    counts:{input:outcomes.length,uniqueIds:byId.size,descriptive:descriptive.length,verified:0,
      pending:pending.length,invalid:invalid.length,other:other.length,
      exactDuplicatesIgnored:duplicateIndices.length,conflictingReceipts:conflictingIds.length,
      untrustedVerificationClaims:untrustedVerificationClaims.length},
    excludedIndices:{invalid,pending,other,exactDuplicates:duplicateIndices,
      conflicting:conflictingIndices,untrustedVerificationClaims},
    conflictingIds,status:'PROSPECTIVE_SKILL_UNVERIFIED',
    reason:'Matured outcomes and caller flags do not authenticate publication before first availability or immutable price vintages. Conflicting duplicate ids are quarantined.'
  };
}
