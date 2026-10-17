/** Khepri exp249: adversarial cross-review of exp248's fixed-phase disjoint test.
 * Only synthetic null simulations. A post-hoc choice among disjoint phases is
 * multiple testing; these results are not measurements of gold forecast skill.
 */
import {pairedLossDifferentials,rng} from '../exp248/dependence_audit.mjs';

function logGamma(z) {
  const p=[0.99999999999980993,676.5203681218851,-1259.1392167224028,
    771.32342877765313,-176.6150291621406,12.507343278686905,
    -0.13857109526572012,9.984369578019572e-6,1.5056327351493116e-7];
  if(z<0.5)return Math.log(Math.PI)-Math.log(Math.sin(Math.PI*z))-logGamma(1-z);
  z-=1;let x=p[0];for(let i=1;i<p.length;i++)x+=p[i]/(z+i);
  const t=z+7.5;return 0.5*Math.log(2*Math.PI)+(z+0.5)*Math.log(t)-t+Math.log(x);
}
function betaCF(a,b,x) {
  const max=200,eps=3e-14,fpmin=1e-300;
  let c=1,d=1-(a+b)*x/(a+1);
  if(Math.abs(d)<fpmin)d=fpmin;d=1/d;let h=d;
  for(let m=1;m<=max;m++){
    const m2=2*m;
    let aa=m*(b-m)*x/((a+m2-1)*(a+m2));
    d=1+aa*d;if(Math.abs(d)<fpmin)d=fpmin;
    c=1+aa/c;if(Math.abs(c)<fpmin)c=fpmin;
    d=1/d;h*=d*c;
    aa=-(a+m)*(a+b+m)*x/((a+m2)*(a+m2+1));
    d=1+aa*d;if(Math.abs(d)<fpmin)d=fpmin;
    c=1+aa/c;if(Math.abs(c)<fpmin)c=fpmin;
    d=1/d;const delta=d*c;h*=delta;
    if(Math.abs(delta-1)<eps)break;
  }
  return h;
}
function regBeta(x,a,b) {
  if(x<=0)return 0;if(x>=1)return 1;
  const front=Math.exp(logGamma(a+b)-logGamma(a)-logGamma(b)+a*Math.log(x)+b*Math.log1p(-x));
  if(x<(a+1)/(a+b+2))return front*betaCF(a,b,x)/a;
  return 1-front*betaCF(b,a,1-x)/b;
}
export function twoSidedTP(t,df) {
  if(!Number.isFinite(t)||!Number.isInteger(df)||df<1)throw Error('Invalid t statistic or degrees of freedom');
  return Math.max(0,Math.min(1,regBeta(df/(df+t*t),df/2,0.5)));
}
export function phaseAudit(d,h,{alpha=0.05}={}) {
  if(!Array.isArray(d)||d.some(x=>!Number.isFinite(x))||!Number.isInteger(h)||h<1||h>Math.floor(d.length/3)||
    !Number.isFinite(alpha)||alpha<=0||alpha>=1)throw Error('Invalid audit input');
  const phases=[];
  for(let offset=0;offset<h;offset++){
    const xs=[];for(let i=offset;i<d.length;i+=h)xs.push(d[i]);
    const n=xs.length,mean=xs.reduce((a,b)=>a+b,0)/n;
    const varSample=xs.reduce((a,x)=>a+(x-mean)**2,0)/(n-1);
    const se=Math.sqrt(varSample/n);
    const t=se===0?(mean===0?0:Math.sign(mean)*1e100):mean/se;
    const p=twoSidedTP(t,n-1);
    phases.push({offset,n,mean,se,t,p});
  }
  const selected=[...phases].sort((a,b)=>a.p-b.p||a.offset-b.offset)[0];
  return {h,alpha,preRegistered:phases[0],selected,
    fixedReject:phases[0].p<alpha,
    postHocAnyReject:selected.p<alpha,
    bonferroniReject:selected.p<alpha/h,
    selectedAdjustedP:Math.min(1,selected.p*h),
    phasePRange:[selected.p,Math.max(...phases.map(x=>x.p))],
    caveat:'Fixed phase must be preregistered. Bonferroni addresses phase search but not serial dependence across disjoint observations, model selection, or other reused data.'};
}
/** Symmetric null for A/B conversion-count differences. Exactly equal expected loss
 * for +c and -c because cohort labels are exchangeable. */
export function pairedConversionDifferences({n=300,h=7,visitors=80,p=0.1,c=0.5,seed=1}={}) {
  if(!Number.isInteger(n)||n<30||!Number.isInteger(h)||h<1||h>n||!Number.isInteger(visitors)||visitors<1||
    !(p>0&&p<1)||!(c>0&&Number.isFinite(c)))throw Error('Invalid conversion simulation');
  const u=rng(seed),daily=[];
  for(let day=0;day<n+h-1;day++){
    let delta=0;for(let i=0;i<visitors;i++)delta+=Number(u()<p)-Number(u()<p);
    daily.push(delta);
  }
  let sum=0;for(let j=0;j<h;j++)sum+=daily[j];
  const denom=Math.sqrt(h*2*visitors*p*(1-p)),d=[];
  for(let i=0;i<n;i++){
    const target=sum/denom;
    d.push(Math.abs(target-c)-Math.abs(target+c));
    if(i<n-1)sum+=daily[i+h]-daily[i];
  }
  return d;
}
export function monteCarlo({replications=1500,n=300,h=30,phi=0,seed=22017,kind='gold'}={}) {
  if(!Number.isInteger(replications)||replications<1||replications>50000||!['gold','conversions'].includes(kind))throw Error('Invalid Monte Carlo options');
  const counts={fixed:0,postHocAny:0,bonferroni:0,selectedMeanMagnitude:0,fixedMeanMagnitude:0};
  for(let r=0;r<replications;r++){
    const s=seed+r*7919;
    const d=kind==='gold'?pairedLossDifferentials({n,h,phi,seed:s}):pairedConversionDifferences({n,h,seed:s});
    const a=phaseAudit(d,h);
    counts.fixed+=Number(a.fixedReject);counts.postHocAny+=Number(a.postHocAnyReject);
    counts.bonferroni+=Number(a.bonferroniReject);
    counts.selectedMeanMagnitude+=Math.abs(a.selected.mean);
    counts.fixedMeanMagnitude+=Math.abs(a.preRegistered.mean);
  }
  return {kind,n,h,phi,replications,seed,
    falsePositiveRate:{fixed:counts.fixed/replications,postHocAny:counts.postHocAny/replications,bonferroni:counts.bonferroni/replications},
    meanAbsPhaseEffect:{fixed:counts.fixedMeanMagnitude/replications,postHocSelected:counts.selectedMeanMagnitude/replications},
    null:'Two symmetric fixed forecasts with exactly equal expected MAE; rates measure spurious significance, not predictive skill.'};
}
