export const MODEL_NAMES={persistence:'آخر إغلاق (Baseline)',momentum:'اتجاه مخفّف',mean_reversion:'عودة للمتوسط',ridge:'Ridge — تعلّم من حركة السعر'};
export const MODEL_VERSION='gold-v2.0.0';
const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
const cap=(x,b)=>Math.max(-b,Math.min(b,x));

// Every feature uses information at or before its origin. No macro/news inputs
// are invented; adding those requires release timestamps and vintage data.
function context(prices){
  const logs=prices.map(Math.log),sums=[0],r=[0],r2=[0];
  for(let i=0;i<logs.length;i++){
    sums.push(sums.at(-1)+logs[i]);
    const ret=i?logs[i]-logs[i-1]:0;r.push(r.at(-1)+ret);r2.push(r2.at(-1)+ret*ret);
  }
  return {logs,sums,r,r2};
}
function featureAt({logs,sums,r,r2},i){
  if(i<60)throw Error('Features require 61 prices');
  const avg=(r[i+1]-r[i-19])/20;
  const vol=Math.sqrt(Math.max(0,(r2[i+1]-r2[i-19])/20-avg*avg));
  return [logs[i]-logs[i-5],logs[i]-logs[i-20],logs[i]-(sums[i+1]-sums[i-19])/20,
    logs[i]-(sums[i+1]-sums[i-59])/60,vol];
}
export function features(prices,i=prices.length-1){return featureAt(context(prices),i);}

export function solve(a,b){
  const m=a.map((row,i)=>[...row,b[i]]),n=b.length;
  for(let i=0;i<n;i++){
    let pivot=i;for(let j=i+1;j<n;j++)if(Math.abs(m[j][i])>Math.abs(m[pivot][i]))pivot=j;
    [m[i],m[pivot]]=[m[pivot],m[i]];
    if(Math.abs(m[i][i])<1e-12)throw Error('Singular Ridge fit');
    const scale=m[i][i];for(let k=i;k<=n;k++)m[i][k]/=scale;
    for(let j=0;j<n;j++)if(j!==i){const factor=m[j][i];for(let k=i;k<=n;k++)m[j][k]-=factor*m[i][k];}
  }
  return m.map(row=>row[n]);
}

function ridge(prices,h){
  const rows=[],ctx=context(prices);
  // Labels must have matured before the last available close. 400-row window;
  // regularization and features are frozen, not chosen on the audit set.
  for(let i=Math.max(60,prices.length-h-400);i+h<prices.length;i++)
    rows.push({x:featureAt(ctx,i),y:Math.log(prices[i+h]/prices[i])});
  if(rows.length<20)return prices.at(-1); // explicit warmup fallback
  const centers=rows[0].x.map((_,j)=>mean(rows.map(r=>r.x[j])));
  const scales=centers.map((c,j)=>Math.max(1e-8,Math.sqrt(mean(rows.map(r=>(r.x[j]-c)**2)))));
  const design=x=>[1,...x.map((v,j)=>(v-centers[j])/scales[j])];
  const a=Array.from({length:6},()=>Array(6).fill(0)),b=Array(6).fill(0);
  for(const row of rows){const x=design(row.x);for(let j=0;j<6;j++){b[j]+=x[j]*row.y;for(let k=0;k<6;k++)a[j][k]+=x[j]*x[k];}}
  for(let j=0;j<6;j++)a[j][j]+=j===0?1e-8:20;
  const beta=solve(a,b),x=design(featureAt(ctx,prices.length-1));
  const logReturn=cap(beta.reduce((s,v,j)=>s+v*x[j],0),0.20);
  return prices.at(-1)*Math.exp(logReturn);
}

export function predict(history,h,model='persistence'){
  if(history.length<42||!Number.isInteger(h)||h<1||h>30)throw Error('Insufficient history / invalid horizon');
  if(history.some(p=>!Number.isFinite(p)||p<=0))throw Error('Invalid prices');
  const last=history.at(-1);
  if(model==='persistence')return last;
  if(model==='momentum'){
    const t=history.slice(-21),r=mean(t.slice(1).map((p,i)=>Math.log(p/t[i])));
    return last*Math.exp(cap(r,0.012)*h*0.45*Math.exp(-h/20));
  }
  if(model==='mean_reversion'){
    const anchor=mean(history.slice(-40).map(Math.log));
    return Math.exp(Math.log(last)+(anchor-Math.log(last))*Math.min(0.6,h*0.025));
  }
  // Ridge uses at most 400 matured origins, h target offsets and 60 lagged closes.
  // Keep full-history validation above; only bound the fitting context.
  if(model==='ridge')return history.length<61?last:ridge(history.length>h+460?history.slice(-(h+460)):history,h);
  throw Error('Unknown model');
}
