// Worker A cycle 266: reproducible synthetic detector trade-off.
// No live gold data; no trading/production use. Node.js ESM: node this-file.mjs
function median(a){const s=[...a].sort((x,y)=>x-y);return s.length%2?s[(s.length-1)/2]:(s[s.length/2-1]+s[s.length/2])/2;}
function absReturns(prices){return prices.slice(1).map((p,i)=>Math.abs(Math.log(p/prices[i])));}
function validate(p){if(!Array.isArray(p)||p.some(x=>!Number.isFinite(x)||x<=0))throw Error('positive finite prices required');}
// Transcribed from cycle265 regime-alert.mjs (not integrated into main).
export function legacy(prices){
 validate(prices);if(prices.length<64)return {status:'insufficient_history'};
 const r=absReturns(prices), baseline=median(r.slice(-63,-3)), recent=r.slice(-3);
 const threshold=Math.max(0.012,5*baseline), severe=Math.max(0.06,8*baseline);
 return {status:recent.some(x=>x>severe)||recent.filter(x=>x>threshold).length>=2?'alert':'clear'};
}
export function ratioDetector(prices,{recent=8,ratio=3,minRecent=0.003,minDelta=0.002}={}){
 validate(prices);if(prices.length<60+recent+1)return {status:'insufficient_history'};
 const r=absReturns(prices), before=median(r.slice(-60-recent,-recent)), now=median(r.slice(-recent));
 return {status:now>=minRecent&&now-before>=minDelta&&now/Math.max(before,0.0005)>=ratio?'alert':'clear',before,now};
}
export function hybrid(prices){
 return {status:legacy(prices).status==='alert'||ratioDetector(prices).status==='alert'?'alert':'clear'};
}
function rng(seed){let s=(seed+1)>>>0;return ()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return (s+0.5)/4294967296;};}
function gaussian(rand){return Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());}
export function series(kind,seed,N=500,switchAt=320){
 const rand=rng(seed),out=[2500];
 for(let i=1;i<N;i++){
  let sd=0.002;
  if(kind==='stationary_low')sd=0.001;
  if(kind==='stationary_mid')sd=0.004;
  if(kind==='stationary_high')sd=0.012;
  if(kind==='shift4x')sd=i>=switchAt?0.006:0.0015;
  if(kind==='shift2.5x')sd=i>=switchAt?0.005:0.002;
  if(kind==='shift1.5x')sd=i>=switchAt?0.0045:0.003;
  let ret=gaussian(rand)*sd;
  if(kind==='single_outlier'&&i===switchAt)ret=0.08;
  if(kind==='alternating_shift'&&i>=switchAt)ret=(i%2?1:-1)*0.007;
  out.push(out.at(-1)*Math.exp(ret));
 }
 return out;
}
export function evaluate(kind,method,seeds=40){
 let detectedAny=0,detected15=0,falseAlarmOrigins=0,preShiftOrigins=0;
 for(let seed=1000;seed<1000+seeds;seed++){
  const prices=series(kind,seed);let earliest=Infinity;
  for(let origin=75;origin<prices.length;origin++){
   const alarm=method(prices.slice(0,origin+1)).status==='alert';
   if(origin<320||kind.startsWith('stationary')){preShiftOrigins++;if(alarm)falseAlarmOrigins++;}
   if(origin>=320&&!kind.startsWith('stationary')&&alarm)earliest=Math.min(earliest,origin);
  }
  if(earliest<Infinity){detectedAny++;if(earliest<335)detected15++;}
 }
 return {seeds,detectedAny,detected15,falseAlarmOrigins,preShiftOrigins};
}
export function benchmark(){
 const kinds=['stationary_low','stationary_mid','stationary_high','single_outlier','shift4x','shift2.5x','shift1.5x','alternating_shift'];
 const methods={legacy,ratio8:p=>ratioDetector(p),ratio5:p=>ratioDetector(p,{recent:5,ratio:3.5,minRecent:0.003,minDelta:0.002}),hybrid};
 return Object.fromEntries(kinds.map(kind=>[kind,Object.fromEntries(Object.entries(methods).map(([name,method])=>[name,evaluate(kind,method)]))]));
}
if(process.argv[1]&&import.meta.url==='file://'+process.argv[1])console.log(JSON.stringify(benchmark(),null,2));
