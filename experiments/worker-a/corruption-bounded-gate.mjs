/** Worker A cycle 240 — robust finite-population audit gate.
 * Precondition: uniformly random initial permutation without replacement,
 * fixed N, fixed looks, and at most B incorrect observed labels across the
 * entire audit (arbitrary adversarial flips permitted). Missing labels may
 * depend arbitrarily on truth. The B assumption must be externally justified.
 * No validity under preferential/nonuniform sampling.
 */
import assert from 'node:assert/strict';
import {exactCountBounds, decision} from './anytime-audit-gate.mjs';

export function corruptionBoundedInterval(N, sample, B, alpha=.05) {
  if (!Number.isInteger(N) || N<1 || !Array.isArray(sample) || sample.length<1 || sample.length>N ||
      !Number.isInteger(B) || B<0 || !(alpha>0 && alpha<1)) throw Error('invalid interval inputs');
  let k=0,u=0;
  for(const x of sample) {if(x===1) k++; else if(x===null) u++; else if(x!==0) throw Error('invalid label');}
  const m=sample.length;
  // True sampled error count is between max(0,k-B) and min(m,k+u+B).
  const lower=exactCountBounds(N,m,Math.max(0,k-B),alpha/2)[0];
  const upper=exactCountBounds(N,m,Math.min(m,k+u+B),alpha/2)[1];
  return [lower/N,upper/N];
}

export function corruptionBoundedGate(N,stream,{looks=[40,80,120],alpha=.05,threshold=.15,B=6}={}) {
  if(!Array.isArray(stream) || !Array.isArray(looks) || !looks.length || !(alpha>0 && alpha<1) ||
     !(threshold>=0 && threshold<=1) || !Number.isInteger(B) || B<0 ||
     looks.some((m,i)=>!Number.isInteger(m)||m<1||m>N||m>stream.length||(i>0&&m<=looks[i-1]))) throw Error('invalid gate inputs');
  const history=[];
  for(const m of looks){
    const interval=corruptionBoundedInterval(N,stream.slice(0,m),B,alpha/looks.length);
    const result=decision(interval,threshold);
    history.push({m,interval,decision:result});
    if(result!=='ABSTAIN')return {decision:result,used:m,history};
  }
  return {decision:'ABSTAIN',used:looks.at(-1),history};
}

function choose(arr,k){if(!k)return [[]];if(arr.length<k)return [];return [...choose(arr.slice(1),k-1).map(x=>[arr[0],...x]),...choose(arr.slice(1),k)];}
export function selfTest(){
  let assertions=0;
  for(let N=2;N<=7;N++)for(let K=0;K<=N;K++)for(let m=1;m<=N;m++){
    const pop=Array.from({length:N},(_,i)=>Number(i<K));
    for(const sample of choose(pop,m)){
      const full=corruptionBoundedInterval(N,sample,0);
      for(let B=0;B<=Math.min(2,m);B++){
        // All possible flips of up to B returned labels; arbitrary hiding.
        for(let mask=0;mask<(1<<m);mask++){
          if(mask.toString(2).replaceAll('0','').length>B)continue;
          const corrupt=sample.map((v,i)=>mask&(1<<i)?1-v:v);
          const ci=corruptionBoundedInterval(N,corrupt,B);
          assert(ci[0]<=full[0]+1e-12 && ci[1]+1e-12>=full[1]);assertions++;
          const hidden=corrupt.map((v,i)=>i%3===0?null:v);
          const ci2=corruptionBoundedInterval(N,hidden,B);
          assert(ci2[0]<=full[0]+1e-12 && ci2[1]+1e-12>=full[1]);assertions++;
        }
      }
    }
  }
  assert.equal(corruptionBoundedGate(300,Array(120).fill(null)).decision,'ABSTAIN');assertions++;
  for(const bad of [-1,1.5])assert.throws(()=>corruptionBoundedInterval(10,[1],bad));
  assertions+=2;
  return assertions;
}
if(process.argv[1]?.endsWith('/corruption-bounded-gate.mjs'))console.log(JSON.stringify({assertions:selfTest()}));
