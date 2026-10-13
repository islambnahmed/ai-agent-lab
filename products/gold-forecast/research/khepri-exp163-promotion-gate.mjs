// Khepri exp163: conservative multi-baseline, multi-regime evidence gate.
// Historical evidence only; never promotes a live model automatically.
function evaluateForecastPromotion(report,{candidate="macroRidge",comparators=["baseline","priceRidge"],minRelativeGain=0}={}){
  if(!Array.isArray(report?.ablation)||!report.ablation.length)throw new Error("Missing ablation array");
  if(!Array.isArray(comparators)||!comparators.length||comparators.includes(candidate))throw new Error("Invalid comparators");
  const phases=["selection","calibrationPeriod","audit"];
  const results=[];
  for(const horizon of report.ablation){
    const checks=[];
    for(const phase of [...phases,"disjoint"]){
      const group=horizon[phase];
      for(const comparator of comparators){
        const c=group?.[candidate],b=group?.[comparator];
        const valid=Number.isInteger(group?.n)&&group.n>0&&c?.n===group.n&&b?.n===group.n&&Number.isFinite(c?.mae)&&c.mae>=0&&Number.isFinite(b?.mae)&&b.mae>0;
        const gain=valid?100*(b.mae-c.mae)/b.mae:null;
        checks.push({phase,comparator,n:group?.n??null,relativeGainPct:gain,pass:valid&&gain>minRelativeGain,reason:!valid?"invalid_or_unpaired_metric":gain<=minRelativeGain?"not_better_than_comparator":"better_than_comparator"});
      }
    }
    const retrospectivePass=checks.filter(c=>phases.includes(c.phase)).every(c=>c.pass);
    results.push({horizon:horizon.horizon,retrospectivePass,checks,disjointIsSensitivityOnly:true});
  }
  return {schemaVersion:1,candidate,comparators,minRelativeGain,decision:"research_only_no_automatic_promotion",allRetrospectivePass:results.every(x=>x.retrospectivePass),horizons:results,limitations:["No independent prospective proof is supplied by this historical report","Disjoint horizons are a sensitivity check, not an independent validation set"]};
}
export {evaluateForecastPromotion};
