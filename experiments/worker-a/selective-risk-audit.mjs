/**
 * Worker A — selective risk under delayed and missing labels.
 * Synthetic audit, not a production forecasting model or a risk guarantee.
 * Node 18+, no third-party dependencies. Import the sibling delayed-feedback.mjs.
 *
 * Audit bounds are sharp worst-case binary-loss bounds WITHOUT assumptions
 * about missingness: if K of N accepted decisions have observed outcomes,
 * [observedErrors/N, (observedErrors+N-K)/N].
 */
import {generate, schedule} from './delayed-feedback.mjs';
import {pathToFileURL} from 'node:url';

const mean = a => a.reduce((s,x)=>s+x,0)/a.length;
const argmin = a => a.reduce((best,v,i)=>v<a[best]?i:best,0);
const predict = (c,x) => x[c>>1] ^ (c&1);
const error = (c,x,y) => Number(predict(c,x)!==y);
const round = x => Number(x.toFixed(5));

export function auditLedger(ledger, cutoff) {
  if(!Array.isArray(ledger) || !Number.isInteger(cutoff) || cutoff<0) throw Error('Invalid ledger/cutoff');
  const accepted = ledger.filter(e=>e.accepted);
  if(ledger.some((e,i)=>e.t!==i || ![0,1].includes(e.pred) || ![0,1,null,undefined].includes(e.y) || typeof e.accepted!=='boolean' ||
    (e.deliveryTime!==null && (!Number.isInteger(e.deliveryTime) || e.deliveryTime<=e.t)))) throw Error('Invalid event or noncausal delivery');
  const observed = accepted.filter(e=>e.deliveryTime!==null && e.deliveryTime<cutoff);
  if(observed.some(e=>![0,1].includes(e.y)))throw Error('Delivered label missing');
  const errors = observed.reduce((n,e)=>n+Number(e.pred!==e.y),0);
  const hasSimulationTruth=accepted.every(e=>[0,1].includes(e.simulationTruth));
  const trueErrors=hasSimulationTruth?accepted.reduce((n,e)=>n+Number(e.pred!==e.simulationTruth),0):null;
  const N=accepted.length, unknown=N-observed.length;
  return {
    total:ledger.length,accepted:N,coverage:N/Math.max(1,ledger.length),observed:observed.length,unknown,
    observedRisk:observed.length?errors/observed.length:null,
    trueRisk:N&&hasSimulationTruth?trueErrors/N:null, // simulator-only; absent for real incomplete ledgers
    identifiedRiskBounds:N?[errors/N,(errors+unknown)/N]:[null,null],
    // No distribution-free CI tighter than this without additional assumptions.
    historicalRiskFullyIdentified:N>0&&unknown===0
  };
}

export function run(seed,{segments,delivery={maxLag:24,drop:.4},commonMode=false}={}) {
  const data=generate(seed,segments);
  const {train,stream,boundaries}=data;
  if(commonMode){
    // Deliberately introduce an out-of-family failure: two sensors agree on a wrong bit.
    // Every 5th event in the middle segment, both informative features are wrong.
    const from=boundaries[0]??Math.floor(stream.length/3);
    const to=boundaries[1]??Math.floor(2*stream.length/3);
    for(let t=from;t<to;t++) if(commonMode==='all'||t%5===0) stream[t].x[0]=stream[t].x[1]=1-stream[t].y;
  }
  const {deliveries,lost,scheduled}=schedule(stream,{...delivery,seed:seed+1000000});
  const m=2*train[0].x.length, decay=2**(-1/16);
  const warm=Array.from({length:m},(_,c)=>mean(train.map(r=>error(c,r.x,r.y))));
  const sum=warm.map(v=>4*v); let weight=4;
  const records={always:[],agreement:[]};
  const deliveryAt=Array(stream.length).fill(null);
  for(const [deliveryTime,events] of deliveries) for(const e of events) deliveryAt[e.eventTime]=deliveryTime;
  for(let t=0;t<stream.length;t++) {
    weight*=decay;for(let c=0;c<m;c++)sum[c]*=decay;
    for(const row of deliveries.get(t)??[]){
      if(row.eventTime>=t)throw Error('Future-label leakage');
      const w=decay**(t-row.eventTime);
      weight+=w;for(let c=0;c<m;c++)sum[c]+=w*error(c,row.x,row.y);
    }
    const choice=argmin(sum.map(v=>v/weight));
    const pred=predict(choice,stream[t].x);
    const base={t,pred,y:deliveryAt[t]!==null&&deliveryAt[t]<stream.length?stream[t].y:null,
      simulationTruth:stream[t].y,deliveryTime:deliveryAt[t]};
    records.always.push({...base,accepted:true});
    records.agreement.push({...base,accepted:stream[t].x[0]===stream[t].x[1]});
  }
  const cutoff=stream.length;
  return {seed,boundaries,feedback:{lost,scheduled,delivered:[...deliveries].reduce((n,[t,rows])=>n+(t<cutoff?rows.length:0),0)},
    always:auditLedger(records.always,cutoff),agreement:auditLedger(records.agreement,cutoff),
    // Recovery checkpoint for tests; simulationTruth is never passed to the learner.
    records};
}

