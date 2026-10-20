/** Worker A cycle 243: simulated independent-frame + oracle gate. Node 18+. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const hash=x=>createHash('sha256').update(x).digest('hex');
function canonical(ids) {
  if(!Array.isArray(ids)||ids.some(x=>typeof x!=='string'||!x)) throw Error('invalid IDs');
  const s=[...ids].sort();
  if(new Set(s).size!==s.length) throw Error('duplicate IDs');
  return s;
}
function choose(ids,seed,n) {
  const s=canonical(ids);
  if(!/^[0-9a-f]{64}$/.test(seed)||!Number.isInteger(n)||n<1||n>s.length) throw Error('bad sample');
  return s.map(id=>[hash('worker-a-243\0'+seed+'\0'+id),id])
    .sort((a,b)=>a[0].localeCompare(b[0])||a[1].localeCompare(b[1])).slice(0,n).map(x=>x[1]);
}
const abstain=reason=>({status:'ABSTAIN',reason});
function verifyAudit(t,ctx) {
  try {
    if(!ctx||!Array.isArray(ctx.referenceIds)||!ctx.seed||!ctx.oracleLabels) return abstain('missing independent source');
    const frame=canonical(ctx.referenceIds),manifest=canonical(t.manifestIds);
    if(frame.length!==manifest.length||frame.some((id,i)=>id!==manifest[i])) return abstain('incomplete population frame');
    if(t.seed!==ctx.seed) return abstain('seed not independently authorized');
    const selected=choose(frame,ctx.seed,t.sampleSize),reported=t.reported;
    if(!reported||typeof reported!=='object'||Array.isArray(reported)) return abstain('missing labels');
    if(Object.keys(reported).length!==selected.length||Object.keys(reported).some(id=>!selected.includes(id))) return abstain('label mismatch');
    for(const id of selected) {
      if(![0,1].includes(reported[id])||![0,1].includes(ctx.oracleLabels[id])) return abstain('invalid labels');
      if(reported[id]!==ctx.oracleLabels[id]) return abstain('oracle disagreement');
    }
    const k=selected.reduce((a,id)=>a+reported[id],0),N=frame.length,m=selected.length;
    return {status:'VERIFIED_TRANSCRIPT',audited:m,population:N,observedErrorRate:k/m,
      unconditionalErrorRateBounds:[k/N,(k+N-m)/N],
      note:'Only conditional on trusted independent frame/seed/oracle. Not a confidence interval.'};
  } catch(e) {return abstain('malformed transcript: '+e.message);}
}
const N=300,K=54,M=60,TRIALS=200;
const counts={honestAccepted:0,omittedRejected:0,forgedRejected:0,seedRejected:0,missingRejected:0,
  colludingOracleForgedAccepted:0,colludingFrameOmittedAccepted:0};
let assertions=0;
function check(a,b){assert.equal(a,b);assertions++;}
for(let t=0;t<TRIALS;t++){
  const ids=Array.from({length:N},(_,i)=>'case-'+String(i).padStart(4,'0'));
  const bad=new Set(choose(ids,hash('truth|'+t),K));
  const labels=Object.fromEntries(ids.map(id=>[id,Number(bad.has(id))]));
  const seed=hash('independent-seed-after-commit|'+t),selected=choose(ids,seed,M);
  const reported=Object.fromEntries(selected.map(id=>[id,labels[id]]));
  const ctx={referenceIds:ids,seed,oracleLabels:labels};
  const honest={manifestIds:ids,seed,sampleSize:M,reported};
  const kept=ids.filter(id=>!bad.has(id));
  const omitted={manifestIds:kept,seed,sampleSize:M,reported:Object.fromEntries(choose(kept,seed,M).map(id=>[id,0]))};
  const forged={...honest,reported:Object.fromEntries(selected.map(id=>[id,0]))};
  const swapped={...honest,seed:hash('producer-seed|'+t)};
  const missing={...honest,reported:{...reported}};delete missing.reported[selected[0]];
  check(verifyAudit(honest,ctx).status,'VERIFIED_TRANSCRIPT');counts.honestAccepted++;
  for(const [attack,key] of [[omitted,'omittedRejected'],[forged,'forgedRejected'],
    [swapped,'seedRejected'],[missing,'missingRejected']]){
    check(verifyAudit(attack,ctx).status,'ABSTAIN');counts[key]++;
  }
  const colludingOracle={...ctx,oracleLabels:Object.fromEntries(ids.map(id=>[id,0]))};
  if(verifyAudit(forged,colludingOracle).status==='VERIFIED_TRANSCRIPT')counts.colludingOracleForgedAccepted++;
  if(verifyAudit(omitted,{...ctx,referenceIds:kept}).status==='VERIFIED_TRANSCRIPT')counts.colludingFrameOmittedAccepted++;
}
console.log(JSON.stringify({cycle:243,trials:TRIALS,assertions,counts,
  unconditionalBoundWidth:1-M/N,
  limitations:'All witnesses simulated. No timestamp, external authentication, or independence proof.'},null,2));
export {canonical,choose,verifyAudit};