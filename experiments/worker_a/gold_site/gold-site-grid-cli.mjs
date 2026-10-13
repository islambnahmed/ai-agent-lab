/** Reproducible fixed-clock XAU/USD backtest command. No network calls.
 * Usage: node gold-site-grid-cli.mjs observed.csv --start ISO --end ISO --as-of ISO [--stride-minutes 75]
 * Input observed.csv is timestamp,price,source (close-time-labelled observations).
 * Do not pass raw OHLCV bars; convert them with gold-site-ohlcv-adapter.mjs first.
 */
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {parsePriceCSV,utcMs} from './gold-site-offline-eval.mjs';
import {evaluateFixedGrid,MIN,HORIZON} from './gold-site-grid-eval.mjs';

const fields=new Map([
 ['--start','startMs'],['--end','endMs'],['--as-of','asOfMs'],
 ['--stride-minutes','strideMs'],['--max-issue-lag-minutes','maxIssueLagMs'],
 ['--max-lookback-lag-minutes','maxLookbackLagMs'],['--max-target-lag-minutes','maxTargetLagMs']
]);
export function parseArgs(args){
 if(args.length<7||(args.length-1)%2!==0)throw Error('Usage: observed.csv --start ISO --end ISO --as-of ISO [--stride-minutes 75]');
 const [path,...rest]=args;
 if(!path||path.startsWith('--'))throw Error('Input CSV path required');
 const opts={};const seen=new Set();
 for(let i=0;i<rest.length;i+=2){
  const flag=rest[i],value=rest[i+1],field=fields.get(flag);
  if(!field||seen.has(flag)||!value)throw Error('Unknown, repeated or missing option: '+flag);
  seen.add(flag);
  if(field==='startMs'||field==='endMs'||field==='asOfMs')opts[field]=utcMs(value);
  else{
   if(!/^\d+$/.test(value))throw Error('Minutes must be a nonnegative integer');
   const minutes=Number(value),ms=minutes*MIN;
   if(!Number.isSafeInteger(ms)||(field==='strideMs'&&ms<MIN))throw Error('Invalid minute option');
   opts[field]=ms;
  }
 }
 if(!['--start','--end','--as-of'].every(k=>seen.has(k)))throw Error('Explicit start, end and as-of required');
 return {path,opts};
}
export function runFixedGridCSV(csv,args){
 const {opts}=parseArgs(['observed.csv',...args]);
 const rows=parsePriceCSV(csv);
 const output=evaluateFixedGrid(rows,opts);
 return {
  protocol:'fixed-clock-xauusd-75m-v1',
  inputSha256:createHash('sha256').update(csv,'utf8').digest('hex'),
  observations:rows.length,
  parameters:{startMs:opts.startMs,endMs:opts.endMs,asOfMs:opts.asOfMs,
   strideMs:opts.strideMs??HORIZON,maxIssueLagMs:opts.maxIssueLagMs??2*MIN,
   maxLookbackLagMs:opts.maxLookbackLagMs??5*MIN,maxTargetLagMs:opts.maxTargetLagMs??10*MIN},
  ...output,
  caveat:'Historical broker quote proxy; no live witnessing, trade execution, or proof of forecast skill'
 };
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{
  const {path}=parseArgs(process.argv.slice(2));
  const output=runFixedGridCSV(readFileSync(path,'utf8'),process.argv.slice(3));
  console.log(JSON.stringify(output,null,2));
 }catch(e){console.error(e.message);process.exitCode=1;}
}
