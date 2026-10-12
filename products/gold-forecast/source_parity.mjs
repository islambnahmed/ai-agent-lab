/**
 * Offline XAU/USD daily-close cross-source screening.
 * No downloads, no redistribution, no proof of source independence or accuracy.
 */
import {readFileSync} from 'node:fs';

const DATE=/^\d{4}-\d{2}-\d{2}$/;
const NUMBER=/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;
const validDate=s=>DATE.test(s)&&Number.isFinite(Date.parse(s+'T00:00:00Z'))&&new Date(Date.parse(s+'T00:00:00Z')).toISOString().slice(0,10)===s;

export function parseDailyCloseCsv(text,{sourceId,unit='USD per troy ounce'}={}) {
  if(typeof sourceId!=='string'||!sourceId.trim())throw Error('sourceId required');
  if(unit!=='USD per troy ounce')throw Error('Only XAU/USD per troy ounce is supported');
  if(typeof text!=='string')throw Error('CSV text required');
  const lines=text.replace(/^\uFEFF/,'').trim().split(/\r?\n/);
  if(lines.length<2)throw Error('CSV has no observations');
  const header=lines.shift().split(',').map(x=>x.trim().toLowerCase());
  const dateIndex=header.indexOf('date');
  const priceIndex=header.indexOf('close')>=0?header.indexOf('close'):header.indexOf('price');
  if(dateIndex<0||priceIndex<0||dateIndex===priceIndex)throw Error('Expected Date,Close or date,price columns');
  if(header.filter(x=>x==='date').length!==1||header.filter(x=>x==='close'||x==='price').length!==1)throw Error('Ambiguous CSV header');
  const rows=[];let previous='';
  for(let i=0;i<lines.length;i++){
    if(!lines[i].trim())throw Error(`Blank CSV row ${i+2}`);
    const parts=lines[i].split(',').map(x=>x.trim());
    if(parts.length!==header.length)throw Error(`Malformed CSV row ${i+2}`);
    const date=parts[dateIndex],raw=parts[priceIndex];
    if(!validDate(date))throw Error(`Invalid date at row ${i+2}`);
    if(date<=previous)throw Error(`Dates must be strictly increasing and unique (row ${i+2})`);
    if(!NUMBER.test(raw))throw Error(`Invalid close at row ${i+2}`);
    const price=Number(raw);
    if(!Number.isFinite(price)||price<=0)throw Error(`Invalid close at row ${i+2}`);
    rows.push({date,price});previous=date;
  }
  return {sourceId,unit,rows};
}

function percentile(values,f){
  if(!values.length)return null;
  const ordered=[...values].sort((a,b)=>a-b);
  return ordered[Math.max(0,Math.ceil(f*ordered.length)-1)];
}

/** Compare only matching UTC dates; differing close clocks require manual review. */
export function compareDailyCloses(a,b,{minOverlap=120,maxGapPct=1}={}){
  if(!a||!b||a.sourceId===b.sourceId||!a.sourceId||!b.sourceId)throw Error('Two distinct named sources required');
  if(a.unit!=='USD per troy ounce'||b.unit!==a.unit)throw Error('Incompatible units');
  if(!Number.isInteger(minOverlap)||minOverlap<2)throw Error('Invalid minOverlap');
  if(!Number.isFinite(maxGapPct)||maxGapPct<0)throw Error('Invalid maxGapPct');
  const check=(source)=>{
    if(!Array.isArray(source.rows))throw Error('Missing rows');
    let prior='';
    for(const r of source.rows){
      if(!validDate(r?.date)||r.date<=prior||typeof r.price!=='number'||!Number.isFinite(r.price)||r.price<=0)
        throw Error('Invalid or unsorted source observations');
      prior=r.date;
    }
  };
  check(a);check(b);
  const byB=new Map(b.rows.map(r=>[r.date,r.price]));
  const byA=new Set(a.rows.map(r=>r.date));
  const matches=[],onlyA=[],onlyB=[];
  for(const r of a.rows){
    if(!byB.has(r.date)){onlyA.push(r.date);continue;}
    const other=byB.get(r.date);
    const gapPct=200*Math.abs(r.price-other)/(r.price+other);
    matches.push({date:r.date,sourceA:r.price,sourceB:other,gapPct});
  }
  for(const r of b.rows)if(!byA.has(r.date))onlyB.push(r.date);
  const gaps=matches.map(r=>r.gapPct),flags=matches.filter(r=>r.gapPct>maxGapPct);
  const status=matches.length<minOverlap?'insufficient-overlap':flags.length?'requires-review':'screened-within-threshold';
  return {sources:[a.sourceId,b.sourceId],unit:a.unit,status,thresholdPct:maxGapPct,
    observations:[a.rows.length,b.rows.length],matchedDates:matches.length,
    onlySourceA:{count:onlyA.length,examples:onlyA.slice(0,5)},
    onlySourceB:{count:onlyB.length,examples:onlyB.slice(0,5)},
    gapPct:{median:percentile(gaps,0.5),p95:percentile(gaps,0.95),max:percentile(gaps,1)},
    flaggedCount:flags.length,flaggedExamples:flags.sort((x,y)=>y.gapPct-x.gapPct).slice(0,5),
    warning:'Exact-date screening only. Different closing times, bid/ask definitions, weekends and provider provenance can invalidate comparisons. This is not proof of accuracy or predictive skill.'};
}

if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
  const [pathA,pathB,idA='source-A',idB='source-B']=process.argv.slice(2);
  if(!pathA||!pathB){console.error('Usage: node source_parity.mjs A.csv B.csv [sourceA] [sourceB]');process.exitCode=2;}
  else try{
    const a=parseDailyCloseCsv(readFileSync(pathA,'utf8'),{sourceId:idA});
    const b=parseDailyCloseCsv(readFileSync(pathB,'utf8'),{sourceId:idB});
    console.log(JSON.stringify(compareDailyCloses(a,b),null,2));
  }catch(e){console.error(e.message);process.exitCode=1;}
}
