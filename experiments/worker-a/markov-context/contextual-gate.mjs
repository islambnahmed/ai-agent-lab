/** Causal contextual expert gate, evaluated on independent Markov data.
 * Context is frozen at prediction time; only delivered historical labels
 * score each expert. The oracle/best-of-two is diagnostic, not a policy.
 */
import {generateMarkov} from './markov-generator.mjs';
import {schedule} from '../../worker-a/delayed-feedback.mjs';
import {pathToFileURL} from 'node:url';
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const pred=(c,x)=>x[c>>1]^(c&1);
const err=(c,x,y)=>+(pred(c,x)!==y);
const argmin=a=>a.reduce((b,v,i)=>v<a[b]?i:b,0);
const VALID=(x)=>Number.isFinite(x);
export function evaluateContextual(data,delivery={}, {alpha=2**(-1/16),metaAlpha=2**(-1/128),
  lagThreshold=22,churnThreshold=.08,minEvidence=8,localMix=.75}={}) {
  if(!(alpha>0&&alpha<1)||!(metaAlpha>0&&metaAlpha<1)||
     !(lagThreshold>=0)||!(churnThreshold>=0&&churnThreshold<=1)||
     !(minEvidence>=0)||!(localMix>=0&&localMix<=1)||
     ![alpha,metaAlpha,lagThreshold,churnThreshold,minEvidence,localMix].every(VALID))throw Error('Invalid gate parameters');
  const {train,stream}=data;
  if(!train?.length||!stream?.length||!train[0]?.x?.length)throw Error('Missing training data');
  const m=train[0].x.length*2;
  const warm=Array.from({length:m},(_,c)=>mean(train.map(row=>err(c,row.x,row.y))));
  const sums=[warm.map(v=>4*v),warm.map(v=>4*v)];
  const weights=[4,4];
  const global=[0,0],byContext=Array.from({length:4},()=>[0,0]);
  const counts=Array(4).fill(0);
  const {deliveries,lost,scheduled}=schedule(stream,delivery);
  const historical=[], ages=[], arrivalPicks=[];
  const losses={arrival:[],timestamp:[],global:[],contextual:[]};
  const selections={global:[],contextual:[],context:[]};
  let delivered=0;
  for(let t=0;t<stream.length;t++){
    weights[0]*=alpha;weights[1]*=alpha;
    for(let c=0;c<m;c++){sums[0][c]*=alpha;sums[1][c]*=alpha;}
    for(let k=0;k<2;k++)global[k]*=metaAlpha;
    for(let k=0;k<4;k++){
      counts[k]*=metaAlpha;
      for(let j=0;j<2;j++)byContext[k][j]*=metaAlpha;
    }
    for(const d of deliveries.get(t)??[]){
      if(d.eventTime>=t)throw Error('Future label leakage');
      const h=historical[d.eventTime];
      if(!h)throw Error('Missing historical prediction');
      for(let k=0;k<2;k++){
        const loss=err(h.experts[k],d.x,d.y);
        global[k]+=loss;
        byContext[h.context][k]+=loss;
      }
      counts[h.context]++;
      const age=t-d.eventTime, w=alpha**age;
      weights[0]++;weights[1]+=w;
      for(let c=0;c<m;c++){
        const loss=err(c,d.x,d.y);
        sums[0][c]+=loss;sums[1][c]+=w*loss;
      }
      ages.push(age);if(ages.length>32)ages.shift();
      delivered++;
    }
    const experts=sums.map((s,k)=>argmin(s.map(v=>v/weights[k])));
    const lagHigh=ages.length>=4 && mean(ages)>=lagThreshold;
    const tail=arrivalPicks.slice(-48);
    const churn=tail.length<8?0:tail.slice(1).filter((v,i)=>v!==tail[i]).length/(tail.length-1);
    const ctx=Number(lagHigh)*2+Number(churn>=churnThreshold);
    const globalChoice=global[1]<global[0]?1:0;
    let contextChoice=globalChoice;
    if(counts[ctx]>=minEvidence){
      const contextualScore=byContext[ctx].map((v,k)=>localMix*v/counts[ctx]+(1-localMix)*global[k]/Math.max(1,counts.reduce((a,b)=>a+b,0)));
      contextChoice=contextualScore[1]<contextualScore[0]?1:0;
    }
    historical[t]={experts,context:ctx};
    arrivalPicks.push(experts[0]);
    const picks={arrival:experts[0],timestamp:experts[1],global:experts[globalChoice],contextual:experts[contextChoice]};
    for(const [name,c] of Object.entries(picks))losses[name].push(err(c,stream[t].x,stream[t].y));
    selections.global.push(globalChoice);selections.contextual.push(contextChoice);selections.context.push(ctx);
  }
  const accuracy=Object.fromEntries(Object.entries(losses).map(([name,v])=>[name,1-mean(v)]));
  return {accuracy,losses,selections,feedback:{delivered,lost,pending:scheduled-delivered},
    contextualUseRate:mean(selections.global.map((v,i)=>+(v!==selections.contextual[i])))};
}
export function study({trials=100,seed=23000000,scenario={},delivery={},hyper={}}={}){
  if(!Number.isInteger(trials)||trials<1)throw Error('Invalid trial count');
  const rows=Array.from({length:trials},(_,i)=>evaluateContextual(generateMarkov(seed+i,scenario),{...delivery,seed:seed+100000+i},hyper));
  const keys=['arrival','timestamp','global','contextual'];
  const accuracy=Object.fromEntries(keys.map(k=>[k,+(100*mean(rows.map(r=>r.accuracy[k]))).toFixed(3)]));
  const paired=(a,b)=>{
    const ds=rows.map(r=>100*(r.accuracy[a]-r.accuracy[b]));
    const mu=mean(ds),sd=Math.sqrt(ds.reduce((s,x)=>s+(x-mu)**2,0)/Math.max(1,trials-1));
    return {delta:+mu.toFixed(3),approx95CI:[+(mu-1.96*sd/Math.sqrt(trials)).toFixed(3),+(mu+1.96*sd/Math.sqrt(trials)).toFixed(3)]};
  };
  return {trials,seed,scenario,delivery,hyper,accuracy,
    contextualVsGlobal:paired('contextual','global'),contextualVsArrival:paired('contextual','arrival'),
    contextualVsTimestamp:paired('contextual','timestamp'),
    contextualChangeRate:+mean(rows.map(r=>r.contextualUseRate)).toFixed(3)};
}
export const scenarios={
  slowSevere:{scenario:{switchRate:.002},delivery:{maxLag:80,drop:.4}},
  fastSevere:{scenario:{switchRate:.04},delivery:{maxLag:80,drop:.4}},
  fastMedium:{scenario:{switchRate:.04},delivery:{maxLag:24,drop:.4}},
  slowMedium:{scenario:{switchRate:.002},delivery:{maxLag:24,drop:.4}},
  persistentLabels:{scenario:{switchRate:.01,labelPersistence:.95},delivery:{maxLag:48,drop:.4}},
  sparseFeedback:{scenario:{switchRate:.01},delivery:{maxLag:48,drop:.8}}
};
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const seed=Number(process.argv[2]??23000000),trials=Number(process.argv[3]??100);
  console.log(JSON.stringify(Object.fromEntries(Object.entries(scenarios).map(([name,config])=>[name,study({...config,seed,trials})])),null,2));
}
