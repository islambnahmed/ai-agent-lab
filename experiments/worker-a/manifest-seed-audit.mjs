/** Worker A cycle 242: synthetic sampling-integrity protocol and adversarial tests.
 * Node >=18, standard library only. No production timestamping or external witness.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const sha = s => createHash('sha256').update(s).digest('hex');
const rank = (seed, id) => sha(`audit-v1\0${seed}\0${id}`);

function canonicalIds(ids) {
  if (!Array.isArray(ids) || ids.some(x => typeof x !== 'string' || !x.length)) throw Error('invalid IDs');
  const sorted = [...ids].sort();
  if (new Set(sorted).size !== sorted.length) throw Error('duplicate IDs');
  return sorted;
}
function commitment(ids) {
  const sorted = canonicalIds(ids);
  return sha(`manifest-v1\0${JSON.stringify(sorted)}`);
}
function sample(ids, seed, m) {
  const sorted = canonicalIds(ids);
  if (!Number.isInteger(m) || m < 1 || m > sorted.length || !/^[a-f0-9]{64}$/.test(seed)) throw Error('bad sample parameters');
  return sorted.map(id => [rank(seed, id), id]).sort((a,b) => a[0].localeCompare(b[0]) || a[1].localeCompare(b[1])).slice(0,m).map(x=>x[1]);
}
function verify({ids, seed, m, reported}, independentlyRetrievedWitness) {
  try {
  if (!independentlyRetrievedWitness || independentlyRetrievedWitness.commitment !== commitment(ids)) return {ok:false,reason:'manifest mismatch or absent independent witness'};
  if (seed !== independentlyRetrievedWitness.seed) return {ok:false,reason:'seed mismatch'};
  const selected = sample(ids, seed, m);
  const keys = Object.keys(reported);
  if (keys.length !== m || selected.some(id => !(id in reported) || ![0,1].includes(reported[id]))) return {ok:false,reason:'missing/invalid audit outcomes'};
  if (keys.some(id=>!selected.includes(id))) return {ok:false,reason:'extra outcomes'};
  const errors = selected.reduce((s,id)=>s+reported[id],0);
  return {ok:true,errors,rate:errors/m,selected};
  } catch { return {ok:false,reason:'malformed transcript'}; }
}
function truthForTrial(ids, trial, badCount) {
  const bad = new Set(sample(ids,sha(`truth-v1|${trial}`),badCount));
  return Object.fromEntries(ids.map(id=>[id,Number(bad.has(id))]));
}
const N=300,K=54,M=60,TRIALS=200,GRIND=64;
const ids=Array.from({length:N},(_,i)=>`case-${String(i).padStart(4,'0')}`);
const mean = a => a.reduce((x,y)=>x+y,0)/a.length;

// Unit/invariant checks, with independently supplied witness fixture.
const seed=sha('postcommit-seed'), witness={commitment:commitment(ids),seed};
const chosen=sample(ids,seed,M), outcomes=Object.fromEntries(chosen.map((id,i)=>[id,i%2]));
assert.deepEqual(sample([...ids].reverse(),seed,M),chosen,'manifest order must not affect sample');
assert.equal(verify({ids,seed,m:M,reported:outcomes},witness).ok,true);
assert.equal(verify({ids:[...ids.slice(1),'substitute'],seed,m:M,reported:outcomes},witness).ok,false);
assert.equal(verify({ids,seed:sha('seed swapped'),m:M,reported:outcomes},witness).ok,false);
const missing={...outcomes}; delete missing[chosen[0]];
assert.equal(verify({ids,seed,m:M,reported:missing},witness).ok,false);
assert.throws(()=>commitment([...ids,ids[0]]),/duplicate/);
assert.throws(()=>sample(ids,'bad',M),/bad sample/);
assert.equal(verify({ids,seed,m:M,reported:outcomes},null).ok,false);
assert.equal(verify({ids,seed:'bad',m:M,reported:outcomes},witness).ok,false);
assert.equal(verify({ids,seed,m:M,reported:null},witness).ok,false);

const honest=[],grinded=[],alteredAccepted=[],omittedAccepted=[];
for(let t=0;t<TRIALS;t++) {
  const truth=truthForTrial(ids,t,K);
  const honestSeed=sha(`unpredictable-after-commit|${t}`);
  const honestSelected=sample(ids,honestSeed,M);
  const w={commitment:commitment(ids),seed:honestSeed};
  const report=Object.fromEntries(honestSelected.map(id=>[id,truth[id]]));
  const result=verify({ids,seed:honestSeed,m:M,reported:report},w);
  assert.equal(result.ok,true);
  honest.push(result.rate);
  let best=1;
  for(let j=0;j<GRIND;j++) {
    const picked=sample(ids,sha(`adversary-picks-seed|${t}|${j}`),M);
    best=Math.min(best,picked.reduce((s,id)=>s+truth[id],0)/M);
  }
  grinded.push(best);
  // Even a valid post-commit seed cannot detect a population truncated BEFORE commitment.
  const cleaned=ids.filter(id=>truth[id]===0);
  const cleanSeed=sha(`cleaned|${t}`), cleanSample=sample(cleaned,cleanSeed,M);
  const cleanReport=Object.fromEntries(cleanSample.map(id=>[id,0]));
  omittedAccepted.push(verify({ids:cleaned,seed:cleanSeed,m:M,reported:cleanReport},{commitment:commitment(cleaned),seed:cleanSeed}).ok);
  // Outcome truthfulness cannot be proved by a manifest of IDs.
  const forged=Object.fromEntries(honestSelected.map(id=>[id,0]));
  alteredAccepted.push(verify({ids,seed:honestSeed,m:M,reported:forged},w).ok);
}
const summary={cycle:242,experiment:'Synthetic witness-before-seed sampling integrity',N,K,M,trials:TRIALS,seedsPerGrindingTrial:GRIND,trueErrorRate:K/N,honestMean:mean(honest),seedGrindingMean:mean(grinded),seedGrindingReductionPoints:100*(mean(honest)-mean(grinded)),postcommitSubstitutionRejected:true,seedSubstitutionRejected:true,missingOutcomesRejected:true,precommitOmissionAccepted:omittedAccepted.filter(Boolean).length,forgedOutcomeLabelsAccepted:alteredAccepted.filter(Boolean).length,scope:'synthetic only; independent witness and label authenticity are assumed, not implemented'};
console.log(JSON.stringify(summary,null,2));
export {canonicalIds,commitment,sample,verify};
