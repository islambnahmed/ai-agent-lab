/**
 * Worker A, cycle 234: independent label audits for selectively missing feedback.
 * Synthetic benchmark; NOT a production accuracy guarantee.
 * No dependencies, Node >=18. The sampling plan uses observable metadata only.
 * Independent audit labels must be obtainable for EVERY sampled decision.
 */
import {pathToFileURL} from 'node:url';

export function seeded(seed) {
  if (!Number.isInteger(seed)) throw Error('seed must be integer');
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const mean = xs => xs.reduce((a, b) => a + b, 0) / xs.length;
const round = (v, digits=5) => Number(v.toFixed(digits));

/** Sample indices without replacement; selection never examines outcomes. */
function choose(rows, count, rand) {
  const pool = [...rows];
  for (let i=0; i<count; i++) {
    const j = i + Math.floor(rand() * (pool.length-i));
    [pool[i],pool[j]] = [pool[j],pool[i]];
  }
  return pool.slice(0,count);
}

/**
 * Create a preregistered fixed-budget probability sample of accepted decisions.
 * For 'stratified', proxy=1 is an observable, pre-outcome high-risk signal.
 * Allocation is intentionally fixed in advance (40% of audit budget to proxy=1).
 */
export function planAudit(rows, budget, {strategy='uniform',seed=1,highShare=.4}={}) {
  if (!Array.isArray(rows) || !Number.isInteger(budget) || budget<0 || !['uniform','stratified'].includes(strategy) ||
      !(highShare>0 && highShare<1)) throw Error('invalid plan options');
  const ids = new Set();
  for (const row of rows) {
    if (!Number.isInteger(row.id) || ids.has(row.id) || ![0,1].includes(row.pred) || typeof row.accepted!=='boolean' ||
        ![0,1].includes(row.proxy)) throw Error('invalid observable row');
    ids.add(row.id);
  }
  const accepted=rows.filter(r=>r.accepted);
  const N=accepted.length;
  if (budget>N) throw Error('budget exceeds accepted population');
  if (!budget || !N) return {N,budget:0,strategy,selected:[],strata:[]};
  const rand=seeded(seed);
  let strata;
  if (strategy==='uniform' || !accepted.some(r=>r.proxy===1) || !accepted.some(r=>r.proxy===0)) {
    strata=[{name:'all',rows:accepted,m:budget}];
  } else {
    if (budget<2) throw Error('stratified budget must cover both strata');
    const high=accepted.filter(r=>r.proxy===1), low=accepted.filter(r=>r.proxy===0);
    const mHigh=Math.max(1,Math.min(high.length,budget-1,Math.max(budget-low.length,Math.round(budget*highShare))));
    const mLow=budget-mHigh;
    if (mLow<1 || mLow>low.length) throw Error('infeasible allocation');
    strata=[{name:'high',rows:high,m:mHigh},{name:'low',rows:low,m:mLow}];
  }
  const selected=[], summary=[];
  for (const s of strata) {
    const sample=choose(s.rows,s.m,rand);
    const weight=s.rows.length/N;
    summary.push({name:s.name,population:s.rows.length,sampled:s.m,weight,inclusionProbability:s.m/s.rows.length});
    for (const row of sample) selected.push({id:row.id,pred:row.pred,stratum:s.name});
  }
  return {N,budget,strategy,selected,strata:summary};
}

/**
 * Estimate risk with a label source INDEPENDENT of routine feedback.
 * Finite-population design-unbiased conditional on a fixed prediction ledger.
 * Hoeffding intervals are conservative and rely on randomized sampling and
 * complete, accurate audits of sampled decisions (not on routine label MAR).
 */
export function estimateAudit(plan, oracle, {alpha=.05}={}) {
  if (!plan || typeof oracle!=='function' || !(alpha>0 && alpha<1)) throw Error('invalid audit');
  if (!plan.budget) return {risk:null,interval:[0,1],halfWidth:null,audited:0};
  const groupLosses=new Map(plan.strata.map(s=>[s.name,[]]));
  for (const row of plan.selected) {
    const label=oracle(row.id);
    if (![0,1].includes(label)) throw Error('audit label unavailable or invalid');
    groupLosses.get(row.stratum).push(Number(row.pred!==label));
  }
  let risk=0, sumRangesSquared=0;
  for (const s of plan.strata) {
    const losses=groupLosses.get(s.name);
    if (losses.length!==s.sampled) throw Error('incomplete audit');
    risk+=s.weight*mean(losses);
    sumRangesSquared+=s.weight**2/s.sampled;
  }
  const fullyAudited=plan.strata.every(s=>s.sampled===s.population);
  const halfWidth=fullyAudited?0:Math.sqrt(Math.log(2/alpha)*sumRangesSquared/2);
  return {risk,interval:[Math.max(0,risk-halfWidth),Math.min(1,risk+halfWidth)],halfWidth,audited:plan.selected.length};
}

/**
 * An independent synthetic oracle is deliberately kept outside publicRows.
 * Routine labels are missing-not-at-random: errors are less likely to arrive.
 */
export function syntheticLedger(seed,{n=540,informativeProxy=true}={}) {
  if (!Number.isInteger(n) || n<1) throw Error('invalid n');
  const rand=seeded(seed),publicRows=[],truth=new Map();
  for(let id=0;id<n;id++) {
    const accepted=rand()<.6,proxy=Number(rand()<.2),pred=Number(rand()<.5);
    const errorRate=informativeProxy?(proxy?.45:.04):.122;
    const actual=pred^Number(rand()<errorRate);
    // MNAR routine delivery: 10% of errors versus 80% of correct labels.
    const delivered=rand()<(actual!==pred?.10:.80);
    publicRows.push({id,accepted,proxy,pred,observedLabel:delivered?actual:null});
    truth.set(id,actual);
  }
  return {publicRows,oracle:id=>truth.get(id)};
}

export function evaluateOne(seed,{budget=40,informativeProxy=true}={}) {
  const {publicRows,oracle}=syntheticLedger(seed,{informativeProxy});
  const accepted=publicRows.filter(r=>r.accepted),N=accepted.length;
  const trueRisk=mean(accepted.map(r=>Number(r.pred!==oracle(r.id))));
  const observed=accepted.filter(r=>r.observedLabel!==null);
  const observedErrors=observed.filter(r=>r.pred!==r.observedLabel).length;
  const observedRisk=observed.length?observedErrors/observed.length:null;
  const identifiedBounds=[observedErrors/N,(observedErrors+N-observed.length)/N];
  const uniform=estimateAudit(planAudit(publicRows,budget,{seed:seed+1000003,strategy:'uniform'}),oracle);
  const stratified=estimateAudit(planAudit(publicRows,budget,{seed:seed+2000003,strategy:'stratified'}),oracle);
  const noAudit=estimateAudit(planAudit(publicRows,0,{seed:seed+3000003}),oracle);
  return {N,trueRisk,observedRisk,identifiedBounds,uniform,stratified,noAudit};
}

/** Independent seeds. Summary CIs describe *across-seed* simulation differences. */
export function benchmark({trials=400,seed=45400000,budget=40,informativeProxy=true}={}) {
  if (!Number.isInteger(trials)||trials<2 || !Number.isInteger(budget) || budget<2) throw Error('trials >= 2 and budget >= 2 required');
  const runs=Array.from({length:trials},(_,i)=>evaluateOne(seed+i,{budget,informativeProxy}));
  const summary=name=>{
    const deviations=runs.map(r=>r[name].risk-r.trueRisk);
    return {meanEstimatePct:round(100*mean(runs.map(r=>r[name].risk))),
      biasPctPoints:round(100*mean(deviations)),
      maePctPoints:round(100*mean(deviations.map(Math.abs))),
      rmsePctPoints:round(100*Math.sqrt(mean(deviations.map(d=>d*d)))),
      intervalCoveragePct:round(100*mean(runs.map(r=>Number(r[name].interval[0]<=r.trueRisk && r.trueRisk<=r[name].interval[1])))),
      meanHalfWidthPctPoints:round(100*mean(runs.map(r=>r[name].halfWidth)))};
  };
  const differences=runs.map(r=>100*(Math.abs(r.uniform.risk-r.trueRisk)-Math.abs(r.stratified.risk-r.trueRisk)));
  const d=mean(differences),sd=Math.sqrt(differences.reduce((a,v)=>a+(v-d)**2,0)/(trials-1));
  return {trials,seed,budget,informativeProxy,
    meanAccepted:round(mean(runs.map(r=>r.N))),
    trueRiskPct:round(100*mean(runs.map(r=>r.trueRisk))),
    routineObservedRiskPct:round(100*mean(runs.map(r=>r.observedRisk))),
    meanNoAssumptionBoundsPct:runs[0].identifiedBounds.map((_,i)=>round(100*mean(runs.map(r=>r.identifiedBounds[i])))),
    uniform:summary('uniform'),stratified:summary('stratified'),
    pairedUniformMinusStratifiedAbsoluteErrorPctPoints:round(d),
    pairedApprox95CI:[round(d-1.96*sd/Math.sqrt(trials)),round(d+1.96*sd/Math.sqrt(trials))],
    caveat:'Independent synthetic seeds; audited outcomes always obtainable. Without an independent label source, no audit estimator is identified. Hoeffding intervals conservative, not proof of production reliability.'};
}

if (process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  const trials=Number(process.argv[2]??400),seed=Number(process.argv[3]??45400000);
  console.log(JSON.stringify({informative:benchmark({trials,seed}),uninformative:benchmark({trials,seed,informativeProxy:false})},null,2));
}
