/**
 * Direction diagnostics for price or demand forecasts.
 * No trading recommendation and no claim of statistical independence.
 * Thresholds are basis points of the strictly positive origin value.
 * A zero or immaterial forecast change is an abstention, NOT a wrong signal.
 */
function checkedThreshold(x,name){
  if(!Number.isFinite(x)||x<0||x>=10000)throw new RangeError(`${name} must be in [0,10000) bps`);
  return x;
}
function classify(deltaBps,deadbandBps){
  return deltaBps>deadbandBps?1:deltaBps< -deadbandBps?-1:0;
}
const pct=(a,b)=>b?100*a/b:null;
export function directionalDiagnostics(rows,{signalDeadbandBps=1,actualDeadbandBps=0}={}){
  if(!Array.isArray(rows)||!rows.length)throw new TypeError('Nonempty rows array required');
  checkedThreshold(signalDeadbandBps,'signalDeadbandBps');
  checkedThreshold(actualDeadbandBps,'actualDeadbandBps');
  let issued=0,abstained=0,material=0,flatActual=0,correct=0,scored=0,correctMaterial=0,up=0,down=0;
  let absError=0;
  for(const row of rows){
    if(!row||!['point','actual','originClose'].every(k=>typeof row[k]==='number'&&Number.isFinite(row[k])&&row[k]>0))
      throw new TypeError('Each row requires finite positive point, actual, originClose');
    const pred=classify(10000*(row.point-row.originClose)/row.originClose,signalDeadbandBps);
    const truth=classify(10000*(row.actual-row.originClose)/row.originClose,actualDeadbandBps);
    absError+=Math.abs(row.point-row.actual);
    if(truth){material++;if(truth>0)up++;else down++;}else flatActual++;
    if(!pred){abstained++;continue;}
    issued++;
    if(pred===truth)correct++;
    if(truth){scored++;if(pred===truth)correctMaterial++;}
  }
  return {
    n:rows.length,priceMae:absError/rows.length,
    issuedSignals:issued,abstained,signalRatePct:pct(issued,rows.length),
    hitRateOnIssuedPct:pct(correct,issued),
    materialActualMoves:material,flatActualMoves:flatActual,
    materialMovesWithSignal:scored,
    hitRateOnSignaledMaterialMovesPct:pct(correctMaterial,scored),
    retrospectiveMajorityClassHitRatePct:pct(Math.max(up,down),material),
    interpretation:'No signal = abstention, not a directional error. Conditional hit rates depend on signal coverage; majority-class reference is hindsight-only. Overlapping targets may be dependent.'
  };
}
/** Exact direction-accuracy rule currently used in forecast.mjs:metrics. */
export function legacyDirectionAccuracy(rows){
  return 100*rows.reduce((s,r)=>s+(Math.sign(r.point-r.originClose)===Math.sign(r.actual-r.originClose)?1:0),0)/rows.length;
}
