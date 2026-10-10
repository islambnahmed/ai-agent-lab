/**
 * Audit whether the UI's reported coverage equals coverage of its displayed interval.
 * Run: node products/gold-forecast/research/band_consistency_audit.mjs [seeds=100]
 * Synthetic paths only; no claim about real gold-market performance.
 */
import {forecast,predict} from '../forecast.mjs';
const seeds=Number(process.argv[2]??100);
if(!Number.isInteger(seeds)||seeds<1||seeds>500)throw Error('seeds must be 1..500');
const scenarios=[
  {name:'stationary',before:.001,after:.001,sigma:.008},
  {name:'strong_reversal',before:.003,after:-.007,sigma:.007},
  {name:'acceleration',before:.001,after:.004,sigma:.008}
];
function path(seed,cfg){
  let s=seed>>>0,logPrice=Math.log(2600);
  const rand=()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return(s+.5)/4294967296};
  const rows=[],date=new Date(Date.UTC(2025,0,1));
  while(rows.length<360){
    if(date.getUTCDay()!==0&&date.getUTCDay()!==6){
      const z=Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());
      logPrice+=(rows.length<290?cfg.before:cfg.after)+cfg.sigma*z;
      rows.push({date:date.toISOString().slice(0,10),price:Math.exp(logPrice)});
    }
    date.setUTCDate(date.getUTCDate()+1);
  }
  return rows;
}
const results=[];
for(const cfg of scenarios)for(const h of [7,30]){
  let total=0,visibleHits=0,reportedSum=0,maxPathGap=0;
  for(let seed=1;seed<=seeds;seed++){
    const rows=path(seed,cfg),p=rows.map(r=>r.price),f=forecast(rows,h);
    const split=Math.floor(p.length*.8);let n=0,hits=0;
    for(let i=split;i<=p.length-h;i++){
      const point=predict(p.slice(0,i),h,f.model),actual=p[i+h-1];
      hits+=Number(actual>=point*(1-f.band)&&actual<=point*(1+f.band));n++;
    }
    visibleHits+=hits;total+=n;reportedSum+=f.coverage/seeds;
    maxPathGap=Math.max(maxPathGap,Math.abs(f.coverage-100*hits/n));
  }
  results.push({scenario:cfg.name,horizon:h,seeds,
    reportedCoveragePct:+reportedSum.toFixed(2),
    actualDisplayedBandCoveragePct:+(100*visibleHits/total).toFixed(2),
    maxPerPathGapPercentagePoints:+maxPathGap.toFixed(2)});
}
console.log(JSON.stringify({note:'Synthetic audit, not investment evidence',results},null,2));
