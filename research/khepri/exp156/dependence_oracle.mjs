/** Khepri 156: exact Markov-null audit for a fixed prospective sign-test promotion gate.
 * No network, secrets, external data or side effects. Research-only.
 */
export function oneSidedSignP(wins, trials) {
  if (!Number.isInteger(wins) || !Number.isInteger(trials) || wins < 0 || wins > trials) throw new RangeError('invalid counts');
  if (trials === 0) return 1;
  // Binomial tail P[Bin(trials,1/2)>=wins]; recurrence avoids factorial overflow.
  let mass = 2 ** (-trials), tail = wins === 0 ? mass : 0;
  for (let k = 1; k <= trials; k++) {
    mass *= (trials - k + 1) / k;
    if (k >= wins) tail += mass;
  }
  return Math.min(1, tail);
}
export function gateFromSigns(signs, {baseline=100, advantage=.2, decisionBlocks=20, minGainPct=5, maxSignP=.05}={}) {
  if (!Array.isArray(signs) || signs.some(x=>x!==0&&x!==1)) throw new TypeError('signs must be 0/1');
  if (!(baseline>0) || !(advantage>0&&advantage<1) || !Number.isInteger(decisionBlocks) || decisionBlocks<1 || !(minGainPct>=0) || !(maxSignP>0&&maxSignP<=1)) throw new RangeError('invalid gate parameters');
  if (signs.length < decisionBlocks) return {status:'awaiting_predeclared_blocks'};
  const frozen=signs.slice(0,decisionBlocks),wins=frozen.reduce((s,v)=>s+v,0);
  const signP=oneSidedSignP(wins,decisionBlocks);
  const gainPct=100*advantage*(2*wins/decisionBlocks-1);
  return {status:gainPct>minGainPct && signP<=maxSignP?'promotable':'rejected',wins,signP,gainPct};
}
export function exactMarkovPromotion({blocks=20,stay=.5,minGainPct=5,maxSignP=.05,advantage=.2}={}) {
  if (!Number.isInteger(blocks)||blocks<1||blocks>1000||!Number.isFinite(stay)||stay<0||stay>1 || !(advantage>0&&advantage<1)) throw new RangeError('invalid Markov parameters');
  // Two-state stationary Markov chain: P(win)=P(loss)=1/2 for every block.
  // dp[state][wins] holds joint probability at current time, with 0=loss, 1=win.
  let dp=[new Float64Array(blocks+1),new Float64Array(blocks+1)];
  dp[0][0]=.5;dp[1][1]=.5;
  for(let t=2;t<=blocks;t++){
    const next=[new Float64Array(blocks+1),new Float64Array(blocks+1)];
    for(let k=0;k<t;k++){
      next[0][k]+=dp[0][k]*stay+dp[1][k]*(1-stay);
      next[1][k+1]+=dp[1][k]*stay+dp[0][k]*(1-stay);
    }
    dp=next;
  }
  let probability=0,expectedWins=0,firstPassingWins=null;
  for(let k=0;k<=blocks;k++){
    const p=dp[0][k]+dp[1][k]; expectedWins+=k*p;
    const gainPct=100*advantage*(2*k/blocks-1);
    if(gainPct>minGainPct && oneSidedSignP(k,blocks)<=maxSignP){probability+=p;if(firstPassingWins===null)firstPassingWins=k;}
  }
  return {blocks,stay,probability,expectedWins,firstPassingWins};
}
export function xorshift(seed){let s=seed>>>0;return ()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return (s>>>0)/4294967296;};}
export function sampleMarkovSigns(blocks,stay,rand){
  if (!Number.isInteger(blocks)||blocks<1||!(stay>=0&&stay<=1)) throw new RangeError('invalid sample params');
  const out=[];let state=rand()<.5?1:0;
  for(let t=0;t<blocks;t++){if(t && rand()>=stay)state=1-state;out.push(state);}
  return out;
}
export function seasonalSeoGate(signs,{minGainPct=5,maxSignP=.05}={}){
  // Weekly-varying baseline errors: second domain, same dependence hazard.
  const n=signs.length,wins=signs.reduce((s,x)=>s+x,0);
  let base=0,candidate=0;
  for(let t=0;t<n;t++){
    const error=500*(1+.3*Math.sin(2*Math.PI*t/7));
    base+=error;candidate+=error*(signs[t]===1?.8:1.2);
  }
  const gainPct=100*(base-candidate)/base,signP=oneSidedSignP(wins,n);
  return {status:gainPct>minGainPct&&signP<=maxSignP?'promotable':'rejected',gainPct,signP,wins};
}
export function simulate(stay,{runs=100000,seed=15600,blocks=20}={}){
  const rand=xorshift(seed);let gold=0,seo=0;
  for(let i=0;i<runs;i++){
    const signs=sampleMarkovSigns(blocks,stay,rand);
    if(gateFromSigns(signs,{decisionBlocks:blocks}).status==='promotable')gold++;
    if(seasonalSeoGate(signs).status==='promotable')seo++;
  }
  return {stay,runs,goldFalsePromotion:gold/runs,seoFalsePromotion:seo/runs};
}