export function benchmark({trials=200,seed=23300000,segments,delivery,commonMode=false}={}){
  if(!Number.isInteger(trials)||trials<1)throw Error('Invalid trial count');
  const rows=Array.from({length:trials},(_,i)=>run(seed+i,{segments,delivery,commonMode}));
  const aggregate=key=>({
    coveragePct:round(100*mean(rows.map(r=>r[key].coverage))),
    trueRiskPct:round(100*mean(rows.map(r=>r[key].trueRisk))),
    observedRiskPct:rows.every(r=>r[key].observed===0)?null:round(100*rows.reduce((n,r)=>n+r[key].observed*(r[key].observedRisk??0),0)/rows.reduce((n,r)=>n+r[key].observed,0)),
    lowerBoundPct:round(100*mean(rows.map(r=>r[key].identifiedRiskBounds[0]))),
    upperBoundPct:round(100*mean(rows.map(r=>r[key].identifiedRiskBounds[1]))),
    observedAccepted:rows.reduce((n,r)=>n+r[key].observed,0),
    totalAccepted:rows.reduce((n,r)=>n+r[key].accepted,0)
  });
  const differences=rows.map(r=>100*(r.agreement.trueRisk-r.always.trueRisk));
  const d=mean(differences),sd=Math.sqrt(differences.reduce((n,x)=>n+(x-d)**2,0)/Math.max(1,trials-1));
  return {trials,seed,commonMode,delivery:delivery??{maxLag:24,drop:.4},
    always:aggregate('always'),agreement:aggregate('agreement'),
    agreementMinusAlwaysRiskPctPoints:round(d),approx95CI:[round(d-1.96*sd/Math.sqrt(trials)),round(d+1.96*sd/Math.sqrt(trials))],
    note:'Simulation-only true risk. Identified bounds are valid for any missingness mechanism; approximate paired CI assumes independent simulation seeds.'};
}

/** Exact non-identifiability witness: identical observable history, opposite true risks. */
export function indistinguishableWorlds(n=20){
  if(!Number.isInteger(n)||n<1)throw Error('Invalid n');
  const visible=Array.from({length:n},(_,t)=>({t,x:[t%2,t%2],delivered:false}));
  const policyPredictions=visible.map(e=>e.x[0]);
  const riskA=0,riskB=1;
  return {n,visible,policyPredictions,riskA,riskB,
    conclusion:'Without labels or assumptions, observable inputs cannot distinguish 0% from 100% error.'};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const scenarios={
    stationary:{segments:[{n:540,p:.03}],delivery:{maxLag:24,drop:.4}},
    abrupt:{delivery:{maxLag:24,drop:.4}},
    severeLag:{delivery:{maxLag:80,drop:.4}},
    missingNotAtRandom:{delivery:{maxLag:24,drop:.85,dropout:'hard'}},
    commonMode:{delivery:{maxLag:24,drop:.4},commonMode:true},
    systematicConsensusFailure:{delivery:{maxLag:24,drop:.4},commonMode:'all'},
    noFeedback:{delivery:{maxLag:24,drop:1}}
  };
  const trials=Number(process.argv[2]??200),seed=Number(process.argv[3]??23300000);
  console.log(JSON.stringify(Object.fromEntries(Object.entries(scenarios).map(([name,opts])=>[name,benchmark({trials,seed,...opts})])),null,2));
}
