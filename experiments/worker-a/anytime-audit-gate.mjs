/** Worker A cycle 239 — budgeted anytime audit decision gate.
 * Finite fixed binary-loss ledger; random permutation/SRS without replacement;
 * labels may be withheld arbitrarily, but observed labels must be correct.
 * Familywise error <= alpha for the pre-registered looks, unconditional over
 * original random permutation, by union bound. No conditional guarantee.
 * Node >=18; no dependencies. Research-only synthetic validation.
 */
import assert from 'node:assert/strict';

export function rng(seed) { let a=seed>>>0; return () => { a=(a+0x6D2B79F5)>>>0; let t=a; t=Math.imul(t^(t>>>15),t|1); t^=t+Math.imul(t^(t>>>7),t|61); return ((t^(t>>>14))>>>0)/4294967296; }; }
export function permute(a,random) { const out=[...a]; for(let i=0;i<out.length;i++){const j=i+Math.floor(random()*(out.length-i));[out[i],out[j]]=[out[j],out[i]];} return out; }
function logFactorials(N) { const lf=[0]; for(let i=1;i<=N;i++)lf[i]=lf[i-1]+Math.log(i); return lf; }
function logChoose(N,k,lf) { return k<0||k>N?-Infinity:lf[N]-lf[k]-lf[N-k]; }
function hyperTail(N,K,m,k,upper,lf) {
 const lo=Math.max(0,m-(N-K)),hi=Math.min(m,K);
 if(upper&&k<=lo || !upper&&k>=hi)return 1;
 if(upper&&k>hi || !upper&&k<lo)return 0;
 let sum=0; const start=upper?Math.max(k,lo):lo,end=upper?hi:Math.min(k,hi);
 for(let x=start;x<=end;x++)sum+=Math.exp(logChoose(K,x,lf)+logChoose(N-K,m-x,lf)-logChoose(N,m,lf));
 return Math.min(1,sum);
}
export function exactCountBounds(N,m,k,tail,lf=logFactorials(N)) {
 if(!Number.isInteger(N)||!Number.isInteger(m)||!Number.isInteger(k)||N<1||m<1||m>N||k<0||k>m||!(tail>0&&tail<.5))throw Error('invalid exact bounds');
 if(m===N)return [k,k];
 let a=0,b=N; while(a<b){const mid=Math.floor((a+b)/2);if(hyperTail(N,mid,m,k,true,lf)>=tail)b=mid;else a=mid+1;} const low=a;
 a=0;b=N; while(a<b){const mid=Math.ceil((a+b)/2);if(hyperTail(N,mid,m,k,false,lf)>=tail)a=mid;else b=mid-1;} return [low,a];
}
export function auditInterval(N,sample,alpha=.05,lf=logFactorials(N)) {
 if(!Array.isArray(sample)||sample.length<1||sample.length>N||!(alpha>0&&alpha<1))throw Error('invalid sample/alpha');
 let k=0,u=0;
 for(const x of sample){if(x===1)k++;else if(x===null)u++;else if(x!==0)throw Error('invalid label');}
 const m=sample.length;
 const lo=exactCountBounds(N,m,k,alpha/2,lf)[0];
 const hi=exactCountBounds(N,m,k+u,alpha/2,lf)[1];
 return [lo/N,hi/N];
}
export function decision(interval,threshold) {
 if(!(threshold>=0&&threshold<=1)||interval[0]>interval[1])throw Error('invalid threshold/interval');
 if(interval[1]<=threshold)return 'SAFE';
 if(interval[0]>threshold)return 'UNSAFE';
 return 'ABSTAIN';
}
/** All looks fixed in advance. alpha allocation sums to <= total alpha. */
export function anytimeGate(N,stream,looks=[40,80,120],alpha=.05,threshold=.15) {
 if(!Array.isArray(stream)||!Array.isArray(looks)||!looks.length||!(alpha>0&&alpha<1))throw Error('invalid gate');
 if(looks.some((m,i)=>!Number.isInteger(m)||m<1||m>N||m>stream.length||(i>0&&m<=looks[i-1])))throw Error('invalid looks');
 if(!(threshold>=0&&threshold<=1))throw Error('invalid threshold');
 const lf=logFactorials(N),perLook=alpha/looks.length;
 const history=[];
 for(const m of looks){const ci=auditInterval(N,stream.slice(0,m),perLook,lf);const d=decision(ci,threshold);history.push({m,interval:ci,decision:d});if(d!=='ABSTAIN')return {decision:d,used:m,history};}
 return {decision:'ABSTAIN',used:looks.at(-1),history};
}
function makePopulation(N,p,seed) { const K=Math.round(N*p);return permute(Array.from({length:N},(_,i)=>Number(i<K)),rng(seed)); }
function hide(labels,mode,r) {return labels.map(y=>{let p=0;if(mode==='mcar')p=.25;if(mode==='mnar')p=y===1?.80:.08;return r()<p?null:y;});}
export function benchmark({trials=200,seed=239000,N=300,looks=[40,80,120]}={}) {
 const results=[];const threshold=.15;
 for(const p of [.03,.12,.18,.32])for(const mode of ['complete','mcar','mnar']){
  let safe=0,unsafe=0,abstain=0,wrong=0,naiveWrong=0,used=0,missing=0;
  for(let t=0;t<trials;t++){
   const pop=makePopulation(N,p,seed+100000*t+Math.round(p*100));
   const stream=hide(permute(pop,rng(seed+100000*t+31337)),mode,rng(seed+100000*t+7331));
   const truth=pop.reduce((s,v)=>s+v,0)/N;
   const g=anytimeGate(N,stream,looks,.05,threshold);
   safe+=Number(g.decision==='SAFE');unsafe+=Number(g.decision==='UNSAFE');abstain+=Number(g.decision==='ABSTAIN');used+=g.used;
   wrong+=Number(g.decision==='SAFE'&&truth>threshold||g.decision==='UNSAFE'&&truth<=threshold);
   const observed=stream.slice(0,looks.at(-1)).filter(x=>x!==null);
   const naive=observed.reduce((s,x)=>s+x,0)/Math.max(1,observed.length)<=threshold?'SAFE':'UNSAFE';
   naiveWrong+=Number(naive==='SAFE'&&truth>threshold||naive==='UNSAFE'&&truth<=threshold);
   missing+=1-observed.length/looks.at(-1);
  }
  results.push({p,mode,trials,safe,unsafe,abstain,wrong,naiveWrong,meanUsed:+(used/trials).toFixed(1),meanMissing:+(100*missing/trials).toFixed(1)});
 }
 return results;
}
function combinations(a,k){if(k===0)return [[]];if(a.length<k)return [];return [...combinations(a.slice(1),k-1).map(v=>[a[0],...v]),...combinations(a.slice(1),k)];}
export function selfTest(){let count=0;const check=(x,msg)=>{assert(x,msg);count++;};
 // Exhaustive fixed-population coverage, all binary populations N<=8, all SRS sample sizes.
 for(let N=2;N<=8;N++)for(let m=1;m<=N;m++)for(let K=0;K<=N;K++){
  const lf=logFactorials(N);let covered=0;
  for(let k=Math.max(0,m-(N-K));k<=Math.min(m,K);k++){
   const [L,U]=exactCountBounds(N,m,k,.025,lf);
   if(L<=K&&K<=U)covered+=Math.exp(logChoose(K,k,lf)+logChoose(N-K,m-k,lf)-logChoose(N,m,lf));
  }check(covered>=.95-1e-9,'exact design coverage');
 }
 // Withholding any subset of labels must widen (or preserve) exact full-data interval.
 for(let N=2;N<=6;N++)for(let K=0;K<=N;K++){
  const pop=Array.from({length:N},(_,i)=>Number(i<K));
  for(let m=1;m<=N;m++)for(const sample of combinations(pop,m)){
   const full=auditInterval(N,sample);
   for(let mask=0;mask<(1<<m);mask++){
    const partial=sample.map((x,i)=>mask&(1<<i)?null:x),ci=auditInterval(N,partial);
    check(ci[0]<=full[0]+1e-10&&ci[1]+1e-10>=full[1],'missing monotonicity');
   }
  }
 }
 check(decision([0,.1],.15)==='SAFE','safe');check(decision([.2,.4],.15)==='UNSAFE','unsafe');check(decision([.1,.2],.15)==='ABSTAIN','abstain');
 check(anytimeGate(200,Array(120).fill(null)).decision==='ABSTAIN','all missing abstains');
 for(const looks of [[40,40],[0,50],[50,301]])assert.throws(()=>anytimeGate(300,Array(300).fill(0),looks));
 return count;
}
if(import.meta.url===`file://${process.argv[1]}`){console.log(JSON.stringify({assertions:selfTest(),results:benchmark()},null,2));}
