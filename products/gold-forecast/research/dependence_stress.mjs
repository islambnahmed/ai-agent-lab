/** Synthetic null stress test: correlated forecast errors inflate naive significance. */
const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
export function pairedDiagnostics(gains,lag=0){
  if(!Array.isArray(gains)||gains.length<30||gains.some(x=>typeof x!=='number'||!Number.isFinite(x)))
    throw Error('At least 30 finite paired error improvements required');
  if(!Number.isInteger(lag)||lag<0||lag>=gains.length)throw Error('Invalid lag');
  const n=gains.length,m=mean(gains),centered=gains.map(x=>x-m);
  const gamma=k=>centered.slice(k).reduce((sum,x,i)=>sum+x*centered[i],0)/n;
  let longRun=gamma(0);
  for(let k=1;k<=lag;k++)longRun+=2*(1-k/(lag+1))*gamma(k);
  const se=Math.sqrt(Math.max(0,longRun)/n);
  return {n,meanImprovement:m,lag,se,z:se>0?m/se:null,
    caveat:'Illustrative normal approximation; lag, nonstationarity, selection, and time anchoring remain unresolved.'};
}
function rng(seed){let state=seed>>>0;return ()=>((state=(1664525*state+1013904223)>>>0)+.5)/4294967296;}
function normal(rand){return Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());}
export function stress({seed=107,repetitions=600,n=140,rho=.85,lag=14}={}){
  if(!Number.isInteger(repetitions)||repetitions<1||repetitions>10000||!Number.isInteger(n)||n<30||n>5000||!(rho>=0&&rho<1)||!Number.isInteger(lag)||lag<0||lag>=n)
    throw Error('Invalid stress parameters');
  const rand=rng(seed);let iidRejects=0,hacRejects=0;
  for(let trial=0;trial<repetitions;trial++){
    const gains=[];let x=0;
    for(let i=0;i<n;i++){x=rho*x+Math.sqrt(1-rho*rho)*normal(rand);gains.push(x);}
    const iid=pairedDiagnostics(gains,0),hac=pairedDiagnostics(gains,lag);
    if(iid.z!==null&&Math.abs(iid.z)>1.96)iidRejects++;
    if(hac.z!==null&&Math.abs(hac.z)>1.96)hacRejects++;
  }
  return {seed,repetitions,n,rho,lag,iidFalsePositiveRate:iidRejects/repetitions,
    hacFalsePositiveRate:hacRejects/repetitions,
    warning:'Synthetic AR(1) zero-mean null. Not gold-market forecast accuracy or calibrated financial inference.'};
}
if(process.argv[1]&&new URL(import.meta.url).pathname===process.argv[1])console.log(JSON.stringify(stress(),null,2));
