/** Worker A cycle 237: exact finite-population design-based audit CIs.
 * Hypergeometric inversion for positive and negative residual counts;
 * Bonferroni over both tails, both signs and all strata.
 * Conditional 1-alpha coverage under SRS without replacement in each
 * observable stratum, complete accurate independent labels, fixed ledger.
 * No validity guarantee under audit nonresponse or inaccurate gold labels.
 * Node >=18; zero dependencies. Synthetic data only. */
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}

function choose(items,m,r){if(m<0||m>items.length)throw Error("sample");const a=[...items];for(let i=0;i<m;i++){const j=i+Math.floor(r()*(a.length-i));[a[i],a[j]]=[a[j],a[i]]}return a.slice(0,m)}

function logFactorials(n){const a=[0];for(let i=1;i<=n;i++)a[i]=a[i-1]+Math.log(i);return a}

function logChoose(n,k,lf){return k<0||k>n?-Infinity:lf[n]-lf[k]-lf[n-k]}

function hyperTail(N,K,m,k,upper,lf){const lo=Math.max(0,m-(N-K)),hi=Math.min(m,K);if(upper&&k<=lo)return 1;if(!upper&&k>=hi)return 1;if(upper&&k>hi)return 0;if(!upper&&k<lo)return 0;let sum=0;for(let x=upper?Math.max(k,lo):lo;x<=(upper?hi:Math.min(k,hi));x++)sum+=Math.exp(logChoose(K,x,lf)+logChoose(N-K,m-x,lf)-logChoose(N,m,lf));return Math.min(1,sum)}

function exactCountBounds(N,m,k,alphaTail,lf){if(!Number.isInteger(N)||!Number.isInteger(m)||!Number.isInteger(k)||N<1||m<1||m>N||k<0||k>m||!(alphaTail>0&&alphaTail<.5))throw Error("bad count");if(m===N)return[k,k];let low=0,high=N;while(low<high){const mid=Math.floor((low+high)/2);if(hyperTail(N,mid,m,k,true,lf)>=alphaTail)high=mid;else low=mid+1}const L=low;low=0;high=N;while(low<high){const mid=Math.ceil((low+high)/2);if(hyperTail(N,mid,m,k,false,lf)>=alphaTail)low=mid;else high=mid-1}return[L,low]}

function population(seed,mode,N=500){const r=rng(seed),rows=[];for(let id=0;id<N;id++){const loss=Number(r()<.12),shared=mode==="shared"&&r()<.12,masked=mode==="asymmetric"&&loss===1&&r()<.70;const votes=Array.from({length:3},()=>shared?1-loss:masked?0:loss^Number(r()<.12));const proxy=Number(votes.reduce((a,b)=>a+b,0)>=2);rows.push({id,loss,proxy,disagree:Number(!(votes[0]===votes[1]&&votes[1]===votes[2]))})}return rows}

function auditPlan(rows,seed,policy="uniform",budget=50){if(!["uniform","targeted"].includes(policy))throw Error("policy");const r=rng(seed);let strata;if(policy==="uniform")strata=[{rows,m:budget}];else{const hi=rows.filter(x=>x.disagree),lo=rows.filter(x=>!x.disagree);if(!hi.length||!lo.length)strata=[{rows,m:budget}];else{const mh=Math.min(hi.length,budget-1,Math.max(1,budget-lo.length,35)),ml=budget-mh;strata=[{rows:hi,m:mh},{rows:lo,m:ml}]}}return strata.map(s=>({N:s.rows.length,m:s.m,sample:choose(s.rows,s.m,r)}))}

function auditEstimate(rows,plan,alpha=.05){const N=rows.length,proxy=rows.reduce((a,x)=>a+x.proxy,0)/N;let estimate=proxy,lo=proxy,hi=proxy,variance=0;const lf=logFactorials(N),tail=alpha/(4*plan.length);for(const s of plan){const residuals=s.sample.map(x=>x.loss-x.proxy),sum=residuals.reduce((a,x)=>a+x,0);estimate+=s.N/N*sum/s.m;const pos=residuals.filter(x=>x===1).length,neg=residuals.filter(x=>x===-1).length;const [lp,up]=exactCountBounds(s.N,s.m,pos,tail,lf),[ln,un]=exactCountBounds(s.N,s.m,neg,tail,lf);lo+=(lp-un)/N;hi+=(up-ln)/N;const sampleVar=s.m>1?residuals.reduce((a,x)=>a+(x-sum/s.m)**2,0)/(s.m-1):0;variance+=(s.N/N)**2*(1-s.m/s.N)*sampleVar/s.m}return{estimate,exact:[Math.max(0,lo),Math.min(1,hi)],normal:[Math.max(0,estimate-1.96*Math.sqrt(variance)),Math.min(1,estimate+1.96*Math.sqrt(variance))]}}

function benchmark(mode,trials,seed){let a={uniform:{mae:0,coverage:0,normalCoverage:0,width:0},targeted:{mae:0,coverage:0,normalCoverage:0,width:0}};for(let i=0;i<trials;i++){const rows=population(seed+i,mode),truth=rows.reduce((x,r)=>x+r.loss,0)/rows.length;for(const policy of ["uniform","targeted"]){const v=auditEstimate(rows,auditPlan(rows,seed+i+1000000,policy));const z=a[policy];z.mae+=Math.abs(v.estimate-truth);z.coverage+=Number(v.exact[0]-1e-12<=truth&&truth<=v.exact[1]+1e-12);z.normalCoverage+=Number(v.normal[0]-1e-12<=truth&&truth<=v.normal[1]+1e-12);z.width+=v.exact[1]-v.exact[0]}}for(const p of Object.keys(a))for(const k of Object.keys(a[p]))a[p][k]=Number((100*a[p][k]/trials).toFixed(3));return{mode,trials,seed,...a}}

function selfTest(){let n=0;const assert=(v,msg)=>{if(!v)throw Error(msg);n++};for(let N=2;N<=7;N++)for(let m=1;m<=N;m++)for(let K=0;K<=N;K++){const lf=logFactorials(N);for(let k=0;k<=m;k++){const [L,U]=exactCountBounds(N,m,k,.025,lf);assert(L<=U&&L>=0&&U<=N,"bounds order")}let cover=0;for(let k=0;k<=m;k++){const [L,U]=exactCountBounds(N,m,k,.025,lf);if(L<=K&&K<=U)cover+=Math.exp(logChoose(K,k,lf)+logChoose(N-K,m-k,lf)-logChoose(N,m,lf))}assert(cover>=.95-1e-10,"exact hypergeometric coverage")}const rows=population(2,"shared");for(const p of ["uniform","targeted"]){const a=auditPlan(rows,3,p),b=auditEstimate(rows,a);assert(a.reduce((s,x)=>s+x.m,0)===50,"budget");assert(b.exact[0]<=b.exact[1],"risk order")}const census=auditEstimate(rows,[{N:rows.length,m:rows.length,sample:rows}]);assert(Math.abs(census.estimate-rows.reduce((s,x)=>s+x.loss,0)/rows.length)<1e-12,"census exact");assert(Math.abs(census.exact[0]-census.exact[1])<1e-12,"census interval");return n}
if(typeof process!=="undefined" && process.argv[1]?.endsWith("exact-audit-ci.mjs")) {
  console.log(JSON.stringify({assertions:selfTest(),results:["independent","shared","asymmetric"].map(mode=>benchmark(mode,240,237000))},null,2));
}
