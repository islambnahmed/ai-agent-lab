/**
 * Abstention-aware directional forecast audit.
 * Point-forecast direction is only evaluated when the model actually calls up/down.
 * An unchanged baseline is NOT an up/down forecast. The deadband is declared
 * before inspecting outcomes; do not tune it on the audit period.
 */
export function directionalAudit(rows,{deadbandBps=5}={}){
  if(!Array.isArray(rows)||rows.length===0)throw Error('Nonempty forecast rows required');
  if(!Number.isFinite(deadbandBps)||deadbandBps<0||deadbandBps>=10000)throw Error('Invalid deadbandBps');
  const threshold=deadbandBps/10000;
  let calls=0,hits=0,abstentions=0,neutralHits=0,rawHits=0;
  for(const row of rows){
    const {originClose,point,actual}=row??{};
    if(![originClose,point,actual].every(v=>typeof v==='number'&&Number.isFinite(v)&&v>0))throw Error('Invalid forecast row');
    const forecastReturn=point/originClose-1,realizedReturn=actual/originClose-1;
    const forecastDir=Math.abs(forecastReturn)>threshold?Math.sign(forecastReturn):0;
    const realizedDir=Math.abs(realizedReturn)>threshold?Math.sign(realizedReturn):0;
    if(Math.sign(forecastReturn)===Math.sign(realizedReturn))rawHits++;
    if(forecastDir===0){abstentions++;if(realizedDir===0)neutralHits++;}
    else{calls++;if(forecastDir===realizedDir)hits++;}
  }
  return {n:rows.length,deadbandBps,directionalCalls:calls,
    directionalCoveragePct:100*calls/rows.length,
    directionalHitRatePct:calls?100*hits/calls:null,
    neutralCalls:abstentions,
    neutralCorrectRatePct:abstentions?100*neutralHits/abstentions:null,
    threeClassAccuracyPct:100*(hits+neutralHits)/rows.length,
    rawSignAgreementPct:100*rawHits/rows.length,
    caution:'Directional hit rate is conditional on non-neutral calls; report call coverage and neutral accuracy separately. No evidence of trading profitability.'};
}
