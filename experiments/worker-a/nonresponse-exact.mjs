/** Worker A cycle 238 — finite-population audit CI with arbitrary audit nonresponse.
 * Pure Node >=18, no dependencies. Synthetic experiments only.
 * Population: fixed N rows, each with known proxy in {0,1} and unknown true loss in {0,1}.
 * SRS without replacement selects m rows; any selected label may be withheld by any mechanism.
 * Conditional on fixed population and honest labels when observed, the returned interval has
 * at least 1-alpha coverage over the original SRS draw, even under adversarial nonresponse.
 * IMPORTANT: Not a conditional guarantee given observed response pattern or selected sample.
 */
import assert from 'node:assert/strict';

export function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}
export function sampleSRS(rows,m,r){assert(Number.isInteger(m)&&m>=1&&m<=rows.length);const a=[...rows];for(let i=0;i<m;i++){const j=i+Math.floor(r()*(a.length-i));[a[i],a[j]]=[a[j],a[i]]}return a.slice(0,m)}
function logFactorials(n){const a=[0];for(let i=1;i<=n;i++)a[i]=a[i-1]+Math.log(i);return a}
function logChoose(n,k,lf){return k<0||k>n?-Infinity:lf[n]-lf[k]-lf[n-k]}
function hyperTail(N,K,m,k,upper,lf){const lo=Math.max(0,m-(N-K)),hi=Math.min(m,K);if(upper&&k<=lo)return 1;if(!upper&&k>=hi)return 1;if(upper&&k>hi)return 0;if(!upper&&k<lo)return 0;let sum=0;for(let x=upper?Math.max(k,lo):lo;x<=(upper?hi:Math.min(k,hi));x++)sum+=Math.exp(logChoose(K,x,lf)+logChoose(N-K,m-x,lf)-logChoose(N,m,lf));return Math.min(1,sum)}
export function exactCountBounds(N,m,k,alphaTail,lf=logFactorials(N)){
 if(!Number.isInteger(N)||!Number.isInteger(m)||!Number.isInteger(k)||N<1||m<1||m>N||k<0||k>m||!(alphaTail>0&&alphaTail<.5))throw Error('invalid hypergeom arguments');
 if(m===N)return[k,k];
 let low=0,high=N;
 while(low<high){const mid=Math.floor((low+high)/2);if(hyperTail(N,mid,m,k,true,lf)>=alphaTail)high=mid;else low=mid+1}
 const L=low;low=0;high=N;
 while(low<high){const mid=Math.ceil((low+high)/2);if(hyperTail(N,mid,m,k,false,lf)>=alphaTail)low=mid;else high=mid-1}
 return [L,low];
}
export function nonresponseInterval(ledger,sample,alpha=.05){
 const N=ledger.length,m=sample.length;
 if(!N||!m||m>N||!(alpha>0&&alpha<1))throw Error('invalid sizes');
 const proxyById=new Map(ledger.map(x=>[x.id,x.proxy]));
 if(proxyById.size!==N||ledger.some(x=>x.proxy!==0&&x.proxy!==1))throw Error('invalid ledger');
 let p=0,n=0,miss0=0,miss1=0;
 const seen=new Set();
 for(const x of sample){
  if(!proxyById.has(x.id)||seen.has(x.id)||x.proxy!==proxyById.get(x.id))throw Error('invalid sample');
  seen.add(x.id);
  if(x.loss===null){if(x.proxy===0)miss0++;else miss1++}
  else if(x.loss===0||x.loss===1){if(x.loss===1&&x.proxy===0)p++;if(x.loss===0&&x.proxy===1)n++}
  else throw Error('invalid loss');
 }
 const proxy=ledger.reduce((s,x)=>s+x.proxy,0)/N;
 // Union bound: two signs x two tails. Each marginal one-sided error <= alpha/4.
 const lf=logFactorials(N),tail=alpha/4;
 const [posLo]=exactCountBounds(N,m,p,tail,lf);
 const [,posHi]=exactCountBounds(N,m,p+miss0,tail,lf);
 const [negLo]=exactCountBounds(N,m,n,tail,lf);
 const [,negHi]=exactCountBounds(N,m,n+miss1,tail,lf);
 const lo=Math.max(0,proxy+(posLo-negHi)/N),hi=Math.min(1,proxy+(posHi-negLo)/N);
 if(lo>hi+1e-12)throw Error('interval inconsistent');
 return {interval:[lo,hi],width:hi-lo,responded:m-miss0-miss1,missing:miss0+miss1,proxy,unknownResidual:[-miss1,miss0],tail};
}
/** Direct binary-loss interval under arbitrary response, no proxy assumptions. */
export function directLossInterval(N,sample,alpha=.05){
 const m=sample.length;
 if(!Number.isInteger(N)||N<1||m<1||m>N||!(alpha>0&&alpha<1))throw Error('invalid direct interval');
 let positives=0,unknown=0;
 for(const x of sample){if(x.loss===null)unknown++;else if(x.loss===1)positives++;else if(x.loss!==0)throw Error('invalid loss')}
 const lf=logFactorials(N),lo=exactCountBounds(N,m,positives,alpha/2,lf)[0],hi=exactCountBounds(N,m,positives+unknown,alpha/2,lf)[1];
 return [lo/N,hi/N];
}
/** Intersect two individually 97.5%-valid intervals to obtain >=95% coverage. */
export function hybridInterval(ledger,sample,alpha=.05){
 const residual=nonresponseInterval(ledger,sample,alpha/2).interval;
 const direct=directLossInterval(ledger.length,sample,alpha/2);
 const lower=Math.max(residual[0],direct[0]),upper=Math.min(residual[1],direct[1]);
 if(lower>upper+1e-10)throw Error('contradictory interval (check ledger or numerical stability)');
 return {interval:[lower,upper],width:upper-lower,residual,direct};
}
function makePopulation(seed,N=400){const r=rng(seed),rows=[];for(let i=0;i<N;i++){
 const loss=Number(r()<.12),shared=r()<.11;
 const votes=Array.from({length:3},()=>shared?1-loss:loss^Number(r()<.12));
 const proxy=Number(votes.reduce((a,b)=>a+b,0)>=2);
 rows.push({id:i,loss,proxy});
 }return rows;
}
function mask(sample,mode,r){return sample.map(x=>{
 let prob=0;
 if(mode==='complete')prob=0;
 if(mode==='mcar')prob=.30;
 if(mode==='mnar')prob=x.loss===1?.75:.12;
 if(mode==='adversarial')prob=(x.loss!==x.proxy)? .95:.08;
 return {...x,loss:r()<prob?null:x.loss};
})}
function naiveRespondentCI(sample){const a=sample.filter(x=>x.loss!==null);if(!a.length)return [0,1];const mean=a.reduce((s,x)=>s+x.loss,0)/a.length;const se=Math.sqrt(mean*(1-mean)/a.length);return [Math.max(0,mean-1.96*se),Math.min(1,mean+1.96*se)]}
export function benchmark(mode,trials=200,seed=238000){let coverage=0,naiveCoverage=0,width=0,hybridCoverage=0,hybridWidth=0,missing=0,pointAbs=0;for(let t=0;t<trials;t++){
 const rows=makePopulation(seed+t),truth=rows.reduce((s,x)=>s+x.loss,0)/rows.length;
 const sample=sampleSRS(rows,60,rng(seed+1000000+t));
 const observed=mask(sample,mode,rng(seed+2000000+t));
 const v=nonresponseInterval(rows.map(x=>({id:x.id,proxy:x.proxy})),observed);
 const naive=naiveRespondentCI(observed);
 const h=hybridInterval(rows.map(x=>({id:x.id,proxy:x.proxy})),observed);
 hybridCoverage+=Number(h.interval[0]-1e-12<=truth&&truth<=h.interval[1]+1e-12);hybridWidth+=h.width;
 coverage+=Number(v.interval[0]-1e-12<=truth&&truth<=v.interval[1]+1e-12);
 naiveCoverage+=Number(naive[0]<=truth&&truth<=naive[1]);
 width+=v.width;missing+=v.missing/60;
 pointAbs+=Math.abs(observed.filter(x=>x.loss!==null).reduce((s,x)=>s+x.loss,0)/Math.max(1,v.responded)-truth);
 }return {mode,trials,exactCoverage:Number((100*coverage/trials).toFixed(2)),naiveCoverage:Number((100*naiveCoverage/trials).toFixed(2)),meanExactWidthPP:Number((100*width/trials).toFixed(2)),hybridCoverage:Number((100*hybridCoverage/trials).toFixed(2)),meanHybridWidthPP:Number((100*hybridWidth/trials).toFixed(2)),meanMissingPercent:Number((100*missing/trials).toFixed(2)),naiveMAEPP:Number((100*pointAbs/trials).toFixed(2))};}
