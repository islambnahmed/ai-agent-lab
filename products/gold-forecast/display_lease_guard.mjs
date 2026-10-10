import {evaluateDisplayLease} from "./freshness_lease.mjs";

/**
 * Enforce expiration only on provider-owned data. DEMO and CSV are exempt.
 * The caller owns DOM rendering: actions update the UI when a lease expires.
 * Repeated calls are idempotent because expired data and mode are cleared.
 */
export function enforceDisplayLease(snapshot, actions, nowMs=Date.now()) {
  if (snapshot.loading || !["live", "history-only", "spot-only"].includes(snapshot.mode)) return null;

  const lease=evaluateDisplayLease({
    quoteUpdated:snapshot.quoteUpdated,
    historyLatestDate:snapshot.historyLatestDate,
    nowMs
  });
  const quoteValid=Boolean(snapshot.quote) && lease.quoteValid;
  const historyValid=Array.isArray(snapshot.series) && snapshot.series.length>0 && lease.historyValid;
  const nextMode=quoteValid && historyValid ? "live" : historyValid ? "history-only" : quoteValid ? "spot-only" : "unavailable";

  if (!quoteValid && snapshot.quote) {
    snapshot.quote=null;
    snapshot.quoteUpdated=null;
    actions.expireQuote();
  }
  if (!historyValid && snapshot.series) {
    snapshot.series=null;
    snapshot.historyLatestDate=null;
    actions.expireHistory();
  }
  if (nextMode !== snapshot.mode) {
    snapshot.mode=nextMode;
    actions.changeStatus(nextMode);
  }
  return {state:nextMode,quoteValid,historyValid};
}
