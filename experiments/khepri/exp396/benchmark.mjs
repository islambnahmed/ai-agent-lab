import {makeLedger} from '../exp395/vintage_gate.mjs';
import {latestObservation} from './latest_observation.mjs';
import {writeFileSync} from 'node:fs';
let state=3962026;
const rand=()=>((state=(Math.imul(1664525,state)+1013904223)>>>0)/2**32);
const N=10000,D=1000000;
const report={seed:3962026,nPerDomain:N,definition:'Synthetic latest-observation task: older revision may arrive after a newer observation. Compare exp395 receipt-first snapshot against observation-first selector. Same trusted receipt ledger; no real data.',domains:{}};
for(const [domain,base,oldDrift,newNoise] of [['gold',2200,0.035,0.002],['seo',100,0.18,0.012]]){
 const m={trials:N,newObservationAvailable:0,lateOldCorrections:0,
  receiptFirstWrongObservation:0,observationFirstWrongObservation:0,
  receiptFirstLeak:0,observationFirstLeak:0,
  receiptFirstSquaredError:0,observationFirstSquaredError:0,
  bothOldWhenNewUnavailable:0};
 for(let i=0;i<N;i++){
  const truth=base*(0.85+rand()*0.3);
  const oldVal=truth*(1+(rand()*2-1)*oldDrift);
  const newVal=truth*(1+(rand()*2-1)*newNoise);
  const newAvailable=rand()<0.9,oldCorrectionLate=rand()<0.5;
  const oldAt=D-5000,newAt=D-100;
  const old={id:`${i}-old`,series:domain,revision:0,value:oldVal,effectiveAt:oldAt,providerPublishedAt:oldAt};
  const newest={id:`${i}-new`,series:domain,revision:0,value:newVal,effectiveAt:newAt,providerPublishedAt:newAt};
  const oldCorrection={id:`${i}-old-r1`,series:domain,revision:1,value:oldVal*1.001,effectiveAt:oldAt,providerPublishedAt:oldAt};
  const arrivals=[[old,D-1000],[newest,newAvailable?D-300:D+100],[oldCorrection,oldCorrectionLate?D-100:D-700]];
  arrivals.sort((a,b)=>a[1]-b[1]);
  const ledger=makeLedger();for(const [evt,when] of arrivals)ledger.append(evt,when);
  const a=ledger.snapshot(domain,D),b=latestObservation(ledger,domain,D);
  if(newAvailable)m.newObservationAvailable++;
  if(oldCorrectionLate)m.lateOldCorrections++;
  if(!newAvailable && a.effectiveAt===oldAt && b.effectiveAt===oldAt)m.bothOldWhenNewUnavailable++;
  if(newAvailable && a.effectiveAt!==newAt)m.receiptFirstWrongObservation++;
  if(newAvailable && b.effectiveAt!==newAt)m.observationFirstWrongObservation++;
  if(a.receivedAt>D)m.receiptFirstLeak++;
  if(b.receivedAt>D)m.observationFirstLeak++;
  m.receiptFirstSquaredError+=((a.value-truth)/truth)**2;
  m.observationFirstSquaredError+=((b.value-truth)/truth)**2;
 }
 m.receiptFirstRelativeRMSE=Math.sqrt(m.receiptFirstSquaredError/N);
 m.observationFirstRelativeRMSE=Math.sqrt(m.observationFirstSquaredError/N);
 delete m.receiptFirstSquaredError;delete m.observationFirstSquaredError;
 report.domains[domain]=m;
}
console.log(JSON.stringify(report,null,2));
if(process.argv.includes('--write'))writeFileSync(new URL('./results.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
