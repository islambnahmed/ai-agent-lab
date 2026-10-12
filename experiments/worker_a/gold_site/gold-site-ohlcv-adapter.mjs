/** Convert public 1m OHLCV samples into the offline evaluator's observation CSV.
 * The input timestamp is BAR OPEN, not the time its close could be known.
 * We conservatively label the close at bar-end (+60s), but do not assert
 * actual provider publication latency or independent time witnessing.
 * This is a broker-CFD-derived proxy, NOT the gold-api.com live quote basis.
 */
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const MIN=60_000;
const SOURCE='getdata-finance-broker-cfd-1m-close';
const OPEN_TIME=/^\d{4}-\d\d-\d\dT\d\d:\d\d:00(?:\.000)?(?:\+00:00|Z)$/;
function time(s){
 if(!OPEN_TIME.test(s))throw Error('Expected minute-aligned UTC bar-open timestamp');
 const t=Date.parse(s);
 if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,19)!==s.slice(0,19))throw Error('Invalid bar timestamp');
 return t;
}
export function convertOneMinuteOHLCV(input){
 if(typeof input!=='string')throw Error('CSV required');
 const lines=input.trim().split(/\r?\n/);
 if(lines.shift()?.replace(/^\uFEFF/,'')!=='datetime,open,high,low,close,volume')throw Error('Unexpected OHLCV header');
 if(!lines.length)throw Error('No bars');
 const output=['timestamp,price,source'];let last=-Infinity;
 for(let i=0;i<lines.length;i++){
  const parts=lines[i].split(',');
  if(parts.length!==6)throw Error(`Malformed OHLCV row ${i+2}`);
  const [ts,...values]=parts;
  const t=time(ts);
  if(t<=last)throw Error(`Duplicate or unsorted bar at row ${i+2}`);
  const [open,high,low,close,volume]=values.map(Number);
  if(values.some(v=>!/^\d+(?:\.\d+)?$/.test(v)) ||
     [open,high,low,close,volume].some(v=>!Number.isFinite(v)) ||
     low<=0||high<low||open<low||open>high||close<low||close>high||
     volume<0||volume>1e10)throw Error(`Invalid OHLCV values at row ${i+2}`);
  output.push(`${new Date(t+MIN).toISOString()},${close},${SOURCE}`);
  last=t;
 }
 return output.join('\n')+'\n';
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{
  if(process.argv.length!==3)throw Error('Usage: node gold-site-ohlcv-adapter.mjs XAUUSD_1m.csv > observed.csv');
  process.stdout.write(convertOneMinuteOHLCV(readFileSync(process.argv[2],'utf8')));
 }catch(e){console.error(e.message);process.exitCode=1;}
}
