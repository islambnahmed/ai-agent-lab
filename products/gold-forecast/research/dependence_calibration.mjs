/**
 * Seshat C108: false-positive calibration under stationary AR(1) null.
 * The oracle knows the true covariance; real gold data do not.
 * No external data or network access.
 */
import {pathToFileURL} from 'node:url';
import {pairedDiagnostics} from './dependence_stress.mjs';

function seeded(seed) {
  let state=seed>>>0;
  return ()=>((state=(Math.imul(1664525,state)+1013904223)>>>0)+0.5)/4294967296;
}
function normal(rand) {
  return Math.sqrt(-2*Math.log(rand()))*Math.cos(2*Math.PI*rand());
}
export function ar1OracleSE(n,rho) {
  if(!Number.isInteger(n)||n<2||!Number.isFinite(rho)||Math.abs(rho)>=1)
    throw Error('n >= 2 and stationary -1 < rho < 1 required');
  let sum=n;
  for(let k=1;k<n;k++) sum+=2*(n-k)*rho**k;
  return Math.sqrt(sum)/n;
}
export function calibrate({seed=108,repetitions=2000,n=140,rho=.85,lags=[0,7,14,28,56]}={}) {
  if(!Number.isInteger(seed)||!Number.isInteger(repetitions)||repetitions<100||repetitions>100000||
     !Number.isInteger(n)||n<30||n>5000||!Number.isFinite(rho)||Math.abs(rho)>=1||
     !Array.isArray(lags)||!lags.length||lags.some(k=>!Number.isInteger(k)||k<0||k>=n))
    throw Error('Invalid calibration parameters');
  const rand=seeded(seed),counts=Object.fromEntries(lags.map(lag=>[lag,0]));
  let oracleRejects=0;
  const oracleSE=ar1OracleSE(n,rho);
  for(let rep=0;rep<repetitions;rep++){
    let x=normal(rand); // Stationary N(0,1) initial observation.
    const gains=[];
    for(let i=0;i<n;i++){
      if(i>0)x=rho*x+Math.sqrt(1-rho*rho)*normal(rand);
      gains.push(x);
    }
    const mean=gains.reduce((a,b)=>a+b,0)/n;
    if(Math.abs(mean/oracleSE)>1.95996398454)oracleRejects++;
    for(const lag of lags){
      const z=pairedDiagnostics(gains,lag).z;
      if(z!==null&&Math.abs(z)>1.95996398454)counts[lag]++;
    }
  }
  const rate=count=>Number((count/repetitions).toFixed(4));
  return {seed,repetitions,n,rho,nominalAlpha:.05,oracleSE,
    oracleFalsePositiveRate:rate(oracleRejects),
    hacFalsePositiveRates:Object.fromEntries(lags.map(lag=>[lag,rate(counts[lag])])),
    monteCarlo95Margin:1.96*Math.sqrt(.05*.95/repetitions),
    caveat:'Synthetic stationary AR(1) zero-mean null; oracle knows rho. Not gold forecast skill.'};
}
export function selfTest(){
  const assert=(v,msg)=>{if(!v)throw Error(msg)};
  assert(Math.abs(ar1OracleSE(100,0)-.1)<1e-12,'iid oracle SE');
  assert(ar1OracleSE(140,.85)>ar1OracleSE(140,0),'serial dependence SE');
  const a=calibrate({seed:13,repetitions:1000,n:140,rho:.85,lags:[0,14,56]});
  const b=calibrate({seed:13,repetitions:1000,n:140,rho:.85,lags:[0,14,56]});
  assert(JSON.stringify(a)===JSON.stringify(b),'reproducibility');
  assert(Math.abs(a.oracleFalsePositiveRate-.05)<.025,'oracle calibration');
  assert(a.hacFalsePositiveRates[0]>a.oracleFalsePositiveRate,'iid false positives');
  return {passed:true,oracle:a.oracleFalsePositiveRate,iid:a.hacFalsePositiveRates[0]};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  console.log(JSON.stringify(process.argv.includes('--self-test')?selfTest():
    {independent:calibrate({rho:0,seed:108}),persistent:calibrate({rho:.85,seed:109})},null,2));
}
