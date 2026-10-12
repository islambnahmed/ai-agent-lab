#!/usr/bin/env node
// Daily GOLD backtest, faithfully reproducing MVP forecast.mjs model equations.
// Run: node research/khepri/gold-data/backtest_mvp_daily.mjs
import fs from 'node:fs';
const text=fs.readFileSync(new URL('./gold_daily_2001_2026.csv',import.meta.url),'utf8').trim();
const rows=text.split(/\r?\n/).slice(1).map(s=>s.split(','));
const dates=rows.map(r=>r[0]),prices=rows.map(r=>Number(r[1]));
if(prices.length<500 || rows.some((r,i)=>!Number.isFinite(prices[i])||prices[i]<=0||(i>0&&dates[i]<=dates[i-1])))throw Error('invalid input');
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
function predict(i,h,model){
  const last=prices[i-1];
  if(model==='persistence')return last;
  if(model==='momentum'){
    const t=prices.slice(i-21,i);
    const r=mean(t.slice(1).map((p,j)=>Math.log(p/t[j])));
    return last*Math.exp(Math.max(-0.012,Math.min(0.012,r))*h*0.45*Math.exp(-h/20));
  }
  if(model==='mean_reversion'){
    const anchor=mean(prices.slice(i-40,i).map(Math.log));
    return Math.exp(Math.log(last)+(anchor-Math.log(last))*Math.min(0.6,h*0.025));
  }
  throw Error('unknown model');
}
const split=Math.floor(prices.length*.8);
const models=['persistence','momentum','mean_reversion'];
const output={source:'gold_daily_2001_2026.csv',rows:prices.length,first:dates[0],last:dates.at(-1),auditStart:dates[split],horizons:{}};
for(const h of [1,7,30]){
  const start=Math.max(65,2*h+45),end=split-h+1,stride=Math.max(1,Math.floor(h/5));
  const validation={},audit={};
  for(const m of models){
    const val=[];
    for(let i=start;i<end;i+=stride)val.push(Math.abs(predict(i,h,m)-prices[i+h-1]));
    validation[m]={n:val.length,mae:mean(val)};
    const test=[];
    for(let i=split;i<prices.length-h+1;i++)test.push(Math.abs(predict(i,h,m)-prices[i+h-1]));
    const half=Math.floor(test.length/2);
    audit[m]={n:test.length,mae:mean(test),firstHalfMAE:mean(test.slice(0,half)),secondHalfMAE:mean(test.slice(half))};
  }
  const selected=[...models].sort((a,b)=>validation[a].mae-validation[b].mae)[0];
  output.horizons[h]={selected,validation,audit,selectedBeatsPersistence:audit[selected].mae<audit.persistence.mae};
}
console.log(JSON.stringify(output,null,2));
