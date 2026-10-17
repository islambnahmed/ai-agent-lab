/** Khepri exp248: paired MAE comparison under overlapping future-label windows.
 * Synthetic null: equally uninformative forecasts +c and -c of a symmetric
 * h-step cumulative shock. Never interpret as empirical gold performance.
 */
export function rng(seed=1){
  let x=seed>>>0; if(!x) x=0x6d2b79f5;
  return ()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296};
}
export function normalGenerator(seed=1){
  const u=rng(seed);let spare=null;
  return ()=>{if(spare!==null){const v=spare;spare=null;return v;}
    const a=Math.max(1e-12,u()),b=u(),r=Math.sqrt(-2*Math.log(a));
    spare=r*Math.sin(2*Math.PI*b);return r*Math.cos(2*Math.PI*b);
  };
}
export function pairedLossDifferentials({n=300,h=30,seed=1,phi=0,c=0.5}={}){
  if(!Number.isInteger(n)||n<30||!Number.isInteger(h)||h<1||h>n||!Number.isFinite(phi)||Math.abs(phi)>=1||!Number.isFinite(c)||c<=0)throw Error('Invalid experiment settings');
  const z=normalGenerator(seed),returns=[];let prev=0;
  for(let i=0;i<n+h-1;i++){
    // stationary unit-variance AR(1) innovations; phi=0 is independent shocks
    prev=phi*prev+Math.sqrt(1-phi*phi)*z();returns.push(prev);
  }
  let sum=0;for(let i=0;i<h;i++)sum+=returns[i];
  const d=[];
  for(let i=0;i<n;i++){
    const target=sum/Math.sqrt(h);
    d.push(Math.abs(target-c)-Math.abs(target+c));
    if(i<n-1)sum+=returns[i+h]-returns[i];
  }
  return d;
}
export function auditPairedDifference(d,{bandwidth=0}={}){
  if(!Array.isArray(d)||d.length<30||d.some(x=>!Number.isFinite(x))||!Number.isInteger(bandwidth)||bandwidth<0||bandwidth>=d.length)throw Error('Invalid paired differences or bandwidth');
  const n=d.length,mean=d.reduce((a,b)=>a+b,0)/n;
  const centered=d.map(v=>v-mean);
  const gamma=k=>{let s=0;for(let t=k;t<n;t++)s+=centered[t]*centered[t-k];return s/n;};
  const g0=gamma(0);
  let longRun=g0;
  for(let k=1;k<=bandwidth;k++)longRun+=2*(1-k/(bandwidth+1))*gamma(k);
  const se=Math.sqrt(Math.max(0,longRun)/n);
  const ci=[mean-1.96*se,mean+1.96*se];
  return {n,mean,bandwidth,se,ci,excludesZero:ci[0]>0||ci[1]<0,effectiveN:g0>0&&longRun>0?n*g0/longRun:null};
}
const tCritical95=[null,12.706,4.303,3.182,2.776,2.571,2.447,2.365,2.306,2.262,2.228,2.201,2.179,2.160,2.145,2.131,2.120,2.110,2.101,2.093,2.086,2.080,2.074,2.069,2.064,2.060,2.056,2.052,2.048,2.045,2.042];
export function disjointPhaseAudit(d,h,offset=0){
  if(!Array.isArray(d)||!Number.isInteger(h)||h<1||!Number.isInteger(offset)||offset<0||offset>=h)throw Error('Invalid phase audit');
  const xs=d.filter((_,i)=>i%h===offset),n=xs.length;
  if(n<3)throw Error('Too few disjoint observations');
  const mean=xs.reduce((a,b)=>a+b,0)/n;
  const sampleVariance=xs.reduce((s,x)=>s+(x-mean)**2,0)/(n-1);
  const se=Math.sqrt(sampleVariance/n),df=n-1;
  // tabulated exact t critical for small df; large-df Cornish-Fisher expansion.
  const z=1.959963984540054,critical=df<=30?tCritical95[df]:z+(z**3+z)/(4*df)+(5*z**5+16*z**3+3*z)/(96*df**2);
  const ci=[mean-critical*se,mean+critical*se];
  return {n,mean,offset,h,ci,se,excludesZero:ci[0]>0||ci[1]<0,
    caveat:'Disjoint labels do not guarantee independent loss differentials when source shocks are autocorrelated.'};
}
export function runMonteCarlo({replications=600,n=300,h=30,phi=0,seed=14001}={}){
  if(!Number.isInteger(replications)||replications<1||replications>20000)throw Error('Invalid replications');
  const widths=[0,Math.min(n-1,h-1),Math.min(n-1,2*h-1)];
  const counts=widths.map(()=>0),seSum=widths.map(()=>0),effSum=widths.map(()=>0);let disjointFalse=0;
  for(let r=0;r<replications;r++){
    const d=pairedLossDifferentials({n,h,phi,seed:seed+r*7919});
    disjointFalse+=Number(disjointPhaseAudit(d,h).excludesZero);
    widths.forEach((bandwidth,j)=>{
      const a=auditPairedDifference(d,{bandwidth});
      counts[j]+=Number(a.excludesZero);seSum[j]+=a.se;effSum[j]+=a.effectiveN??0;
    });
  }
  return {replications,n,h,phi,methods:widths.map((bandwidth,j)=>({method:bandwidth===0?'iid':bandwidth===h-1?'HAC_h-1':'HAC_2h-1',bandwidth,falsePositiveRate:counts[j]/replications,meanSE:seSum[j]/replications,meanEffectiveN:effSum[j]/replications})),disjointFixedPhase:{falsePositiveRate:disjointFalse/replications,observations:Math.ceil(n/h)},note:'Two fixed symmetric forecasts have exactly equal expected absolute error. Any exclusion of zero is a false positive. HAC is approximate and not a guaranteed finite-sample correction.'};
}
