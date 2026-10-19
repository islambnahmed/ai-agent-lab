/** Khepri exp296: phase-aggregate identifiability witnesses; synthetic sequences, not actual gold outcomes. */
export function reconstruct(phase, {mode='clustered'}={}) {
  if (!Array.isArray(phase)||phase.length<1||!['clustered','spread'].includes(mode)) throw Error('Invalid phase or mode');
  const h=phase.length;
  const n=phase.reduce((s,p,i)=>{
    if(!Array.isArray(p)||p.length!==2||!Number.isInteger(p[0])||!Number.isInteger(p[1])||p[0]<1||p[1]<0||p[1]>p[0])throw Error('Invalid phase counts');
    return s+p[0];
  },0);
  for(let i=0;i<h;i++)if(phase[i][0]!==Math.floor((n-1-i)/h)+1)throw Error('Phase sizes inconsistent with contiguous origins');
  const out=new Array(n).fill(1);
  for(let i=0;i<h;i++){
    const [count,hits]=phase[i],misses=count-hits;
    for(let j=0;j<count;j++){
      let miss;
      if(mode==='clustered') miss=j<misses;
      else {
        const rotated=(j+(i*11+3)%count)%count;
        miss=Math.floor((rotated+1)*misses/count)>Math.floor(rotated*misses/count);
      }
      out[i+j*h]=miss?0:1;
    }
  }
  return out;
}
export function phasesOf(bits,h){
  if(!Number.isInteger(h)||h<1)throw Error('Invalid horizon');
  return Array.from({length:h},(_,i)=>{
    const vals=bits.filter((_,j)=>j%h===i);
    return [vals.length,vals.reduce((a,b)=>a+b,0)];
  });
}
export function longestMissRun(bits){let run=0,max=0;for(const x of bits){run=x===0?run+1:0;max=Math.max(run,max);}return max;}
export function worstWindowCoverage(bits,w){
  if(!Number.isInteger(w)||w<1||w>bits.length)throw Error('Invalid window');
  let s=bits.slice(0,w).reduce((a,b)=>a+b,0),min=s;
  for(let i=w;i<bits.length;i++){s+=bits[i]-bits[i-w];min=Math.min(min,s);}
  return min/w;
}
export function bootstrapCoverage(bits,{block=30,reps=3000,seed=296}={}){
  if(!Array.isArray(bits)||bits.length<block||block<1||!Number.isInteger(reps)||reps<100||!Number.isInteger(seed))throw Error('Invalid bootstrap parameters');
  let state=seed>>>0;
  const rand=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;};
  const n=bits.length,means=[];
  for(let r=0;r<reps;r++){
    let total=0;
    for(let k=0;k<n;){const start=Math.floor(rand()*n);for(let j=0;j<block&&k<n;j++,k++)total+=bits[(start+j)%n];}
    means.push(total/n);
  }
  means.sort((a,b)=>a-b);
  return {lo:means[Math.floor(reps*0.025)],hi:means[Math.floor(reps*0.975)],width:means[Math.floor(reps*0.975)]-means[Math.floor(reps*0.025)]};
}
export function compare(phase,{window=30,block=30,reps=3000}={}){
  const cases={};
  for(const mode of ['clustered','spread']){
    const bits=reconstruct(phase,{mode});
    cases[mode]={n:bits.length,hits:bits.reduce((a,b)=>a+b,0),coverage:bits.reduce((a,b)=>a+b,0)/bits.length,
      longestMissRun:longestMissRun(bits),worstWindowCoverage:worstWindowCoverage(bits,Math.min(window,bits.length)),
      blockBootstrap95:bootstrapCoverage(bits,{block:Math.min(block,bits.length),reps})};
  }
  return {phase, cases, caveat:'Both sequences are artificial witnesses; block bootstrap is illustrative, not a valid confidence interval for the actual historical outcomes.'};
}
