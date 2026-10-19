/**
 * Worker A: strictly causal delayed-label online adaptation benchmark.
 * Synthetic evidence only. All learning uses labels already delivered.
 * Node >=18, no dependencies. Run: node delayed-feedback.mjs
 */
import {pathToFileURL} from 'node:url';

export function seeded(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const argmin = values => values.reduce((winner, value, i) => value < values[winner] ? i : winner, 0);
const pred = (candidate, x) => x[candidate >> 1] ^ (candidate & 1);
const err = (candidate, x, y) => Number(pred(candidate, x) !== y);
const mean = arr => arr.reduce((a,b) => a + b, 0) / arr.length;

/** Labels are generated before the run but never exposed to learners before delivery. */
export function generate(seed, segments = [{n:180, p:.03}, {n:180, p:.97}, {n:180, p:.03}]) {
  if (!Array.isArray(segments) || !segments.length || segments.some(s => !Number.isInteger(s.n) || s.n < 1 || !(s.p >= 0 && s.p <= 1))) throw Error('Invalid segments');
  const rand = seeded(seed);
  const sample = p => {
    const y = +(rand() < .5);
    return {x: [y ^ +(rand() < .22), y ^ +(rand() < p), +(rand() < .5)], y};
  };
  const train = Array.from({length:80}, () => sample(segments[0].p));
  const stream = [], boundaries = [];
  for (const [i, segment] of segments.entries()) {
    if (i) boundaries.push(stream.length);
    for (let j=0; j<segment.n; j++) stream.push(sample(segment.p));
  }
  return {train, stream, boundaries};
}

/**
 * A delivery is observable only at time >= eventTime+1+lag.
 * Dropout modes: mcar (independent), hard (depends on the stable candidate being wrong).
 * The latter is missing-not-at-random and intentionally non-identifiable from delivered labels alone.
 */
export function schedule(stream, {seed=999, maxLag=0, drop=.0, dropout='mcar'} = {}) {
  if (!Number.isInteger(maxLag) || maxLag < 0 || !(drop >= 0 && drop <= 1) || !['mcar','hard'].includes(dropout)) throw Error('Invalid delivery parameters');
  const rand = seeded(seed), deliveries = new Map();
  let lost = 0, scheduled = 0;
  for (const [eventTime, row] of stream.entries()) {
    const hard = row.x[0] !== row.y;
    const p = dropout === 'hard' ? (hard ? drop : 0) : drop;
    if (rand() < p) {lost++; continue;}
    const lag = Math.floor(rand() * (maxLag + 1));
    const deliveryTime = eventTime + 1 + lag;
    if (!deliveries.has(deliveryTime)) deliveries.set(deliveryTime, []);
    deliveries.get(deliveryTime).push({eventTime, x:row.x, y:row.y});
    scheduled++;
  }
  return {deliveries, lost, scheduled};
}

/**
 * Train on a common 80-label warm start; score all methods on every stream row.
 * Oracle is a diagnostic upper-information comparator, not a deployable model.
 * timestamped uses exponential age weights; arrivalEMA ignores event timestamps.
 */
export function evaluate(data, options = {}) {
  const {train, stream, boundaries=[]} = data;
  if (!train?.length || !stream?.length) throw Error('Train and stream required');
  const d = train[0].x.length, m = 2*d, decay = 2**(-1/16);
  const trainMean = Array.from({length:m}, (_,c) => mean(train.map(r=>err(c,r.x,r.y))));
  const frozen = argmin(trainMean), oracle = [...trainMean], arrivalEMA = [...trainMean];
  const timestampedSum = trainMean.map(v=>4*v), arrivalWeightedSum = trainMean.map(v=>4*v);
  let timestampedWeight = 4, arrivalWeightedWeight = 4;
  const {deliveries,lost,scheduled} = schedule(stream, options);
  const errors = {frozen:[],oracle:[],arrivalEMA:[],arrivalWeighted:[],timestamped:[]};
  const choices = {frozen:[],oracle:[],arrivalEMA:[],arrivalWeighted:[],timestamped:[]};
  let delivered = 0, maxStaleness = 0;
  for (const [t,row] of stream.entries()) {
    // Clock decay and labels delivered by time t happen before today's prediction.
    timestampedWeight *= decay;
    arrivalWeightedWeight *= decay;
    for (let c=0;c<m;c++) {timestampedSum[c] *= decay; arrivalWeightedSum[c] *= decay;}
    for (const deliveredRow of deliveries.get(t) ?? []) {
      if (deliveredRow.eventTime >= t) throw Error('Future-label leakage');
      const age = t - deliveredRow.eventTime;
      const weight = decay ** age;
      timestampedWeight += weight;
      arrivalWeightedWeight += 1;
      maxStaleness = Math.max(maxStaleness, age);
      for (let c=0;c<m;c++) {
        const loss = err(c,deliveredRow.x,deliveredRow.y);
        arrivalEMA[c] = decay*arrivalEMA[c] + (1-decay)*loss;
        timestampedSum[c] += weight*loss;
        arrivalWeightedSum[c] += loss;
      }
      delivered++;
    }
    const picks = {
      frozen,
      oracle:argmin(oracle),
      arrivalEMA:argmin(arrivalEMA),
      arrivalWeighted:argmin(arrivalWeightedSum.map(v=>v/arrivalWeightedWeight)),
      timestamped:argmin(timestampedSum.map(v=>v/timestampedWeight))
    };
    for (const [method,c] of Object.entries(picks)) {
      choices[method].push(c);
      errors[method].push(err(c,row.x,row.y));
    }
    // Oracle sees the current label only AFTER all predictions are recorded.
    for (let c=0;c<m;c++) oracle[c] = decay*oracle[c] + (1-decay)*err(c,row.x,row.y);
  }
  const accuracy = Object.fromEntries(Object.entries(errors).map(([k,v])=>[k,1-mean(v)]));
  const first30 = Object.fromEntries(Object.entries(errors).map(([k,v])=>[k,boundaries.length ? 1-mean(boundaries.flatMap(b=>v.slice(b,b+30))) : null]));
  return {accuracy,first30,deliveries:{delivered,lost,scheduled,notYetDelivered:scheduled-delivered,maxStaleness},choices,errors};
}

export function benchmark({trials=200, seed=20261019, segments, delivery={}}={}) {
  if (!Number.isInteger(trials) || trials < 1) throw Error('Invalid trials');
  const results = Array.from({length:trials},(_,i)=>evaluate(generate(seed+i,segments), {...delivery,seed:seed+100000+i}));
  const methods = ['frozen','oracle','arrivalEMA','arrivalWeighted','timestamped'];
  const aggregate = key => Object.fromEntries(methods.map(m=>[m,+(100*mean(results.map(r=>r[key][m]))).toFixed(2)]));
  const paired = (key, a, b) => {
    const differences = results.map(r=>100*(r[key][a]-r[key][b]));
    const avg = mean(differences);
    const sd = Math.sqrt(differences.reduce((n,v)=>n+(v-avg)**2,0)/Math.max(1,trials-1));
    const halfWidth = 1.96*sd/Math.sqrt(trials); // approximate across independent synthetic seeds
    return {differencePctPoints:+avg.toFixed(2),approx95CI:[+(avg-halfWidth).toFixed(2),+(avg+halfWidth).toFixed(2)]};
  };
  return {
    trials, delivery, accuracyPct:aggregate('accuracy'), first30Pct:results[0].first30.frozen === null ? null : aggregate('first30'),
    timestampVsArrivalWeighted:paired('accuracy','timestamped','arrivalWeighted'),
    timestampVsArrivalWeightedFirst30:results[0].first30.frozen === null ? null : paired('first30','timestamped','arrivalWeighted'),
    feedback:{delivered:results.reduce((n,r)=>n+r.deliveries.delivered,0),lost:results.reduce((n,r)=>n+r.deliveries.lost,0),
      pendingAtEnd:results.reduce((n,r)=>n+r.deliveries.notYetDelivered,0)}
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const cases = {
    stationaryMCAR:{maxLag:24,drop:.4},
    immediate:{maxLag:0},
    variableLag:{maxLag:24},
    variableLagMCAR:{maxLag:24,drop:.4},
    variableLagHardMNAR:{maxLag:24,drop:.85,dropout:'hard'},
    severeLag:{maxLag:80,drop:.4}
  };
  console.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([name,delivery])=>[name,benchmark({delivery,segments:name==='stationaryMCAR'?[{n:540,p:.03}]:undefined})])),null,2));
}
