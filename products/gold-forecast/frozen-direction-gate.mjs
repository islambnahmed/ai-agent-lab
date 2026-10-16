/**
 * Seshat cycle 194: frozen threshold evaluation for directional calls.
 * Select only on training labels; never tune against the audit outcomes.
 * Descriptive diagnostics, not trading profitability or statistical inference.
 */
export function directionGate(rows, thresholdPct = 0) {
  if (!Array.isArray(rows) || !rows.length) throw Error('Nonempty rows required');
  if (!Number.isFinite(thresholdPct) || thresholdPct < 0 || thresholdPct >= 100)
    throw RangeError('thresholdPct must be in [0,100)');
  let calls=0,hits=0,flatActual=0,absError=0;
  for (const row of rows) {
    const {originClose,point,actual}=row ?? {};
    if (![originClose,point,actual].every(Number.isFinite) || originClose<=0 || point<=0 || actual<=0)
      throw Error('Finite positive originClose, point, actual required');
    absError+=Math.abs(point-actual);
    const outcomeSign=Math.sign(actual-originClose);
    if (outcomeSign===0) flatActual++;
    const callSign=Math.sign(point-originClose);
    if (callSign!==0 && 100*Math.abs(point/originClose-1)>thresholdPct) {
      calls++;
      if (callSign===outcomeSign) hits++;
    }
  }
  return {n:rows.length,thresholdPct,calls,hits,abstentions:rows.length-calls,flatActual,
    callRatePct:100*calls/rows.length,
    hitRateWhenCalledPct:calls?100*hits/calls:null,mae:absError/rows.length};
}
export function freezeGate(selectionRows,{
  thresholdsPct=[0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9],
  minCallRatePct=10,minCalls=20
}={}) {
  if (!Array.isArray(thresholdsPct) || !thresholdsPct.length ||
      thresholdsPct.some(x=>!Number.isFinite(x)||x<0||x>=100) ||
      new Set(thresholdsPct).size!==thresholdsPct.length)
    throw Error('Thresholds must be unique finite percentages in [0,100)');
  if (!Number.isFinite(minCallRatePct)||minCallRatePct<0||minCallRatePct>100||
      !Number.isInteger(minCalls)||minCalls<1)
    throw Error('Invalid minimum call requirements');
  const candidates=thresholdsPct.map(x=>directionGate(selectionRows,x));
  const eligible=candidates.filter(x=>x.calls>=minCalls&&x.callRatePct>=minCallRatePct);
  if (!eligible.length) return {status:'no_eligible_gate',thresholdPct:null,candidates};
  eligible.sort((a,b)=>b.hitRateWhenCalledPct-a.hitRateWhenCalledPct||
    b.calls-a.calls||a.thresholdPct-b.thresholdPct);
  return {status:'frozen',thresholdPct:eligible[0].thresholdPct,
    selection:eligible[0],candidates};
}
export function evaluateFrozen(selectionRows,auditRows,options={}) {
  const frozen=freezeGate(selectionRows,options);
  return {...frozen,
    audit:frozen.status==='frozen'?directionGate(auditRows,frozen.thresholdPct):null,
    caveat:'Threshold chosen on selection only; audit held out. Dependence invalidates naive IID confidence claims. No trading-cost model.'};
}
export function xorshift32(seed) {
  let s=seed>>>0;
  if(!s)throw Error('Nonzero seed required');
  return ()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return (s>>>0)/4294967296;};
}
export function makeNullRows(n,rng) {
  const rows=[];
  for(let i=0;i<n;i++){
    const predictedSign=rng()<0.5?-1:1;
    const magnitudePct=0.05+0.95*rng();
    const realizedSign=rng()<0.5?-1:1;
    rows.push({originClose:100,point:100*(1+predictedSign*magnitudePct/100),
      actual:100*(1+realizedSign/100)});
  }
  return rows;
}
export function runNullExperiment({repetitions=1000,selectionN=160,auditN=320,seed=1942026}={}) {
  if(![repetitions,selectionN,auditN].every(x=>Number.isInteger(x)&&x>0))
    throw Error('Positive integer sample sizes required');
  const rng=xorshift32(seed),chosen={},train=[],test=[],call=[];
  for(let rep=0;rep<repetitions;rep++){
    const result=evaluateFrozen(makeNullRows(selectionN,rng),makeNullRows(auditN,rng),
      {minCallRatePct:10,minCalls:20});
    if(result.status!=='frozen')throw Error('Unexpected ineligible null gate');
    chosen[result.thresholdPct]=(chosen[result.thresholdPct]??0)+1;
    train.push(result.selection.hitRateWhenCalledPct);
    test.push(result.audit.hitRateWhenCalledPct);
    call.push(result.audit.callRatePct);
  }
  const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
  return {assumptions:'IID synthetic independent random signs; 10 thresholds; disjoint selection/audit.',
    repetitions,selectionN,auditN,seed,
    meanSelectedInSampleHitPct:mean(train),meanFrozenAuditHitPct:mean(test),
    meanAuditCallRatePct:mean(call),
    apparentSelectionInflationPp:mean(train)-mean(test),
    chosenThresholdCounts:chosen,
    caveat:'Null simulation, not gold market data or evidence of predictive skill.'};
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href)
  console.log(JSON.stringify(runNullExperiment(),null,2));
