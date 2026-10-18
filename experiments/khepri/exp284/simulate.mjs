// Deterministic synthetic regimes. NOT actual gold or traffic data.
export function rng(seed) {
  let s = seed >>> 0;
  const uniform = () => {s = (1664525*s+1013904223)>>>0;return (s+0.5)/4294967296;};
  return () => Math.sqrt(-2*Math.log(uniform()))*Math.cos(2*Math.PI*uniform());
}
export function simulate(kind,seed,n=850) {
  const z=rng(seed),p=[kind==='web_traffic'?1500:2000];let lastReturn=0;
  for(let i=1;i<n;i++){
    let r;
    if(kind==='random_walk')r=.0001+.008*z();
    else if(kind==='persistent_returns')r=.72*lastReturn+.004*z();
    else if(kind==='trend_reversal')r=(i<500?.002:-.002)+.004*z();
    else if(kind==='web_traffic')r=.001+.006*z()+.025*(Math.sin(2*Math.PI*i/7)-Math.sin(2*Math.PI*(i-1)/7));
    else throw Error('Unknown synthetic regime');
    lastReturn=r;p.push(p.at(-1)*Math.exp(r));
  }
  return p;
}
