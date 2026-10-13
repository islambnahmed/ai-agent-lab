/**
 * Conservative, descriptive UTC session attribution for a 75-minute XAU/USD grid.
 * This is NOT an exchange or broker trading calendar. The labels are heuristic:
 * - weekendCore: Saturday 03:00 UTC through Sunday 18:00 UTC.
 * - transitionUnknown: Friday 20:00–Saturday 03:00, Sunday 18:00–Monday 02:00 UTC.
 * - weekdayCandidate: remaining times (holidays / vendor outages are still unknown).
 * An anchor is assigned the most cautious category across ISSUE and TARGET.
 * All fixed-clock anchors remain in the all-clock denominator.
 */
import {evaluateFixedGrid, HORIZON, MIN} from './gold-site-grid-eval.mjs';

export function classifyGoldSessionUTC(ms) {
  if (!Number.isSafeInteger(ms)) throw Error('UTC timestamp must be a safe integer');
  const d = new Date(ms);
  if (!Number.isFinite(d.getTime())) throw Error('Invalid UTC timestamp');
  const day = d.getUTCDay(); // 0=Sunday, 6=Saturday
  const minute = d.getUTCHours() * 60 + d.getUTCMinutes();
  if ((day === 6 && minute >= 3 * 60) || (day === 0 && minute < 18 * 60)) return 'weekendCore';
  if ((day === 5 && minute >= 20 * 60) || (day === 6 && minute < 3 * 60) ||
      (day === 0 && minute >= 18 * 60) || (day === 1 && minute < 2 * 60)) return 'transitionUnknown';
  return 'weekdayCandidate';
}

const ordered = ['weekendCore', 'transitionUnknown', 'weekdayCandidate'];
const empty = () => ({scheduled:0, matured:0, notMatured:0, missingIssue:0, missingLookback:0,
  invalidMomentum:0, missingTarget:0, evaluated:0, eligible:0});
const before = (rows, t) => {let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<=t)lo=m+1;else hi=m;}return lo-1;};
const after = (rows, t) => {let lo=0,hi=rows.length;while(lo<hi){const m=(lo+hi)>>>1;if(rows[m].t<t)lo=m+1;else hi=m;}return lo;};
const ratio = (a,b) => b ? a/b : null;

export function auditSessionCoverage(rows, options) {
  // Reuse published evaluator's validation; compare independently counted totals.
  const baseline = evaluateFixedGrid(rows, options);
  const {startMs, endMs, asOfMs, strideMs=HORIZON, maxIssueLagMs=2*MIN,
    maxLookbackLagMs=5*MIN, maxTargetLagMs=10*MIN} = options;
  const groups = Object.fromEntries(ordered.map(x => [x, empty()]));
  const total = empty();
  for (let t=startMs; t<=endMs; t+=strideMs) {
    const target=t+HORIZON;
    const categories=[classifyGoldSessionUTC(t), classifyGoldSessionUTC(target)];
    const group=groups[ordered.find(x=>categories.includes(x))];
    for (const b of [total,group]) {
      b.scheduled++;
      if (target<=asOfMs) b.matured++; else b.notMatured++;
    }
    const count = key => {total[key]++;group[key]++;};
    const i=before(rows,t);
    if (i<0 || t-rows[i].t>maxIssueLagMs) {count('missingIssue');continue;}
    const j=before(rows,t-30*MIN);
    if (j<0 || t-30*MIN-rows[j].t>maxLookbackLagMs) {count('missingLookback');continue;}
    const rate=(rows[i].price-rows[j].price)/(rows[i].t-rows[j].t);
    const prediction=rows[i].price+rate*(target-rows[i].t);
    if (!Number.isFinite(prediction)||prediction<=0) {count('invalidMomentum');continue;}
    count('eligible');
    if (target>asOfMs) continue;
    const k=after(rows,target);
    if (k>=rows.length || rows[k].t>target+maxTargetLagMs || rows[k].t>asOfMs) {count('missingTarget');continue;}
    count('evaluated');
  }
  const enrich = b => ({...b, endToEndCoverage:ratio(b.evaluated,b.matured),
    eligibleCoverage:ratio(b.eligible,b.scheduled),
    unscoredMatured:b.matured-b.evaluated});
  for (const [field, expected] of Object.entries({scheduled:baseline.scheduled,
    ...(baseline.maturedScheduled === undefined ? {} : {matured:baseline.maturedScheduled}),
    eligible:baseline.eligible, missingIssue:baseline.missingIssue,
    missingLookback:baseline.missingLookback, invalidMomentum:baseline.invalidMomentum,
    missingTarget:baseline.missingTarget,evaluated:baseline.evaluated})) {
    if (total[field]!==expected) throw Error(`Cross-check mismatch for ${field}: ${total[field]} vs ${expected}`);
  }
  return {
    protocol:'conservative-utc-session-attribution-v1',
    policy:'heuristic only; no independently verified broker session calendar or holiday schedule',
    grouping:'worst of issue and target UTC category; no anchors removed from all-clock totals',
    total:enrich(total), groups:Object.fromEntries(ordered.map(k=>[k,enrich(groups[k])])),
    baselinePairedMAE:{persistence:baseline.persistence.mae,momentum30:baseline.momentum30.mae},
    warning:'WeekdayCandidate is not proof market was open; missing quotes cannot be called feed failures without external trading-session evidence.'
  };
}
