import {evaluateDisplayLease} from "./freshness_lease.mjs";
export function enforceDisplayLease(snapshot, actions, nowMs=Date.now()) {
  if (snapshot.loading || !["live","history-only","spot-only"].includes(snapshot.mode)) return null;
  const lease=evaluateDisplayLease({quoteUpdated:snapshot.quoteUpdated,historyLatestDate:snapshot.historyLatestDate,nowMs});
  if (!lease.quoteValid && snapshot.quote) {
    snapshot.quote=null;
    snapshot.quoteUpdated=null;
  }
  return lease;
}
