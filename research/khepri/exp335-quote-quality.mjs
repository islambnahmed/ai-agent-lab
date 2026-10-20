/** Experimental spread-aware indicative quote check.
 * Apply only AFTER existing validatedSpot/crossCheck timestamp and unit checks.
 * Thresholds are configurable heuristics, not verified market standards.
 */
export function auditQuoteAgreement(primary, secondaryPrice, {maxSpreadPct=1,maxDifferencePct=1}={}){
  const {ask,bid}=primary??{};
  if(![ask,bid,secondaryPrice].every(x=>typeof x==='number'&&Number.isFinite(x)&&x>0))
    throw new TypeError('positive finite numeric quotes required');
  if(ask<bid)throw new RangeError('crossed dealer quote');
  if(![maxSpreadPct,maxDifferencePct].every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=0))
    throw new RangeError('invalid threshold');
  const midpoint=ask/2+bid/2;
  const spreadPct=100*(ask/midpoint-bid/midpoint);
  const differencePct=100*Math.abs(secondaryPrice/midpoint-1);
  const wideSpread=spreadPct>maxSpreadPct;
  const divergent=differencePct>maxDifferencePct;
  const status=wideSpread?'wide_spread_uninformative_comparison':divergent?'price_divergence':'consistent_tight_indicative_quotes';
  return {status,midpoint,spreadPct,differencePct,wideSpread,divergent,
    caveat:'Spread warning does not authenticate source independence or price truth'};
}
