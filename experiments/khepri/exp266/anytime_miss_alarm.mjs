/**
 * Sequential one-sided miss-rate monitor (research prototype).
 * Null assumption: for each observation t, conditional on all prior observations,
 * P(miss_t=1 | past) <= p0. Under this assumption and predictable fixed bets,
 * W_t is a nonnegative supermartingale; Ville bounds the probability that
 * W_t ever crosses 1/alpha by alpha. Marginal calibration alone is NOT enough.
 * No claim is made that historical gold forecast intervals satisfy this null.
 */
export class AnytimeMissAlarm {
  constructor({p0=0.2, alpha=0.05, betFractions=[0.02,0.05,0.1,0.2,0.4]}={}) {
    if(!(p0>0 && p0<1) || !Number.isFinite(p0))throw Error('p0 must be strictly between 0 and 1');
    if(!(alpha>0 && alpha<1) || !Number.isFinite(alpha))throw Error('alpha must be strictly between 0 and 1');
    if(!Array.isArray(betFractions)||!betFractions.length||betFractions.some(f=>!(f>0&&f<1)||!Number.isFinite(f)))
      throw Error('betFractions must be nonempty fractions in (0,1)');
    this.p0=p0;this.alpha=alpha;this.betFractions=[...betFractions];
    this.logWealth=betFractions.map(()=>0);this.n=0;this.misses=0;this.firstAlarm=null;
  }
  update(miss){
    if(miss!==0 && miss!==1 && miss!==false && miss!==true)throw Error('miss must be 0 or 1');
    const x=Number(miss);
    for(let j=0;j<this.betFractions.length;j++){
      const f=this.betFractions[j];
      // 1 + (f/p0)*(x-p0); both factors strictly positive.
      this.logWealth[j]+=Math.log1p(f*(x-this.p0)/this.p0);
    }
    this.n++;this.misses+=x;
    const top=Math.max(...this.logWealth);
    const logE=top+Math.log(this.logWealth.reduce((s,v)=>s+Math.exp(v-top),0)/this.logWealth.length);
    const alarm=logE>=-Math.log(this.alpha);
    if(alarm&&this.firstAlarm===null)this.firstAlarm=this.n;
    return {n:this.n,misses:this.misses,observedMissRate:this.misses/this.n,logE,alarm,firstAlarm:this.firstAlarm};
  }
}

// Exact binomial upper tail, for a *single* pre-specified window.
// Repeatedly testing rolling windows at alpha without adjustment is invalid.
export function binomialUpperTail(k,n,p){
  if(!Number.isInteger(n)||n<1||!Number.isInteger(k)||k<0||k>n||!(p>0&&p<1))throw Error('invalid binomial parameters');
  if(k===0)return 1;
  let term=(1-p)**n,sum=0;
  for(let i=0;i<=n;i++){
    if(i>=k)sum+=term;
    if(i<n)term*=((n-i)/(i+1))*(p/(1-p));
  }
  return Math.max(0,Math.min(1,sum));
}
export function RollingNaiveAlarm({p0=0.2,alpha=0.05,window=25}={}){
  const buffer=[];let n=0,firstAlarm=null;
  return {update(miss){
    const x=Number(miss);if(x!==0&&x!==1)throw Error('invalid miss');
    buffer.push(x);if(buffer.length>window)buffer.shift();n++;
    const pValue=buffer.length===window?binomialUpperTail(buffer.reduce((a,b)=>a+b,0),window,p0):1;
    const alarm=pValue<=alpha;
    if(alarm&&firstAlarm===null)firstAlarm=n;
    return {n,pValue,alarm,firstAlarm};
  }};
}
