/**
 * Audit overlap diagnostic for Gold Lab. Pure, no network calls.
 * Compatible with the original MVP and experiment-151's denominator fix.
 * Disjoint label windows are NOT a proof of independent errors.
 */
import {forecast, normalize, predict} from './forecast.mjs';

export function auditDependence(raw, horizon, minDisjoint=20) {
  if (![1,7,30].includes(horizon)) throw new RangeError('unsupported horizon');
  if (!Number.isInteger(minDisjoint) || minDisjoint < 1) throw new RangeError('invalid minimum');
  const series=normalize(raw), prices=series.map(p=>p.price), n=prices.length;
  const result=forecast(series,horizon);
  const split=Math.floor(n*0.8), end=n-horizon+1;
  const rows=[];
  for(let origin=split;origin<end;origin++) {
    const expected=predict(prices.slice(0,origin),horizon,result.model);
    const actual=prices[origin+horizon-1];
    rows.push({origin, targetEnd:origin+horizon-1, covered:Math.abs(expected-actual)/expected<=result.band});
  }
  const phases=[];
  for(let offset=0;offset<horizon;offset++) {
    const subset=rows.filter(r=>(r.origin-split)%horizon===offset);
    if(subset.length) phases.push({offset,n:subset.length,coverage:100*subset.filter(r=>r.covered).length/subset.length,
      origins:subset.map(r=>r.origin),targets:subset.map(r=>r.targetEnd)});
  }
  const maxDisjoint=Math.max(...phases.map(p=>p.n));
  const literalCoverage=100*rows.filter(r=>r.covered).length/rows.length;
  const coverageMatchesDisplayed=Math.abs(literalCoverage-result.coverage)<=1e-9;
  return {horizon,nPrices:n,nAudit:rows.length,model:result.model,beatBaselineOnAudit:result.beat,reportedCoverage:result.coverage,literalCoverage,coverageMatchesDisplayed,
    maxDisjointTargetWindows:maxDisjoint, minDisjoint,
    auditInterpretation:maxDisjoint>=minDisjoint?'eligible_for_further_dependence_checks':'descriptive_only',
    phaseCoverageMin:Math.min(...phases.map(p=>p.coverage)),phaseCoverageMax:Math.max(...phases.map(p=>p.coverage)),
    phaseCounts:phases.map(p=>p.n),phases,
    caveat:'Disjoint target intervals do not establish statistical independence; origin training sets and market regimes remain shared.'};
}