function chooseAll(a,k){if(!k)return [[]];if(a.length<k)return [];return [...chooseAll(a.slice(1),k-1).map(s=>[a[0],...s]),...chooseAll(a.slice(1),k)]}
export function selfTest(){let assertions=0;const check=(v,msg)=>{assert(v,msg);assertions++};
 // Exhaustively verify design coverage for all binary populations N=2..6 and every SRS sample size.
 for(let N=2;N<=6;N++)for(let m=1;m<=N;m++)for(let K=0;K<=N;K++){
  const lf=logFactorials(N);let coverage=0;
  for(let k=0;k<=m;k++){
   const [L,U]=exactCountBounds(N,m,k,.0125,lf);
   if(L<=K&&K<=U)coverage+=Math.exp(logChoose(K,k,lf)+logChoose(N-K,m-k,lf)-logChoose(N,m,lf));
  }check(coverage>=.975-1e-10,'one binary count two-sided coverage');
 }
 // Every response mask on every possible sample must contain the full-label CI, regardless of withholding mechanism.
 for(let N=2;N<=5;N++)for(let maskP=0;maskP<(1<<N);maskP++)for(let maskY=0;maskY<(1<<N);maskY++){
  const rows=Array.from({length:N},(_,i)=>({id:i,proxy:(maskP>>i)&1,loss:(maskY>>i)&1}));
  const ledger=rows.map(({id,proxy})=>({id,proxy}));
  for(let m=1;m<=N;m++)for(const drawn of chooseAll(rows,m)){
   const full=nonresponseInterval(ledger,drawn).interval;
   for(let withheld=0;withheld<(1<<m);withheld++){
    const observed=drawn.map((x,i)=>({...x,loss:(withheld>>i)&1?null:x.loss}));
    const partial=nonresponseInterval(ledger,observed).interval;
    check(partial[0]<=full[0]+1e-10&&partial[1]+1e-10>=full[1],'partial must contain full interval');
    const hFull=hybridInterval(ledger,drawn).interval,hPartial=hybridInterval(ledger,observed).interval;
    check(hPartial[0]<=hFull[0]+1e-10&&hPartial[1]+1e-10>=hFull[1],'hybrid partial must contain hybrid full');
   }
  }
 }
 const ledger=[{id:0,proxy:0},{id:1,proxy:1}];
 const census=nonresponseInterval(ledger,[{id:0,proxy:0,loss:1},{id:1,proxy:1,loss:0}]);
 check(census.interval[0]===.5&&census.interval[1]===.5,'census');
 const blind=nonresponseInterval(ledger,[{id:0,proxy:0,loss:null},{id:1,proxy:1,loss:null}]);
 check(blind.interval[0]===0&&blind.interval[1]===1,'full missing census');
 return assertions;
}
if(import.meta.url===`file://${process.argv[1]}`){const tests=selfTest();const results=['complete','mcar','mnar','adversarial'].flatMap(mode=>[benchmark(mode,200,238000),benchmark(mode,200,9238000)]);console.log(JSON.stringify({assertions:tests,results},null,2));}
