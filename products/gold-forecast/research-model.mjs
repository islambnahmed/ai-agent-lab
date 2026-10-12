// Frozen exploratory ablation. Not admitted to the production selector.
import {solve} from './models.mjs';
export function fitRidgeAt(prices,vectors,origin,h,{window=400,penalty=20}={}){
  if(!Number.isInteger(origin)||origin<0||!Number.isInteger(h)||h<1||h>30||origin>=prices.length||!Number.isInteger(window)||window<20||!Number.isFinite(penalty)||penalty<=0)throw Error('Invalid research origin or fit settings');
  const current=vectors[origin];
  if(!current||current.some(x=>!Number.isFinite(x)))return null;
  const rows=[];
  for(let i=0;i+h<=origin;i++)if(vectors[i]){
    const x=vectors[i],a=prices[i],b=prices[i+h];
    if(x.length!==current.length||x.some(v=>!Number.isFinite(v))||!Number.isFinite(a)||!Number.isFinite(b)||a<=0||b<=0)throw Error('Invalid matured training row');
    rows.push({x,y:Math.log(b/a)});
  }
  const train=rows.slice(-window);
  if(train.length<20)return null;
  const width=current.length,center=current.map((_,j)=>train.reduce((s,r)=>s+r.x[j],0)/train.length);
  const scale=center.map((c,j)=>Math.max(1e-8,Math.sqrt(train.reduce((s,r)=>s+(r.x[j]-c)**2,0)/train.length)));
  const design=x=>[1,...x.map((v,j)=>(v-center[j])/scale[j])];
  const a=Array.from({length:width+1},()=>Array(width+1).fill(0)),b=Array(width+1).fill(0);
  for(const row of train){const x=design(row.x);for(let j=0;j<=width;j++){b[j]+=x[j]*row.y;for(let k=0;k<=width;k++)a[j][k]+=x[j]*x[k];}}
  for(let j=0;j<=width;j++)a[j][j]+=j===0?1e-8:penalty;
  const beta=solve(a,b),x=design(current),ret=beta.reduce((s,v,j)=>s+v*x[j],0);
  return {point:prices[origin]*Math.exp(Math.max(-.20,Math.min(.20,ret))),trainingRows:train.length};
}
