import {DelayedCalibrator,conformalQuantile,intervalScore} from './delayed_calibration.mjs';
import {predict} from './forecast.mjs';
import {writeFileSync} from 'node:fs';

function rng(seed){let s=seed>>>0;return ()=>((s=(1664525*s+1013904223)>>>0)+.5)/4294967296}
function normal(random){return Math.sqrt(-2*Math.log(Math.max(1e-12,random())))*Math.cos(2*Math.PI*random())}
function makeSeries(kind,seed,n=700){const r=rng(seed),a=[];let p=2200;
 for(let t=0;t<n;t++){
  let sig;
  if(kind==='gold_up')sig=t<300?.003:.016;
  else if(kind==='gold_pulse')sig=t<300||t>=345?.003:.016;
  else if(kind==='gold_stable')sig=.006;
  else if(kind==='seo_up')sig=t<300?3:24;
  else if(kind==='seo_pulse')sig=t<300||t>=345?3:24;
  else throw Error('unknown scenario');
  if(kind.startsWith('gold')){p*=Math.exp(.00018+sig*normal(r));a.push(p)}
  else a.push(Math.max(1,180+.15*t+18*Math.sin(2*Math.PI*t/7)+sig*normal(r)));
 }
 return a;
}
function runOne(kind,seed){
 const series=makeSeries(kind,seed),gold=kind.startsWith('gold'),h=gold?7:1,freeze=220,regime=300;
 const c=new DelayedCalibrator({horizon:h,alpha:.2,window:80,minCalibration:40});
 const pendingFixed=new Map();let fixedBand=null;
 const entries=[];
 for(let t=0;t<series.length;t++){
  const actual=series[t],settled=c.observe(t,actual),f=pendingFixed.get(t);
  if(settled&&f&&settled.origin>=freeze&&settled.band!==null){
   entries.push({origin:settled.origin,post:settled.origin>=regime+h,
      afterPulse:settled.origin>=365,
      adaptive:{hit:settled.hit,score:intervalScore(actual,settled.point,settled.band),width:2*settled.band},
      frozen:{hit:actual>=f.point*(1-f.band)&&actual<=f.point*(1+f.band),
       score:intervalScore(actual,f.point,f.band),width:2*f.band}});
  }
  pendingFixed.delete(t);
  if(t===freeze)fixedBand=conformalQuantile(c.scores,.2);
  if(t>=60&&t<series.length-h){
   const point=gold?predict(series.slice(0,t+1),h,'persistence'):series[t-6];
   const issue=c.issue(t,point);
   if(t>=freeze&&fixedBand!==null)pendingFixed.set(t+h,{origin:t,point,band:fixedBand});
  }
 }
 if(fixedBand===null||entries.length<200)throw Error('benchmark undercalibrated');
 return {entries,fixedBand};
}
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
function summarize(entries){
 const out={n:entries.length};
 for(const k of ['adaptive','frozen']){
  out[k]={coverage:mean(entries.map(x=>+x[k].hit)),meanScore:mean(entries.map(x=>x[k].score)),meanWidth:mean(entries.map(x=>x[k].width))};
 }
 out.scoreGain=out.frozen.meanScore-out.adaptive.meanScore;
 return out;
}
const result={seedCount:80,nPerSeries:700,freezeOrigin:220,regimeShiftAt:300,
 alpha:.2,horizonGold:7,horizonSeo:1,rollingWindow:80,minCalibration:40,
 scenarios:{}};
for(const kind of ['gold_up','gold_pulse','gold_stable','seo_up','seo_pulse']){
 const all=[],post=[],late=[],gains=[];
 for(let seed=1;seed<=80;seed++){
  const r=runOne(kind,seed*7919+13);all.push(...r.entries);post.push(...r.entries.filter(x=>x.post));late.push(...r.entries.filter(x=>x.afterPulse));
  gains.push(summarize(r.entries.filter(x=>x.post)).scoreGain);
 }
 result.scenarios[kind]={overall:summarize(all),postShift:summarize(post),afterPulse:summarize(late),
   postShiftSeedGain:{mean:mean(gains),wins:gains.filter(x=>x>0).length,losses:gains.filter(x=>x<0).length}};
}
const out=JSON.stringify(result,null,2);
writeFileSync(new URL('./benchmark146.json',import.meta.url),out);
console.log(out);
