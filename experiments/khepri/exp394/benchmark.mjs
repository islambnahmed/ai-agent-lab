import {corroborate} from '../exp393/provenance_quorum.mjs';
import {corroborateGraph,graphFor} from './graph_quorum.mjs';
export function simulate({trials=12000,seed=394,base=2000,amplitude=200,badMultiplier=1.18,
  xFault=0.12,otherFault=0.04,systemicFault=0.02,mode='honest'}={}) {
  if (!Number.isInteger(trials) || trials<1 || !Number.isInteger(seed) || base<=amplitude || amplitude<0 ||
      !Number.isFinite(badMultiplier) || badMultiplier<=0 || Math.abs(badMultiplier-1)<=0.05 ||
      [xFault,otherFault,systemicFault].some(p=>!Number.isFinite(p)||p<0||p>1)) throw Error('Invalid simulation parameters');
  const graph=graphFor(mode); let state=seed>>>0;
  const rand=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;};
  const metrics={flat:{correct:0,wrong:0,abstain:0},graph:{correct:0,wrong:0,abstain:0}};
  const breakdown={commonShock:0,sharedXFault:0,independentXFaults:0};
  for(let t=0;t<trials;t++) {
    const truth=base+amplitude*Math.sin(t/71),common=rand()<systemicFault;
    const badX=common||rand()<xFault;
    const badY=common||rand()<otherFault, badZ=common||rand()<otherFault;
    if (common) breakdown.commonShock++;
    if (mode!=='independent' && badX && !common) breakdown.sharedXFault++;
    if (mode==='independent' && badX && !common) breakdown.independentXFaults++;
    const badXs=mode==='independent' ? [badX,common||rand()<xFault,common||rand()<xFault] : [badX,badX,badX];
    const bad=[...badXs,badY,badZ], ids=['X1','X2','X3','Y','Z'];
    const observations=ids.map((id,i)=>({source:`feed-${id}`,upstream:id,node:id,value:truth*(bad[i]?badMultiplier:1)}));
    const decisions={flat:corroborate(observations,{quorum:3}),graph:corroborateGraph(observations,graph,{quorum:3})};
    for(const [name,decision] of Object.entries(decisions)) {
      const bucket=decision.status==='abstain'?'abstain':(Math.abs(decision.value/truth-1)>0.05?'wrong':'correct');
      metrics[name][bucket]++;
    }
  }
  return {trials,seed,mode,base,amplitude,badMultiplier,xFault,otherFault,systemicFault,breakdown,metrics,
    note:'Synthetic. Honest graph explicitly reveals shared X. Forged graph hides it. Independent mode has separate X failures.'};
}
if (process.argv[1] && import.meta.url===new URL(`file://${process.argv[1]}`).href) {
  const results={gold:simulate({seed:394}),seo:simulate({seed:395,base:100,amplitude:10,badMultiplier:0.7}),
    forged:simulate({seed:394,mode:'forged'}),independent:simulate({seed:394,mode:'independent'}),
    commonShock:simulate({seed:394,systemicFault:0.25})};
  process.stdout.write(JSON.stringify(results,null,2)+'\n');
}
