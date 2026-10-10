// Deterministic gold forecasting baselines; zero network or paid dependencies.
export const MODEL_NAMES = {persistence:"آخر إغلاق (Baseline)",momentum:"اتجاه مخفّف",mean_reversion:"عودة للمتوسط"};
export function normalize(raw){
  if(!Array.isArray(raw)) throw Error("Invalid price series");
  const out=new Map();
  for(const p of raw){
    const price=Number(p?.price??p?.close),ts=Date.parse(p?.t??p?.date);
    if(!Number.isFinite(price)||price<=0||!Number.isFinite(ts))continue;
    const day=new Date(ts).toISOString().slice(0,10),previous=out.get(day);
    if(!previous||ts>=previous.ts)out.set(day,{date:day,price,ts});
  }
  return [...out.values()].sort((a,b)=>a.date.localeCompare(b.date)).map(({date,price})=>({date,price}));
}
const mean=v=>v.reduce((a,b)=>a+b,0)/v.length;
export function predict(history,h,model="persistence"){
  if(history.length<42||h<1||h>30||!Number.isInteger(h))throw Error("Insufficient history/invalid horizon");
  const last=history.at(-1);
  if(history.some(p=>!Number.isFinite(p)||p<=0))throw Error("Invalid values");
  if(model==="persistence")return last;
  if(model==="momentum"){
    const t=history.slice(-21),r=mean(t.slice(1).map((p,i)=>Math.log(p/t[i])));
    return last*Math.exp(Math.max(-0.012,Math.min(0.012,r))*h*0.45*Math.exp(-h/20));
  }
  if(model==="mean_reversion"){
    const anchor=mean(history.slice(-40).map(Math.log));
    return Math.exp(Math.log(last)+(anchor-Math.log(last))*Math.min(0.6,h*0.025));
  }
  throw Error("Unknown model");
}
function q(a,f){const b=[...a].sort((x,y)=>x-y);return b[Math.max(0,Math.min(b.length-1,Math.ceil(b.length*f)-1))]}
function sample(prices,h,model,start,end,stride=1){
  const rows=[];
  for(let i=start;i<end;i+=stride){
    const actual=prices[i+h-1];if(!Number.isFinite(actual))break;
    const expected=predict(prices.slice(0,i),h,model);
    rows.push({mae:Math.abs(expected-actual),mape:Math.abs(expected-actual)/actual});
  }
  return rows;
}
const metric=rows=>({n:rows.length,mae:mean(rows.map(r=>r.mae)),mape:100*mean(rows.map(r=>r.mape))});
export function forecast(raw,h=7){
  if(![1,7,30].includes(h))throw Error("Unsupported horizon");
  const series=normalize(raw),prices=series.map(p=>p.price),n=prices.length;
  if(n<Math.max(165,h+130))throw Error("Not enough price history");
  const split=Math.floor(n*0.8),start=Math.max(65,2*h+45),end=split-h+1;
  const candidates=Object.keys(MODEL_NAMES).map(model=>{
    const rows=sample(prices,h,model,start,end,Math.max(1,Math.floor(h/5)));
    return {model,rows,validation:metric(rows)};
  });
  if(candidates.some(c=>c.rows.length<10))throw Error("Not enough validation samples");
  candidates.sort((a,b)=>a.validation.mae-b.validation.mae);
  const best=candidates[0],auditRows=sample(prices,h,best.model,split,n-h+1),baselineRows=sample(prices,h,"persistence",split,n-h+1);
  if(auditRows.length<10)throw Error("Not enough audit samples");
  const band=Math.max(0.002,q(best.rows.map(r=>r.mape),0.8));
  const point=predict(prices,h,best.model),audit=metric(auditRows),baseline=metric(baselineRows);
  return {model:best.model,point,lower:Math.max(0,point*(1-band)),upper:point*(1+band),
    band,coverage:100*auditRows.filter(r=>r.mape<=band).length/auditRows.length,
    audit,baseline,beat:audit.mae<baseline.mae,series:series.slice(-120),
    latest:series.at(-1),auditedFrom:series[split].date};
}
export function tradingDate(dateISO,h){
  const d=new Date(dateISO+"T12:00:00Z");
  for(let n=0;n<h;){d.setUTCDate(d.getUTCDate()+1);if(d.getUTCDay()!==0&&d.getUTCDay()!==6)n++}
  return d.toISOString().slice(0,10);
}