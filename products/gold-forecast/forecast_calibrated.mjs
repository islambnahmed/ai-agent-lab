// Multiplicative intervals centered on the selected point forecast.
// Report only observed held-out coverage; no nominal coverage guarantee.
import {forecast,normalize,predict} from './forecast.mjs';
import {calibrateMultiplicativeInterval,intervalAt,empiricalCoverage} from './calibration.mjs';

export function forecastCalibrated(raw,h=7){
  const original=forecast(raw,h);
  const prices=normalize(raw).map(x=>x.price),n=prices.length;
  const split=Math.floor(n*0.8),start=Math.max(65,2*h+45),end=split-h+1;
  const stride=Math.max(1,Math.floor(h/5));
  const pairs=(begin,stop,step)=>{
    const result=[];
    for(let i=begin;i<stop;i+=step){
      const predicted=predict(prices.slice(0,i),h,original.model);
      result.push({predicted,actual:prices[i+h-1]});
    }
    return result;
  };
  const calibration=pairs(start,end,stride),audit=pairs(split,n-h+1,1);
  const {logRadius,band}=calibrateMultiplicativeInterval(calibration);
  return {...original,...intervalAt(original.point,logRadius),band,
    coverage:empiricalCoverage(audit,logRadius),
    coverageDefinition:'fraction of held-out actual closes inside displayed interval',
    coverageWarning:'descriptive only; not guaranteed under dependence, shift or model selection'};
}
