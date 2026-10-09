import {validateSpot,validateHistory} from "./source_quality.mjs";

/** Pure, fail-closed classifier for ONE refresh. Never reads prior UI state. */
export function classifyFeeds(historyResult,spotResult,{nowMs=Date.now(),spotMaxAgeMinutes=15,historyMaxAgeDays=7}={}) {
  let quote=null,series=null,quoteUpdated=null,historyLatestDate=null;
  const problems=[];
  if (spotResult?.status==="fulfilled") {
    try {
      const checked=validateSpot(spotResult.value,{nowMs,maxAgeMinutes:spotMaxAgeMinutes});
      quoteUpdated=checked.quote.updated;
      if (checked.state==="fresh") quote=checked.quote;
      else problems.push("spot_stale:"+checked.ageMinutes.toFixed(1)+"m");
    } catch(error) {problems.push("spot_invalid:"+error.message)}
  } else problems.push("spot_unavailable");
  if (historyResult?.status==="fulfilled") {
    try {
      const checked=validateHistory(historyResult.value,{nowMs,maxAgeDays:historyMaxAgeDays});
      historyLatestDate=checked.latestDate;
      if (checked.state==="fresh") series=checked.rows;
      else problems.push("history_stale:"+checked.ageDays.toFixed(1)+"d");
    } catch(error) {problems.push("history_invalid:"+error.message)}
  } else problems.push("history_unavailable");
  const state=quote&&series?"live":series?"history-only":quote?"spot-only":"unavailable";
  return {state,quote,series,quoteUpdated,historyLatestDate,problems};
}
