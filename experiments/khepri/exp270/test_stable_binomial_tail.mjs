import assert from 'node:assert/strict';
import {stableBinomialUpperTail as tail} from './stable_binomial_tail.mjs';
function old(k,n,p){let term=(1-p)**n,sum=0;for(let i=0;i<=n;i++){if(i>=k)sum+=term;if(i<n)term*=((n-i)/(i+1))*(p/(1-p));}return sum;}
const cases=[
 [1000,5000,.2,.5056417406385556],
 [1,5000,.2,1],
 [1000,10000,.1,.5048759163092349],
 [200,1000,.2,.5126139256145433],
 [100,10000,.01,.5134992717193709],
 [5,10,.2,.0327934976],
 [100,1000,.1,.513326076936],
];
for(const [k,n,p,expected] of cases){
 const got=tail(k,n,p);
 assert.ok(Math.abs(got-expected)<2e-8,`k=${k} n=${n} got=${got} expected=${expected}`);
}
assert.equal(old(1000,5000,.2),0);
assert.ok(tail(1000,5000,.2)>.05);
assert.equal(old(1,5000,.2),0);
assert.equal(tail(1,5000,.2),1);
function choose(n,k){let x=1;for(let i=1;i<=k;i++)x=x*(n-i+1)/i;return x;}
for(let n=1;n<=35;n++)for(const p of [.01,.1,.2,.5,.9,.99]){
 let prev=1;
 for(let k=0;k<=n;k++){
  let expected=0;
  for(let j=k;j<=n;j++)expected+=choose(n,j)*p**j*(1-p)**(n-j);
  const got=tail(k,n,p);
  assert.ok(Math.abs(got-expected)<1e-9,`n=${n} p=${p} k=${k}`);
  assert.ok(got<=prev+1e-10&&got>=0&&got<=1);
  prev=got;
 }
}
for(const args of [[1,0,.2],[1,10,0],[1,10,1],[11,10,.2],[-1,10,.2],[1,2.5,.2]])assert.throws(()=>tail(...args));
console.log('PASS exp270 regression + 17? SciPy spot checks + exhaustive small-n');
