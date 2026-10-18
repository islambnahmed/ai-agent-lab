/** Research-only stable binomial upper tail for exp266 rolling comparator. */
const C=[0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-0.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
function logGamma(z){
  if(z<0.5)return Math.log(Math.PI)-Math.log(Math.sin(Math.PI*z))-logGamma(1-z);
  z-=1;let x=C[0];for(let i=1;i<C.length;i++)x+=C[i]/(z+i);
  const t=z+7.5;return .5*Math.log(2*Math.PI)+(z+.5)*Math.log(t)-t+Math.log(x);
}
function logPmf(k,n,p){
  return logGamma(n+1)-logGamma(k+1)-logGamma(n-k+1)+k*Math.log(p)+(n-k)*Math.log1p(-p);
}
export function stableBinomialUpperTail(k,n,p){
  if(!Number.isSafeInteger(n)||n<1||!Number.isSafeInteger(k)||k<0||k>n||!Number.isFinite(p)||!(p>0&&p<1))throw Error('invalid binomial parameters');
  if(k===0)return 1;
  let term,sum;
  if(k>n*p){
    term=Math.exp(logPmf(k,n,p));sum=term;
    for(let j=k;j<n;j++){term*=((n-j)/(j+1))*(p/(1-p));sum+=term;if(term===0)break;}
    return Math.max(0,Math.min(1,sum));
  }
  let j=k-1;term=Math.exp(logPmf(j,n,p));sum=term;
  while(j>0){term*=(j/(n-j+1))*((1-p)/p);sum+=term;j--;if(term===0)break;}
  return Math.max(0,Math.min(1,1-sum));
}
