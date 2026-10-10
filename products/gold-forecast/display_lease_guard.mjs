import {evaluateDisplayLease} from "./freshness_lease.mjs";
export function enforceDisplayLease(snapshot, actions, nowMs=Date.now()) {
  return evaluateDisplayLease({quoteUpdated:snapshot.quoteUpdated,historyLatestDate:snapshot.historyLatestDate,nowMs});
}
