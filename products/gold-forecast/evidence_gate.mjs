/**
 * Conservative evidence gate for forecast evaluation.
 * Non-overlapping windows are NOT guaranteed independent.
 * Does not establish skill or interval calibration.
 */
export function evidenceGate({
  seriesLength, horizon, auditedOnRealData=false,
  prospectivelyTimestamped=false, crossSourceVerified=false, minDisjoint=20
}={}) {
  if(!Number.isInteger(seriesLength)||seriesLength<1) throw Error("Invalid series length");
  if(![1,7,30].includes(horizon)) throw Error("Unsupported horizon");
  if(!Number.isInteger(minDisjoint)||minDisjoint<2) throw Error("Invalid threshold");
  const split=Math.floor(seriesLength*.8);
  const start=Math.max(65,2*horizon+45);
  const stride=Math.max(1,Math.floor(horizon/5));
  const validationOverlapping=Math.max(0,Math.ceil((split-horizon+1-start)/stride));
  const holdoutOverlapping=Math.max(0,seriesLength-horizon+1-split);
  const validationDisjoint=Math.max(0,Math.floor((split-start)/horizon));
  const holdoutDisjoint=Math.max(0,Math.floor((seriesLength-split)/horizon));
  const forecastRunnable=seriesLength>=Math.max(165,horizon+130)
    &&validationOverlapping>=10&&holdoutOverlapping>=10;
  const enoughWindows=forecastRunnable&&validationDisjoint>=minDisjoint&&holdoutDisjoint>=minDisjoint;
  const canDiscussProspectiveSkill=enoughWindows&&auditedOnRealData
    &&prospectivelyTimestamped&&crossSourceVerified;
  return {
    horizon,seriesLength,forecastRunnable,enoughWindows,canDiscussProspectiveSkill,
    validation:{overlappingWindows:validationOverlapping,nonoverlappingTargetWindows:validationDisjoint},
    holdout:{overlappingWindows:holdoutOverlapping,nonoverlappingTargetWindows:holdoutDisjoint},
    coverageLabel:!forecastRunnable?"forecast_unavailable":
      enoughWindows?"descriptive_historical_coverage":"insufficient_nonoverlapping_targets",
    skillLabel:canDiscussProspectiveSkill?"eligible_for_further_skill_analysis":"unverified"
  };
}
