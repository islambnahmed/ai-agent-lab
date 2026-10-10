/**
 * Reproducible synthetic, strictly chronological interval stress test.
 * Run: node products/gold-forecast/research/prequential_band_benchmark.mjs [seeds=100]
 *
 * Compares the product's fixed validation-error band against an EXPERIMENTAL
 * trailing 30-error band, updated only after the corresponding target is known.
 * Neither is a calibrated confidence interval. No real gold data is used.
 * Output: average holdout coverage and mean half-width as % of predicted price.
 */
import {forecast,predict} from "../forecast.mjs";

const seeds = Number(process.argv[2] ?? 100);
if (!Number.isInteger(seeds) || seeds < 1 || seeds > 500)
  throw Error("seeds must be an integer in [1,500]");

function rng(seed) {
  let s = seed >>> 0;
  return () => {s = (Math.imul(s,1664525) + 1013904223) >>> 0; return (s+.5)/4294967296;};
}
function normal(r) {return Math.sqrt(-2*Math.log(r()))*Math.cos(2*Math.PI*r());}
function prices(seed, cfg) {
  const r=rng(seed), out=[]; let logP=Math.log(2600);
  const date=new Date(Date.UTC(2025,0,1));
  while (out.length<360) {
    if (date.getUTCDay()!==0 && date.getUTCDay()!==6) {
      logP += (out.length<290 ? cfg.before : cfg.after) + cfg.sigma*normal(r);
      out.push({date:date.toISOString().slice(0,10),price:Math.exp(logP)});
    }
    date.setUTCDate(date.getUTCDate()+1);
  }
  return out;
}
function quantile(values, fraction) {
  const sorted=[...values].sort((a,b)=>a-b);
  return sorted[Math.max(0,Math.ceil(sorted.length*fraction)-1)];
}
const scenarios=[
  {name:"stationary",before:.001,after:.001,sigma:.008},
  {name:"moderate_reversal",before:.0015,after:-.002,sigma:.008},
  {name:"strong_reversal",before:.003,after:-.007,sigma:.007},
  {name:"acceleration",before:.001,after:.004,sigma:.008}
];
function evaluate(seed, cfg, horizon) {
  const rows=prices(seed,cfg), p=rows.map(x=>x.price), n=p.length;
  const selected=forecast(rows,horizon);
  const split=Math.floor(n*.8), start=Math.max(65,2*horizon+45);
  const end=split-horizon+1, stride=Math.max(1,Math.floor(horizon/5));
  const validation=[];
  for(let i=start;i<end;i+=stride) {
    const point=predict(p.slice(0,i),horizon,selected.model);
    validation.push(Math.abs(point-p[i+horizon-1])/point);
  }
  const audit=[], metrics={staticHits:0,adaptiveHits:0,staticWidth:0,adaptiveWidth:0,count:0};
  for(let origin=split;origin<=n-horizon;origin++) {
    const point=predict(p.slice(0,origin),horizon,selected.model);
    const actual=p[origin+horizon-1];
    // Only previously completed outcomes are eligible; never use future targets.
    const matured=audit.filter(x=>x.targetIndex<origin).map(x=>x.error);
    const recent=[...validation.slice(-30),...matured].slice(-30);
    const adaptive=Math.max(.002,quantile(recent,.8));
    const fixed=selected.band;
    metrics.staticHits+=Number(actual>=point*(1-fixed)&&actual<=point*(1+fixed));
    metrics.adaptiveHits+=Number(actual>=point*(1-adaptive)&&actual<=point*(1+adaptive));
    metrics.staticWidth+=fixed; metrics.adaptiveWidth+=adaptive; metrics.count++;
    audit.push({targetIndex:origin+horizon-1,error:Math.abs(point-actual)/point});
  }
  return {
    staticCoverage:metrics.staticHits/metrics.count,
    adaptiveCoverage:metrics.adaptiveHits/metrics.count,
    staticHalfWidth:metrics.staticWidth/metrics.count,
    adaptiveHalfWidth:metrics.adaptiveWidth/metrics.count
  };
}
const results=[];
for(const scenario of scenarios)for(const horizon of [7,30]) {
  const sums={staticCoverage:0,adaptiveCoverage:0,staticHalfWidth:0,adaptiveHalfWidth:0};
  for(let seed=1;seed<=seeds;seed++) {
    const metrics=evaluate(seed,scenario,horizon);
    for(const key of Object.keys(sums))sums[key]+=metrics[key]/seeds;
  }
  results.push({scenario:scenario.name,horizon,seeds,
    ...Object.fromEntries(Object.entries(sums).map(([key,value])=>[key,+(value*100).toFixed(2)]))});
}
console.log(JSON.stringify({note:"Synthetic stress test only; percentages; NOT a real gold-market performance claim",results},null,2));
