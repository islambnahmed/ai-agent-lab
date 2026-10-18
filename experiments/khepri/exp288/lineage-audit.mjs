/** Khepri exp288: lineage overlap audit. Requires exp287 auditedFeatures.
 * Registry must be separately verified. Disjoint roots do NOT establish
 * statistically independent errors. Experimental; no production wiring.
 */
import {auditedFeatures} from './audited-features.mjs';
const cmp=(a,b)=>a<b?-1:a>b?1:0;
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
function auditAttestations(attestations,registry){
  const sources=[...new Set(attestations.map(a=>a.source))].sort(cmp);
  const missing=[],known=[];
  for(const source of sources){
    if(!own(registry,source)){missing.push(source);continue;}
    const roots=registry[source];
    if(!Array.isArray(roots)||!roots.length||roots.some(r=>typeof r!=='string'||!r.trim()))throw Error('Invalid verified lineage for '+source);
    known.push({source,roots:[...new Set(roots)].sort(cmp)});
  }
  const parent=new Map(known.map(x=>[x.source,x.source]));
  const find=x=>{while(parent.get(x)!==x)x=parent.get(x);return x;};
  const join=(a,b)=>{a=find(a);b=find(b);if(a!==b)parent.set(cmp(a,b)<0?b:a,cmp(a,b)<0?a:b);};
  const seenRoot=new Map();
  for(const item of known)for(const root of item.roots){
    if(seenRoot.has(root))join(item.source,seenRoot.get(root));
    else seenRoot.set(root,item.source);
  }
  const groups=new Map();
  for(const item of known){
    const root=find(item.source);
    if(!groups.has(root))groups.set(root,[]);
    groups.get(root).push(item.source);
  }
  const overlapGroups=[...groups.values()].map(g=>g.sort(cmp)).sort((a,b)=>cmp(a[0],b[0]));
  return {distinctSources:sources.length,lineageComplete:missing.length===0,missingLineage:missing,
    knownOverlapGroups:overlapGroups,distinctLineageGroups:missing.length?null:overlapGroups.length,
    statisticalIndependence:'not_established',
    caution:'Source and root labels are not authenticated here; hidden shared causes may remain.'};
}
export function auditCorroboration(records,originAt,{lineageRegistry={},maxAgeDays=30}={}){
  if(!lineageRegistry||typeof lineageRegistry!=='object'||Array.isArray(lineageRegistry))throw Error('Invalid lineage registry');
  const result=auditedFeatures(records,originAt,{maxAgeDays}),lineage={};
  for(const name of Object.keys(result.evidence))lineage[name]=auditAttestations(result.evidence[name].attestations,lineageRegistry);
  return {...result,lineage};
}
