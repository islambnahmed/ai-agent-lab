/** Independent synthetic generator for causal delayed-feedback benchmarks.
 * Uses xorshift32 (not the prior Mulberry generator), stochastic regime
 * transitions, persistent binary labels, and drifting feature reliability.
 */
export function rng(seed) {
  let s = (seed >>> 0) || 0x9e3779b9;
  return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return (s >>> 0) / 4294967296; };
}
export function generateMarkov(seed, {n=720, switchRate=.01, initialBad=false,
  labelPersistence=.7, stableError=.22, goodError=.06, badError=.94, trainN=100}={}) {
  if(!Number.isInteger(n)||n<1||!Number.isInteger(trainN)||trainN<1||
    [switchRate,labelPersistence,stableError,goodError,badError].some(v=>!(v>=0&&v<=1))) throw Error('Invalid generator parameters');
  const r=rng(seed), train=[],stream=[];
  let bad=initialBad, y=+(r()<.5);
  const sample=()=>{
    if(r()<1-labelPersistence) y^=1;
    return {x:[y^+(r()<stableError),y^+(r()<(bad?badError:goodError)),+(r()<.5)],y};
  };
  for(let i=0;i<trainN;i++)train.push(sample());
  for(let t=0;t<n;t++){
    if(r()<switchRate)bad=!bad;
    stream.push(sample());
  }
  return {train,stream,boundaries:[]};
}
