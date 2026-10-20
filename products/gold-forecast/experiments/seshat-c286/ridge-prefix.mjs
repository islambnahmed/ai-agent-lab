/**
 * Experimental Ridge sufficient-statistics index; not production-integrated.
 * Baseline: products/gold-forecast/models.mjs @ 6bb15abe57c87bb9bc98dbc0a25e4bff5ee65b87.
 * Numerical parity is tolerance-based; do not claim bit-identical forecasts.
 */
import {solve} from '../../models.mjs';
const DIM=5, WIDTH=1+DIM+DIM*DIM+DIM;
const cap=(x,b)=>Math.max(-b,Math.min(b,x));
function context(prices){
  const logs=prices.map(Math.log),sums=[0],r=[0],r2=[0];
  for(let i=0;i<logs.length;i++){
    sums.push(sums.at(-1)+logs[i]);
    const ret=i?logs[i]-logs[i-1]:0;
    r.push(r.at(-1)+ret);r2.push(r2.at(-1)+ret*ret);
  }
  return {logs,sums,r,r2};
}
function featureAt({logs,sums,r,r2},i){
  if(i<60)throw Error('Features require 61 prices');
  const avg=(r[i+1]-r[i-19])/20;
  const vol=Math.sqrt(Math.max(0,(r2[i+1]-r2[i-19])/20-avg*avg));
  return [logs[i]-logs[i-5],logs[i]-logs[i-20],
    logs[i]-(sums[i+1]-sums[i-19])/20,
    logs[i]-(sums[i+1]-sums[i-59])/60,vol];
}
export function buildRidgeIndex(history,h){
  if(!Array.isArray(history)||history.length<61||!Number.isInteger(h)||h<1||h>30)
    throw Error('Invalid Ridge index input');
  if(history.some(p=>!Number.isFinite(p)||p<=0))throw Error('Invalid prices');
  const prices=history.slice(),ctx=context(prices),n=prices.length;
  const sums=Array.from({length:n+1},()=>new Float64Array(WIDTH));
  for(let i=0;i<n;i++){
    const row=sums[i+1];row.set(sums[i]);
    if(i<60||i+h>=n)continue;
    const x=featureAt(ctx,i),y=Math.log(prices[i+h]/prices[i]);
    row[0]+=y;
    for(let j=0;j<DIM;j++){
      row[1+j]+=x[j];
      row[1+DIM+DIM*DIM+j]+=x[j]*y;
      for(let k=0;k<DIM;k++)row[1+DIM+j*DIM+k]+=x[j]*x[k];
    }
  }
  return {prices,h,ctx,sums};
}
export function predictRidgeIndexed(index,originLength){
  const {prices,h,ctx,sums}=index;
  if(!Number.isInteger(originLength)||originLength<61||originLength>prices.length)
    throw Error('Invalid origin length');
  const lo=Math.max(60,originLength-h-400),hi=originLength-h,n=hi-lo;
  if(n<20)return prices[originLength-1];
  const upper=sums[hi],lower=sums[lo],sum=k=>upper[k]-lower[k];
  const centers=Array.from({length:DIM},(_,j)=>sum(1+j)/n);
  const scales=centers.map((c,j)=>Math.max(1e-8,Math.sqrt(Math.max(0,sum(1+DIM+j*DIM+j)/n-c*c))));
  const a=Array.from({length:DIM+1},()=>Array(DIM+1).fill(0));
  const b=Array(DIM+1).fill(0);
  a[0][0]=n+1e-8;b[0]=sum(0);
  for(let j=0;j<DIM;j++){
    a[0][j+1]=a[j+1][0]=(sum(1+j)-n*centers[j])/scales[j];
    b[j+1]=(sum(1+DIM+DIM*DIM+j)-centers[j]*sum(0))/scales[j];
    for(let k=0;k<DIM;k++)
      a[j+1][k+1]=(sum(1+DIM+j*DIM+k)-centers[j]*sum(1+k)-centers[k]*sum(1+j)+n*centers[j]*centers[k])/(scales[j]*scales[k])+(j===k?20:0);
  }
  const beta=solve(a,b),features=featureAt(ctx,originLength-1);
  const x=[1,...features.map((v,j)=>(v-centers[j])/scales[j])];
  return prices[originLength-1]*Math.exp(cap(beta.reduce((s,v,j)=>s+v*x[j],0),0.20));
}
