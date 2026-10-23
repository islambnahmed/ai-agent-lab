/** Synthetic research prototype: root-ancestor quorum, NOT provenance authentication. */
export function corroborateGraph(observations, nodes, {quorum=3, tolerance=0.01}={}) {
  if (!Array.isArray(observations) || observations.length>15 || !Array.isArray(nodes) || nodes.length>100 ||
      !Number.isInteger(quorum) || quorum<2 || !Number.isFinite(tolerance) || tolerance<0 || tolerance>=1)
    throw Error('Invalid inputs');
  const graph=new Map();
  for (const n of nodes) {
    if (!n || typeof n.id!=='string' || !n.id.trim() || !Array.isArray(n.parents) ||
        n.parents.some(p=>typeof p!=='string' || !p.trim()) ||
        new Set(n.parents).size!==n.parents.length || graph.has(n.id)) throw Error('Invalid/duplicate node');
    graph.set(n.id, n.parents);
  }
  for (const [id,parents] of graph) for(const p of parents) if (!graph.has(p)) throw Error(`Unknown parent ${p} for ${id}`);
  const memo=new Map(), visiting=new Set();
  function roots(id) {
    if (!graph.has(id)) throw Error('Unknown observation node');
    if (memo.has(id)) return memo.get(id);
    if (visiting.has(id)) throw Error('Cycle in provenance graph');
    visiting.add(id);
    const parents=graph.get(id);
    const set=new Set(parents.length ? parents.flatMap(p=>[...roots(p)]) : [id]);
    visiting.delete(id);
    memo.set(id,set);
    return set;
  }
  // Reject a cycle even in a disconnected graph component.
  for (const id of graph.keys()) roots(id);
  const sourceIds=new Set(), grouped=new Map();
  for(const o of observations) {
    if (!o || typeof o.source!=='string' || !o.source.trim() || sourceIds.has(o.source) ||
        typeof o.node!=='string' || !Number.isFinite(o.value) || o.value<=0) throw Error('Invalid/duplicate observation');
    sourceIds.add(o.source);
    const r=[...roots(o.node)].sort(), signature=JSON.stringify(r);
    if (!grouped.has(signature)) grouped.set(signature,{roots:r,values:[]});
    grouped.get(signature).values.push(o.value);
  }
  const groups=[], quarantined=[];
  for(const [signature,g] of grouped) {
    const low=Math.min(...g.values), high=Math.max(...g.values);
    if ((high-low)/low>tolerance) {quarantined.push(signature);continue;}
    groups.push({roots:g.roots,value:g.values.reduce((a,b)=>a+b,0)/g.values.length});
  }
  let bestSize=0, winners=[];
  for(let mask=1;mask<2**groups.length;mask++) {
    const selected=groups.filter((_,i)=>mask&(1<<i));
    if (selected.length<quorum || selected.length<bestSize) continue;
    const seen=new Set(); let independent=true;
    for(const g of selected) for(const r of g.roots) {if(seen.has(r)) independent=false; seen.add(r);}
    if (!independent) continue;
    const vals=selected.map(x=>x.value),low=Math.min(...vals),high=Math.max(...vals);
    if ((high-low)/low>tolerance) continue;
    if (selected.length>bestSize) {bestSize=selected.length; winners=[];}
    winners.push(selected);
  }
  if (!winners.length) return {status:'abstain',reason:'no_independent_quorum',groups:groups.length,quarantined};
  if (winners.length>1) return {status:'abstain',reason:'ambiguous_quorums',groups:groups.length,quarantined};
  const selected=winners[0];
  return {status:'corroborated_not_verified',value:selected.reduce((a,b)=>a+b.value,0)/selected.length,
    independentGroups:selected.length,groups:groups.length,quarantined};
}
export function graphFor(mode) {
  if (!['honest','forged','independent'].includes(mode)) throw Error('Invalid mode');
  const roots=mode==='honest' ? [{id:'X',parents:[]}] : [];
  return [...roots, ...['X1','X2','X3'].map(id=>({id,parents:mode==='honest'?['X']:[]})),
    {id:'Y',parents:[]},{id:'Z',parents:[]}];
}
