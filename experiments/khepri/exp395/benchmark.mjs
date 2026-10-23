import {makeLedger,naiveLatest,naivePublishedCutoff} from './vintage_gate.mjs';
import {writeFileSync} from 'node:fs';
let state=3952026;
function rand(){state=(Math.imul(1664525,state)+1013904223)>>>0;return state/2**32;}
const results={seed:3952026,definition:'Synthetic; receipt timestamps are trusted; oracle truth is latent value at decision. Revisions after decision can be more accurate but unavailable.',cases:{}};
for(const [domain,base,amplitude] of [['gold',2200,0.035],['seo',100,0.08]]){
 const D=1000000,N=12000,totals={n:N,lateRevision:0,backdatedLateRevision:0,initialLate:0,latestLeak:0,publishedLeak:0,snapshotLeak:0,snapshotAbstain:0,latestSquaredError:0,publishedSquaredError:0,snapshotSquaredError:0,latestCount:0,publishedCount:0,snapshotCount:0};
 for(let i=0;i<N;i++){
  const truth=base*(0.8+0.4*rand());
  const l=makeLedger();const initialLate=rand()<0.15;
  const first={id:i+'-v0',series:domain,revision:0,value:truth*(1+(rand()*2-1)*amplitude),effectiveAt:D-1000,providerPublishedAt:D-900};
  if(initialLate)totals.initialLate++;
  const revisedLate=rand()<0.70,backdated=rand()<0.50;
  const second={id:i+'-v1',series:domain,revision:1,value:truth*(1+(rand()*2-1)*amplitude*0.05),effectiveAt:D-1000,providerPublishedAt:backdated?D-100:D+150};
  const arrivals=[[first,initialLate?D+100:D-300],[second,revisedLate?D+300:D-100]];
  arrivals.sort((a,b)=>a[1]-b[1]);
  for(const [event,receivedAt] of arrivals)l.append(event,receivedAt);
  if(revisedLate){totals.lateRevision++;if(backdated)totals.backdatedLateRevision++;}
  const receipts=l.receipts(), selections={latest:naiveLatest(receipts,domain),published:naivePublishedCutoff(receipts,domain,D),snapshot:l.snapshot(domain,D)};
  for(const [name,s] of Object.entries(selections)){
   if(!s || s.status==='abstain'){if(name==='snapshot')totals.snapshotAbstain++;continue;}
   totals[name+'Count']++;
   totals[name+'SquaredError']+=((s.value-truth)/truth)**2;
   if(s.receivedAt>D)totals[name+'Leak']++;
  }
 }
 const metrics={n:N,lateRevision:totals.lateRevision,backdatedLateRevision:totals.backdatedLateRevision,initialLate:totals.initialLate};
 for(const name of ['latest','published','snapshot']){
  metrics[name]={coverage:totals[name+'Count']/N,leakedDecisions:totals[name+'Leak'],leakRateAmongSelected:totals[name+'Count']?totals[name+'Leak']/totals[name+'Count']:0,relativeRMSE:Math.sqrt(totals[name+'SquaredError']/Math.max(1,totals[name+'Count']))};
 }
 results.cases[domain]=metrics;
}
const json=JSON.stringify(results,null,2)+'\n';
console.log(json);
if(process.argv.includes('--write'))writeFileSync(new URL('./results.json',import.meta.url),json);
