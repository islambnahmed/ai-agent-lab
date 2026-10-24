/** Seeded, reproducible, synthetic property benchmark. No external IO. */
import fs from 'node:fs';
import {availableFeatures} from './feature-store.mjs';
import {guardedFeatures} from './provenance_guard.mjs';
let state=4102026;
function random(){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;}
function shuffle(x){const a=x.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
const origin='2025-03-01T00:00:00Z';
const r=(feature,source,vintage,value,observedAt='2025-02-01T00:00:00Z',availableAt='2025-02-02T00:00:00Z')=>({feature,source,vintage,value,observedAt,availableAt});
const result={seed:4102026,repetitionsPerCase:2000,sourceBlob:{
  'products/gold-forecast/feature-store.mjs':'7d0213edcc264b3ca79e3474aa82c2d88b434b1b',
  'products/gold-forecast/historical-integrity.mjs':'d104548e8f514903b9f7c91b3899033a85e3a914'
},cases:{}};
for (const label of ['gold_equal_value_source_tie','seo_distinct_features_order','gold_timezone_alias','seo_matured_revision']) {
  let upstreamOrderDependent=0,guardOrderDependent=0,guardRejectedBoth=0,guardAgreed=0;
  for(let i=0;i<2000;i++){
    let rows;
    if(label==='gold_equal_value_source_tie') rows=[r('yield','FRED','v1',i),r('yield','ALFRED','v2',i)];
    if(label==='seo_distinct_features_order') rows=[r('clicks','GSC','v1',i),r('impressions','GSC','v1',i+1)];
    if(label==='gold_timezone_alias') rows=[r('yield','FRED','v1',i),r('yield','FRED','v1',i,'2025-02-01T02:00:00+02:00','2025-02-02T02:00:00+02:00')];
    if(label==='seo_matured_revision') rows=[r('clicks','GSC','v1',i),r('clicks','GSC','v2',i+1,'2025-02-01T00:00:00Z','2025-02-04T00:00:00Z')];
    const x=shuffle(rows),y=x.slice().reverse();
    const u1=JSON.stringify(availableFeatures(x,origin)),u2=JSON.stringify(availableFeatures(y,origin));
    if(u1!==u2)upstreamOrderDependent++;
    let g1,g2,e1=null,e2=null;
    try{g1=JSON.stringify(guardedFeatures(x,origin));}catch(e){e1=e.message;}
    try{g2=JSON.stringify(guardedFeatures(y,origin));}catch(e){e2=e.message;}
    if(e1&&e2&&e1===e2)guardRejectedBoth++;
    else if(g1!==g2||e1!==e2)guardOrderDependent++;
    else guardAgreed++;
    if(label==='seo_matured_revision'&&(!g1||JSON.parse(g1).clicks.value!==i+1))throw Error('Incorrect matured revision');
  }
  result.cases[label]={upstreamOrderDependent,guardOrderDependent,guardRejectedBoth,guardAgreed};
}
fs.writeFileSync(new URL('./results.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
