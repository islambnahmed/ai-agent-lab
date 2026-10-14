// Khepri exp184: online, no-lookahead interval stress test. Node >= 22, no dependencies.
export function quantile80(errors) {
  if (!Array.isArray(errors) || !errors.length || errors.some(x => !Number.isFinite(x) || x < 0)) throw Error('Nonnegative finite errors required');
  const sorted = [...errors].sort((a,b) => a-b);
  return sorted[Math.min(sorted.length, Math.ceil((sorted.length + 1)*0.8))-1];
}
export function rng(seed) {
  let state = seed >>> 0;
  return () => { state ^= state << 13; state ^= state >>> 17; state ^= state << 5; return (state >>> 0) / 4294967296; };
}
export function gaussian(rand) {
  const u = Math.max(Number.MIN_VALUE, rand());
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2*Math.PI*rand());
}
export function sigmaFor(scenario, t) {
  if (scenario === 'stationary') return 1;
  if (scenario === 'step') return t < 400 ? 1 : 3;
  if (scenario === 'alternating') return t < 200 ? 1 : (Math.floor((t-200)/20) % 2 === 0 ? 3 : 1);
  if (scenario === 'spike') return t >= 400 && t < 410 ? 5 : 1;
  throw Error('Unknown scenario');
}
export function rollingBoundAt(errors, t, window) {
  if (!Number.isInteger(t) || !Number.isInteger(window) || window < 1 || t < window || t > errors.length) throw Error('Invalid causal window');
  return quantile80(errors.slice(t-window,t));
}
export function runTrial(scenario, seed) {
  const rand = rng(seed), errors = Array.from({length: 600}, (_,t) => Math.abs(gaussian(rand) * sigmaFor(scenario,t)));
  const frozen = quantile80(errors.slice(0,200));
  const stats = Object.fromEntries(['frozen','rolling50','rolling100'].map(k=>[k,{hits:0,n:0,sumWidth:0,lateHits:0,lateN:0,lateWidth:0,earlyHits:0,earlyN:0,earlyWidth:0}]));
  for (let t=200; t<600; t++) {
    const bounds = {frozen,rolling50:rollingBoundAt(errors,t,50),rolling100:rollingBoundAt(errors,t,100)};
    for (const [key, bound] of Object.entries(bounds)) {
      const s=stats[key],hit=Number(errors[t]<=bound);
      s.hits+=hit;s.n++;s.sumWidth+=2*bound;
      if(t>=500){s.lateHits+=hit;s.lateN++;s.lateWidth+=2*bound;}
      if(t>=400 && t<420){s.earlyHits+=hit;s.earlyN++;s.earlyWidth+=2*bound;}
    }
  }
  return stats;
}
export function benchmark({trials=300, seed=20261014}={}) {
  const out={seed,trials,results:{}};
  for(const scenario of ['stationary','step','alternating','spike']){
    const totals=Object.fromEntries(['frozen','rolling50','rolling100'].map(k=>[k,{hits:0,n:0,sumWidth:0,lateHits:0,lateN:0,lateWidth:0,earlyHits:0,earlyN:0,earlyWidth:0}]));
    for(let i=0;i<trials;i++){
      const trial=runTrial(scenario,(seed + i*7919 + ['stationary','step','alternating','spike'].indexOf(scenario)*1000003)>>>0);
      for(const [key,values] of Object.entries(trial))for(const field of Object.keys(values))totals[key][field]+=values[field];
    }
    out.results[scenario]=Object.fromEntries(Object.entries(totals).map(([key,s])=>[key,{coveragePct:100*s.hits/s.n,avgFullWidth:s.sumWidth/s.n,lateCoveragePct:100*s.lateHits/s.lateN,lateAvgFullWidth:s.lateWidth/s.lateN,earlyCoveragePct:100*s.earlyHits/s.earlyN,earlyAvgFullWidth:s.earlyWidth/s.earlyN}]));
  }
  return out;
}
if (process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href) console.log(JSON.stringify(benchmark(),null,2));
